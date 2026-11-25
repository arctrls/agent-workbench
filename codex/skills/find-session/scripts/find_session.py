#!/usr/bin/env python3
"""Find local Codex conversations without searching tool payloads or modifying history."""

import argparse
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


UTC = dt.timezone.utc
INJECTED_PREFIXES = ('# AGENTS.md instructions', '<environment_context>')


def database(home, prefix):
    paths = [p for p in home.glob(f'{prefix}_*.sqlite') if re.fullmatch(rf'{prefix}_\d+\.sqlite', p.name)]
    return max(paths, key=lambda p: int(p.stem.rsplit('_', 1)[1]), default=None)


def connect(path):
    return sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)


def timestamp(value):
    if not value:
        return None
    try:
        date = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        return date.replace(tzinfo=UTC) if date.tzinfo is None else date
    except (ValueError, TypeError):
        return None


def boundary(value, zone, *, upper=False):
    if value is None:
        return None
    date = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if len(value) == 10 and upper:
        date += dt.timedelta(days=1)
    if date.tzinfo is None:
        date = date.replace(tzinfo=zone)
    return date.timestamp()


def text_content(content):
    return '\n'.join(c.get('text', '') for c in content if c.get('type') in ('text', 'input_text', 'output_text'))


def excerpt(text, terms, size=240):
    positions = [text.casefold().find(term.casefold()) for term in terms]
    pos = min((i for i in positions if i >= 0), default=0)
    start = max(0, pos - 65)
    end = min(len(text), start + size)
    return ('…' if start else '') + text[start:end].strip() + ('…' if end < len(text) else '')


@dataclass
class Session:
    identifier: str
    title: str = ''
    cwd: str = ''
    path: str = ''
    active: bool = False
    body_terms: set = field(default_factory=set)
    evidence: list = field(default_factory=list)
    seen: dict = field(default_factory=dict)
    last_match: float = 0


class Search:
    def __init__(self, args):
        self.args = args
        self.sessions = {}
        self.warnings = []
        self.sources = set()
        self.messages_scanned = 0
        self.covered = set()
        self.projections = {}
        self.project = args.project.casefold() if args.project else ''

    def warn(self, message):
        if message not in self.warnings:
            self.warnings.append(message)

    def session(self, identifier):
        if identifier not in self.sessions:
            self.sessions[identifier] = Session(identifier)
        return self.sessions[identifier]

    def allowed(self, session):
        return session.identifier not in self.args.exclude_session and (not self.project or self.project in session.cwd.casefold())

    def in_range(self, stamp):
        return (self.args.since is None or stamp >= self.args.since) and (self.args.until is None or stamp < self.args.until)

    def load_metadata(self, home):
        path = database(home, 'state')
        if path:
            try:
                with closing(connect(path)) as c:
                    for identifier, title, cwd, rollout in c.execute('SELECT id, title, cwd, rollout_path FROM threads'):
                        s = self.session(identifier)
                        s.title, s.cwd, s.path = title or '', cwd or '', rollout or ''
            except sqlite3.Error as error:
                self.warn(f'Metadata database unavailable ({type(error).__name__}); using session index and rollout metadata.')
        index = home / 'session_index.jsonl'
        if index.is_file():
            with index.open(encoding='utf-8') as stream:
                for line in stream:
                    try:
                        entry = json.loads(line)
                        if entry.get('id') and entry.get('thread_name'):
                            self.session(entry['id']).title = entry['thread_name']
                    except (ValueError, TypeError):
                        self.warn('Some session index entries could not be read.')

    def add_message(self, session, role, text, stamp, *, source, line=None, item_id=None, phase=None):
        if not text or text.lstrip().startswith(INJECTED_PREFIXES) or not self.in_range(stamp):
            return
        if not self.allowed(session):
            return
        session.active = True
        key = (role, text)
        previous = session.seen.get(key)
        if previous is not None and abs(previous - stamp) < 2:
            return
        session.seen[key] = stamp
        self.messages_scanned += 1
        found = [term for term in self.args.term if term.casefold() in text.casefold()]
        if not found:
            return
        session.body_terms.update(found)
        session.last_match = max(session.last_match, stamp)
        evidence = {'role':role, 'timestamp':dt.datetime.fromtimestamp(stamp, self.args.zone).isoformat(),
                    'matched_terms':found, 'text':excerpt(text, found), 'source':source}
        if line is not None:
            evidence['line'] = line
            evidence['path'] = source
        if item_id is not None:
            evidence['item_id'] = item_id
        evidence['_sort'] = (len(found), role == 'user', phase == 'final_answer', stamp)
        session.evidence.append(evidence)
        session.evidence.sort(key=lambda e:e['_sort'], reverse=True)
        del session.evidence[3:]

    def search_database(self, home):
        path = database(home, 'thread_history')
        if not path:
            return
        try:
            with closing(connect(path)) as c:
                # These local projection schemas are optional; inspect before using them.
                tables = {row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                columns = {row[1] for row in c.execute('PRAGMA table_info(thread_items)')}
                if not {'thread_id','item_id','created_at_ms','item_type','item_json'} <= columns:
                    raise sqlite3.OperationalError('Unsupported conversation projection schema')
                if 'thread_history_projection_state' in tables:
                    self.projections = dict(c.execute('SELECT thread_id, next_rollout_byte_offset FROM thread_history_projection_state'))
                turn_ids = set()
                candidates = None
                if 'thread_turns' in tables:
                    turn_ids = {r[0] for r in c.execute('SELECT DISTINCT thread_id FROM thread_turns')}
                    if self.args.since is not None or self.args.until is not None:
                        clauses, params = [], []
                        if self.args.since is not None:
                            clauses.append('(completed_at IS NULL OR completed_at >= ?)')
                            params.append(self.args.since)
                        if self.args.until is not None:
                            clauses.append('(started_at IS NULL OR started_at < ?)')
                            params.append(self.args.until)
                        candidates = {r[0] for r in c.execute('SELECT DISTINCT thread_id FROM thread_turns WHERE '+' AND '.join(clauses),params)}
                all_ids = set(self.projections) or {r[0] for r in c.execute('SELECT DISTINCT thread_id FROM thread_items')}
                # A projection checkpoint alone does not establish message coverage for old schemas.
                self.covered = {identifier for identifier in all_ids if c.execute(
                    "SELECT 1 FROM thread_items WHERE thread_id=? AND item_type IN ('userMessage','agentMessage') LIMIT 1",
                    [identifier]).fetchone()}
                if candidates is not None:
                    candidates |= self.covered - turn_ids
                else:
                    candidates = self.covered
                clauses = ["thread_id = ?", "item_type IN ('userMessage','agentMessage')"]
                params = []
                if self.args.since is not None:
                    clauses.append('created_at_ms >= ?')
                    params.append(self.args.since*1000)
                if self.args.until is not None:
                    clauses.append('created_at_ms < ?')
                    params.append(self.args.until*1000)
                sql = 'SELECT item_id, created_at_ms, item_type, item_json FROM thread_items WHERE '+' AND '.join(clauses)
                for identifier in sorted(candidates):
                    session = self.session(identifier)
                    if not self.allowed(session):
                        continue
                    for item_id, ms, kind, content in c.execute(sql,[identifier,*params]):
                        try:
                            item = json.loads(content)
                            text = text_content(item.get('content',[])) if kind == 'userMessage' else item.get('text','')
                            self.add_message(session,'user' if kind == 'userMessage' else 'assistant',text,ms/1000,
                                             source='thread_history',item_id=item_id,phase=item.get('phase'))
                        except (ValueError, TypeError, AttributeError):
                            self.warn('Some conversation projection messages could not be read.')
                self.sources.add('thread_history')
        except sqlite3.Error as error:
            self.covered.clear()
            self.projections.clear()
            self.warn(f'Conversation database unavailable ({type(error).__name__}); searching rollout logs instead.')

    @contextmanager
    def open_log(self, path):
        if path.suffix != '.zst':
            with path.open('rb') as stream:
                yield stream
            return
        executable = shutil.which('zstd')
        if not executable:
            raise OSError('zstd is required to read compressed rollout archives')
        process = subprocess.Popen([executable,'-dc','--',str(path)],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        try:
            yield process.stdout
            # A projected log may be skipped after its header. Do not wait on a full pipe.
            if process.stdout.read(1):
                return
            if process.wait(timeout=5) != 0:
                raise OSError('Compressed rollout could not be decoded')
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            process.stdout.close()

    def search_log(self, path):
        # Older sessions can resume today. Filter by file mtime, never creation-directory date.
        if self.args.since is not None and path.stat().st_mtime < self.args.since:
            self.sources.add('rollout')
            return
        with self.open_log(path) as stream:
            header = json.loads(stream.readline())
            if header.get('type') != 'session_meta' or not header.get('payload',{}).get('id'):
                self.warn(f'Rollout metadata missing: {path.name}')
                return
            meta = header['payload']
            session = self.session(meta['id'])
            session.cwd = session.cwd or meta.get('cwd','')
            session.path = session.path or str(path)
            if not self.allowed(session):
                return
            offset = self.projections.get(session.identifier)
            if session.identifier in self.covered and offset is not None and session.path == str(path):
                if path.suffix == '.zst' or path.stat().st_size == offset:
                    return
                if 0 < offset < path.stat().st_size:
                    stream.seek(offset)
            self.sources.add('rollout')
            if offset and session.identifier in self.covered and session.path == str(path) and path.suffix != '.zst':
                base_line = None
            else:
                base_line = 1
            for count, line in enumerate(stream,1):
                try:
                    record = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    self.warn(f'Some rollout records could not be read: {path.name}')
                    continue
                stamp = timestamp(record.get('timestamp'))
                if stamp is None or not self.in_range(stamp.timestamp()):
                    continue
                payload = record.get('payload',{})
                role, text = None, ''
                if record.get('type') == 'response_item' and payload.get('type') == 'message' and payload.get('role') in ('user','assistant'):
                    role = payload['role']
                    text = text_content(payload.get('content',[]))
                elif record.get('type') == 'event_msg' and payload.get('type') in ('user_message','agent_message'):
                    role = 'user' if payload['type'] == 'user_message' else 'assistant'
                    text = payload.get('message','')
                if role:
                    self.add_message(session,role,text,stamp.timestamp(),source=str(path),
                                     line=None if base_line is None else base_line+count,phase=payload.get('phase'))

    def search_logs(self, home):
        known_paths = {}
        for session in self.sessions.values():
            if session.path:
                known_paths[session.path] = session
                if session.path.endswith('.jsonl'):
                    # Codex may compress a fully projected log without rewriting its metadata path.
                    known_paths[session.path + '.zst'] = session
        for folder in (home/'sessions',home/'archived_sessions'):
            if not folder.is_dir():
                continue
            for path in folder.rglob('rollout-*.jsonl*'):
                if path.name.endswith(('.jsonl','.jsonl.zst')):
                    try:
                        known = known_paths.get(str(path))
                        if known and known.identifier in self.covered and known.identifier in self.projections:
                            if path.suffix == '.zst' or path.stat().st_size == self.projections[known.identifier]:
                                continue
                        self.search_log(path)
                    except (OSError, ValueError, TypeError) as error:
                        self.warn(f'Rollout skipped: {path.name} ({type(error).__name__}: {error})')

    def results(self):
        results = []
        for session in self.sessions.values():
            if not session.active or not self.allowed(session):
                continue
            title_terms = {t for t in self.args.term if t.casefold() in session.title.casefold()}
            matched = session.body_terms | title_terms
            if not matched or (self.args.all_terms and len(matched) != len(self.args.term)):
                continue
            evidence = [{k:v for k,v in e.items() if not k.startswith('_')} for e in session.evidence]
            results.append({'session_id':session.identifier,'title':session.title or '(untitled)',
                            'project':session.cwd,'rollout_path':session.path,
                            'matched_terms':[t for t in self.args.term if t in matched],
                            'missing_terms':[t for t in self.args.term if t not in matched],
                            'verification':'conversation' if session.body_terms else 'title_only',
                            'evidence':evidence,'resume_command':'codex resume '+shlex.quote(session.identifier),
                            '_sort':(len(matched),bool(session.body_terms),len(session.body_terms),session.last_match)})
        results.sort(key=lambda r:r['_sort'],reverse=True)
        for result in results:
            del result['_sort']
        return results[:self.args.limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--term',action='append',required=True,help='Literal case-insensitive keyword or phrase; repeat for more terms')
    parser.add_argument('--since',help='Inclusive local date or ISO timestamp')
    parser.add_argument('--until',help='Exclusive ISO timestamp; a date alone includes the whole date')
    parser.add_argument('--timezone',default='Asia/Seoul')
    parser.add_argument('--project',help='Substring of the session working directory')
    parser.add_argument('--exclude-session',action='append',default=[])
    parser.add_argument('--all-terms',action='store_true',help='Require all terms across the session title and in-range conversation')
    parser.add_argument('--limit',type=int,default=5)
    parser.add_argument('--codex-home',type=Path,default=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex'))))
    args = parser.parse_args()
    try:
        args.zone = ZoneInfo(args.timezone)
        args.since = boundary(args.since,args.zone)
        args.until = boundary(args.until,args.zone,upper=True)
    except (ValueError, ZoneInfoNotFoundError) as error:
        parser.error(str(error))
    if args.since is not None and args.until is not None and args.since >= args.until:
        parser.error('--since must be earlier than --until')
    args.term = list(dict.fromkeys(t.strip() for t in args.term if t.strip()))
    if not args.term or not 1 <= args.limit <= 20:
        parser.error('Provide a non-empty --term and a --limit between 1 and 20')
    home = args.codex_home.expanduser().resolve()
    started = time.perf_counter()
    search = Search(args)
    try:
        search.load_metadata(home)
        search.search_database(home)
        search.search_logs(home)
        if not search.sources:
            detail = '; '.join(search.warnings[:3])
            raise OSError('No readable Codex conversation history was found in '+str(home)+('. '+detail if detail else ''))
    except (OSError, UnicodeError) as error:
        print(f'Session search failed: {error}',file=sys.stderr)
        return 1
    response = {'results':search.results(),'elapsed_ms':round((time.perf_counter()-started)*1000),
                'sessions_searched':sum(s.active for s in search.sessions.values()),
                'messages_searched':search.messages_scanned,'sources':sorted(search.sources),
                'timezone':args.timezone,'warnings':search.warnings}
    print(json.dumps(response,ensure_ascii=False,indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
