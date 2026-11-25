"""Behavioral checks against isolated Codex history fixtures."""

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('find_session.py')


def epoch(value):
    return int(dt.datetime.fromisoformat(value).timestamp())


class FindSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='find-session-test-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'codex home'
        self.home.mkdir()
        self.state = self.home / 'state_5.sqlite'
        self.history = self.home / 'thread_history_1.sqlite'
        with sqlite3.connect(self.state) as c:
            c.execute('CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, rollout_path TEXT)')
        with sqlite3.connect(self.history) as c:
            c.execute('CREATE TABLE thread_turns (thread_id TEXT, turn_id TEXT, started_at INTEGER, completed_at INTEGER)')
            c.execute('CREATE TABLE thread_items (thread_id TEXT, turn_id TEXT, item_id TEXT, created_at_ms INTEGER, item_type TEXT, item_json TEXT)')
            c.execute('CREATE INDEX items_by_thread ON thread_items(thread_id, created_at_ms)')

    def add_thread(self, identifier, title='Teams 메시지 확인', cwd='/projects/analytics'):
        with sqlite3.connect(self.state) as c:
            c.execute('INSERT INTO threads VALUES (?, ?, ?, ?)', (identifier, title, cwd, str(self.home / f'{identifier}.jsonl')))

    def add_message(self, identifier, text, timestamp='2026-11-25T08:00:00+09:00', role='user', item_type=None):
        stamp = epoch(timestamp)
        kind = item_type or ('userMessage' if role == 'user' else 'agentMessage')
        payload = {'type': kind, 'content': [{'type':'text','text':text}]} if role == 'user' else {'type':kind,'text':text,'phase':'final_answer'}
        with sqlite3.connect(self.history) as c:
            key = str(c.execute('SELECT count(*) FROM thread_items').fetchone()[0])
            c.execute('INSERT INTO thread_turns VALUES (?, ?, ?, ?)', (identifier,key,stamp,stamp+10))
            c.execute('INSERT INTO thread_items VALUES (?, ?, ?, ?, ?, ?)', (identifier,key,key,stamp*1000,kind,json.dumps(payload,ensure_ascii=False)))

    def run_search(self, *args, success=True):
        before = {p:p.read_bytes() for p in self.home.glob('*.sqlite')}
        result = subprocess.run([sys.executable,'-B',str(SCRIPT),'--codex-home',str(self.home),*args], capture_output=True,text=True)
        for p, content in before.items():
            self.assertEqual(hashlib.sha256(p.read_bytes()).digest(),hashlib.sha256(content).digest())
        if success:
            self.assertEqual(result.returncode,0,result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode,0)
        return result

    def test_resumed_old_session_and_kst_exclusive_time_boundary(self):
        self.add_thread('old-session')
        self.add_message('old-session','대시보드 변경 계획','2026-10-01T08:00:00+09:00')
        self.add_message('old-session','사업본부 대시보드 계획','2026-11-25T07:42:00+09:00')
        self.add_thread('too-late')
        self.add_message('too-late','대시보드','2026-11-25T09:00:00+09:00')
        result=self.run_search('--term','대시보드','--since','2026-11-25T07:00','--until','2026-11-25T09:00','--timezone','Asia/Seoul')
        self.assertEqual([r['session_id'] for r in result['results']],['old-session'])
        self.assertIn('07:42',result['results'][0]['evidence'][0]['timestamp'])
        self.assertEqual(result['results'][0]['resume_command'],'codex resume old-session')

    def test_tools_and_injected_instructions_do_not_match(self):
        self.add_thread('noise')
        self.add_message('noise','대시보드 secret token',item_type='mcpToolCall')
        self.add_message('noise','# AGENTS.md instructions\n대시보드')
        self.add_message('noise','그 외 작업')
        result=self.run_search('--term','대시보드')
        self.assertEqual(result['results'],[])
        self.assertNotIn('secret token',json.dumps(result))

    def test_terms_rank_across_messages_with_exact_matches_explained(self):
        for name in ['one','both']:
            self.add_thread(name)
        self.add_message('one','사업본부 현황')
        self.add_message('both','사업본부 대시보드를 바꾸자')
        self.add_message('both','영업본부도 같은 기준으로 바꾸겠습니다',role='assistant')
        result=self.run_search('--term','사업본부','--term','영업본부')
        self.assertEqual(result['results'][0]['session_id'],'both')
        self.assertEqual(result['results'][0]['matched_terms'],['사업본부','영업본부'])
        self.assertEqual(result['results'][1]['missing_terms'],['영업본부'])
        strict=self.run_search('--term','사업본부','--term','영업본부','--all-terms')
        self.assertEqual([r['session_id'] for r in strict['results']],['both'])

    def test_title_only_is_explicit_and_project_and_exclusion_work(self):
        self.add_thread('title-only','결제 대시보드 계획','/projects/shop')
        self.add_message('title-only','아직 설명 없음')
        result=self.run_search('--term','결제','--project','shop')
        self.assertEqual(result['results'][0]['verification'],'title_only')
        self.assertEqual(result['results'][0]['evidence'],[])
        self.assertEqual(self.run_search('--term','결제','--exclude-session','title-only')['results'],[])
        self.assertEqual(self.run_search('--term','결제','--project','analytics')['results'],[])

    def write_rollout(self, identifier, messages):
        folder=self.home/'sessions'/'2026'/'10'/'01'
        folder.mkdir(parents=True,exist_ok=True)
        path=folder/f'rollout-2026-10-01T08-00-00-{identifier}.jsonl'
        lines=[{'type':'session_meta','timestamp':'2026-10-01T00:00:00Z','payload':{'id':identifier,'cwd':'/projects/analytics'}}]
        for role,text,timestamp in messages:
            lines.append({'type':'response_item','timestamp':timestamp,'payload':{'type':'message','role':role,'content':[{'type':'input_text' if role=='user' else 'output_text','text':text}]}})
        path.write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in lines)+'\n',encoding='utf-8')
        return path

    def test_jsonl_fallback_handles_resumed_sessions_and_ignores_developer(self):
        self.history.unlink()
        self.state.unlink()
        path=self.write_rollout('fallback',[
            ('developer','대시보드 비밀 설정','2026-11-25T00:00:00Z'),
            ('user','사업본부 대시보드 계획','2026-11-24T22:42:00Z'),
        ])
        (self.home/'session_index.jsonl').write_text(json.dumps({'id':'fallback','thread_name':'아침 계획'})+'\n')
        result=self.run_search('--term','대시보드','--since','2026-11-25T07:00','--until','2026-11-25T09:00')
        self.assertEqual(result['results'][0]['session_id'],'fallback')
        self.assertEqual(result['results'][0]['title'],'아침 계획')
        self.assertEqual(len(result['results'][0]['evidence']),1)
        self.assertEqual(result['results'][0]['evidence'][0]['path'],str(path.resolve()))
        self.assertNotIn('비밀 설정',json.dumps(result,ensure_ascii=False))

    def test_indexed_and_unindexed_rollouts_are_both_searched(self):
        self.add_thread('indexed')
        self.add_message('indexed','선수금 대시보드')
        self.write_rollout('unindexed',[('user','선수금 추이','2026-11-24T23:00:00Z')])
        result=self.run_search('--term','선수금','--since','2026-11-25T07:00','--until','2026-11-25T09:00')
        self.assertEqual({r['session_id'] for r in result['results']},{'indexed','unindexed'})

    @unittest.skipUnless(shutil.which('zstd'),'zstd unavailable')
    def test_compressed_archive_fallback(self):
        self.history.unlink()
        self.state.unlink()
        path=self.write_rollout('archive',[('assistant','선수금 추이 계획','2026-11-24T23:00:00Z')])
        archives=self.home/'archived_sessions'
        archives.mkdir()
        dest=archives/(path.name+'.zst')
        subprocess.run(['zstd','-q',str(path),'-o',str(dest)],check=True)
        path.unlink()
        result=self.run_search('--term','선수금')
        self.assertEqual(result['results'][0]['session_id'],'archive')
        self.assertEqual(result['results'][0]['evidence'][0]['path'],str(dest.resolve()))

    def test_unprojected_tail_is_searched_without_repeating_indexed_messages(self):
        self.add_thread('tail')
        self.add_message('tail','대시보드 원래 계획')
        path=self.write_rollout('tail',[('user','대시보드 원래 계획','2026-11-24T23:00:00Z')])
        offset=path.stat().st_size
        record={'type':'response_item','timestamp':'2026-11-25T00:00:00Z','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':'선수금 후속 계획'}]}}
        with path.open('a') as stream:
            stream.write(json.dumps(record,ensure_ascii=False)+'\n')
        with sqlite3.connect(self.state) as c:
            c.execute('UPDATE threads SET rollout_path=? WHERE id=?',(str(path.resolve()),'tail'))
        with sqlite3.connect(self.history) as c:
            c.execute('CREATE TABLE thread_history_projection_state (thread_id TEXT, next_rollout_byte_offset INTEGER)')
            c.execute('INSERT INTO thread_history_projection_state VALUES (?,?)',('tail',offset))
        result=self.run_search('--term','대시보드','--term','선수금')
        self.assertEqual(result['results'][0]['matched_terms'],['대시보드','선수금'])
        self.assertEqual(result['messages_searched'],2)

    @unittest.skipUnless(shutil.which('zstd'),'zstd unavailable')
    def test_projected_compressed_alias_does_not_rescan_tool_payloads(self):
        self.add_thread('projected')
        self.add_message('projected','선수금 계획')
        path=self.write_rollout('projected',[('user','선수금 계획','2026-11-24T23:00:00Z')])
        offset=path.stat().st_size
        with sqlite3.connect(self.state) as c:
            c.execute('UPDATE threads SET rollout_path=? WHERE id=?',(str(path.resolve()),'projected'))
        with sqlite3.connect(self.history) as c:
            c.execute('CREATE TABLE thread_history_projection_state (thread_id TEXT, next_rollout_byte_offset INTEGER)')
            c.execute('INSERT INTO thread_history_projection_state VALUES (?,?)',('projected',offset))
        dest=Path(str(path)+'.zst')
        subprocess.run(['zstd','-q',str(path),'-o',str(dest)],check=True)
        path.unlink()
        result=self.run_search('--term','선수금')
        self.assertEqual(result['sources'],['thread_history'])
        self.assertEqual(result['messages_searched'],1)
        self.assertEqual(result['warnings'],[])

    def test_projection_and_rollout_copies_are_deduplicated(self):
        self.add_thread('duplicate')
        self.add_message('duplicate','대시보드 계획')
        self.write_rollout('duplicate',[('user','대시보드 계획','2026-11-24T23:00:00Z')])
        result=self.run_search('--term','대시보드')
        self.assertEqual(result['messages_searched'],1)
        self.assertEqual(len(result['results'][0]['evidence']),1)

    @unittest.skipUnless(shutil.which('zstd'),'zstd unavailable')
    def test_checkpoint_without_conversation_messages_still_searches_archive(self):
        self.add_thread('old-schema')
        path=self.write_rollout('old-schema',[('user','선수금 계획','2026-11-24T23:00:00Z')])
        offset=path.stat().st_size
        with sqlite3.connect(self.state) as c:
            c.execute('UPDATE threads SET rollout_path=? WHERE id=?',(str(path.resolve()),'old-schema'))
        with sqlite3.connect(self.history) as c:
            c.execute('CREATE TABLE thread_history_projection_state (thread_id TEXT, next_rollout_byte_offset INTEGER)')
            c.execute('INSERT INTO thread_history_projection_state VALUES (?,?)',('old-schema',offset))
        dest=Path(str(path)+'.zst')
        subprocess.run(['zstd','-q',str(path),'-o',str(dest)],check=True)
        path.unlink()
        result=self.run_search('--term','선수금')
        self.assertEqual(result['results'][0]['session_id'],'old-schema')
        self.assertIn('rollout',result['sources'])

    def test_keywords_are_literals_and_evidence_is_bounded(self):
        self.add_thread('literal')
        self.add_message('literal','앞'*500+'select [orders].* 뒤'+'뒤'*1000)
        result=self.run_search('--term','[orders].*')
        self.assertEqual(len(result['results']),1)
        evidence=result['results'][0]['evidence'][0]['text']
        self.assertIn('[orders].*',evidence)
        self.assertLessEqual(len(evidence),242)

    def test_schema_failure_falls_back_with_visible_coverage_warning(self):
        with sqlite3.connect(self.history) as c:
            c.execute('DROP TABLE thread_items')
        self.write_rollout('fallback',[('user','정산 계획','2026-11-24T23:00:00Z')])
        result=self.run_search('--term','정산')
        self.assertEqual(result['results'][0]['session_id'],'fallback')
        self.assertTrue(result['warnings'])

    def test_date_only_until_includes_that_calendar_day(self):
        self.add_thread('night')
        self.add_message('night','대시보드','2026-11-25T23:59:00+09:00')
        result=self.run_search('--term','대시보드','--since','2026-11-25','--until','2026-11-25')
        self.assertEqual(len(result['results']),1)

    def test_logs_outside_time_window_are_an_empty_result_not_missing_history(self):
        self.history.unlink()
        self.state.unlink()
        path=self.write_rollout('earlier',[('user','대시보드','2026-10-01T00:00:00Z')])
        stamp=epoch('2026-10-01T01:00:00+00:00')
        os.utime(path,(stamp,stamp))
        result=self.run_search('--term','대시보드','--since','2026-11-25')
        self.assertEqual(result['results'],[])
        self.assertEqual(result['warnings'],[])

    def test_invalid_range_and_missing_history_are_errors(self):
        self.run_search('--term','대시보드','--since','2026-11-26','--until','2026-11-25',success=False)
        self.history.unlink()
        self.state.unlink()
        result=self.run_search('--term','대시보드',success=False)
        self.assertIn('history',result.stderr.lower())


if __name__ == '__main__':
    unittest.main()
