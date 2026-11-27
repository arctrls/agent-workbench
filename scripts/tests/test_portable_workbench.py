from pathlib import Path
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'codex'))
import sync


class PortableWorkbenchTests(unittest.TestCase):
    def test_codex_home_is_default_target(self):
        with patch.dict(os.environ, {'CODEX_HOME': '/isolated/account'}):
            self.assertEqual(sync.default_target(), Path('/isolated/account'))

    def test_environment_file_does_not_execute_and_process_values_win(self):
        from environment import load_environment
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'env'
            marker = Path(tmp) / 'must-not-exist'
            p.write_text(f'MYSQL_READ_DEV_HOST=file-host\nVALUE=$(touch {marker})\n')
            result = load_environment({'AGENT_WORKBENCH_ENV_FILE': str(p), 'MYSQL_READ_DEV_HOST': 'process-host'})
            self.assertEqual(result['MYSQL_READ_DEV_HOST'], 'process-host')
            self.assertEqual(result['VALUE'], f'$(touch {marker})')
            self.assertFalse(marker.exists())

    def test_portable_config_without_private_values_preserves_existing_mysql(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'config.toml'
            target.write_text('[mcp_servers.mysql-mcp-server]\ncommand="custom"\nargs=["existing"]\n')
            plan = sync.plan_config(ROOT / 'codex/config.base.toml', target, environment={})
            import tomllib
            result = tomllib.loads(plan.output)
            self.assertEqual(result['mcp_servers']['mysql-mcp-server']['command'], 'custom')
            self.assertEqual(result['mcp_servers']['rea']['command'], 'npx')
            self.assertNotIn('PATH', result['mcp_servers']['rea'].get('env', {}))

    def test_partial_mysql_settings_fail_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'config.toml'
            with self.assertRaisesRegex(ValueError, 'MYSQL_READ_DEV'):
                sync.plan_config(ROOT / 'codex/config.base.toml', target, environment={'MYSQL_READ_DEV_HOST': 'db.invalid'})
            self.assertFalse(target.exists())

    def test_mysql_settings_are_supplied_by_environment(self):
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            env = {'MYSQL_READ_DEV_HOST': 'db.invalid', 'MYSQL_READ_DEV_SECRET_ARN': 'arn:example',
                   'MYSQL_READ_DEV_DATABASE': 'example_db', 'MYSQL_READ_DEV_REGION': 'test-region'}
            target = Path(tmp) / 'config.toml'
            plan = sync.plan_config(ROOT / 'codex/config.base.toml', target, environment=env)
            server = tomllib.loads(plan.output)['mcp_servers']['mysql-mcp-server']
            self.assertIn('db.invalid', server['args'])
            self.assertIn('example_db', server['args'])
            self.assertNotIn('db.invalid', '\n'.join(plan.changes))

    def test_secret_filter_detects_synthetic_token_and_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'scripts').mkdir()
            script = root / 'scripts/check-sensitive-data.sh'
            script.write_bytes((ROOT / 'scripts/check-sensitive-data.sh').read_bytes())
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'fixture.txt').write_text('AKIA' + 'Z' * 16 + '\n')
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
            result = subprocess.run(['bash', str(script)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Potential Secret', result.stdout)
            self.assertNotIn('unknown encoding', result.stderr)


class SharedSkillsTests(unittest.TestCase):
    def run_sync(self, target, shared, envfile, *flags):
        env = {k:v for k,v in os.environ.items() if not k.startswith(('MYSQL_READ_', 'REA_'))}
        env['AGENT_WORKBENCH_ENV_FILE'] = str(envfile)
        return subprocess.run([sys.executable, str(ROOT/'codex/sync.py'), '--target-dir', str(target),
                               '--shared-skills-dir', str(shared), *flags], env=env, capture_output=True, text=True)

    def test_shared_links_work_for_another_account_and_preserve_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'personal';shared=root/'user-skills';other=root/'work'
            target.mkdir();other.mkdir()
            (target/'auth.json').write_text('personal-auth-fixture')
            (other/'auth.json').write_text('work-auth-fixture')
            preview=self.run_sync(target,shared,root/'no-env','--dry-run')
            self.assertEqual(preview.returncode,0,preview.stderr)
            self.assertFalse(shared.exists())
            self.assertFalse((target/'config.toml').exists())
            result=self.run_sync(target,shared,root/'no-env')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual((shared/'spring-review/SKILL.md').read_bytes(),(ROOT/'codex/skills/spring-review/SKILL.md').read_bytes())
            self.assertEqual((target/'auth.json').read_text(),'personal-auth-fixture')
            self.assertEqual((other/'auth.json').read_text(),'work-auth-fixture')
            again=self.run_sync(target,shared,root/'no-env')
            self.assertEqual(again.stdout.strip(),'No changes.')

    def test_foreign_shared_skill_blocks_before_config_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'personal';shared=root/'user-skills'
            (shared/'spring-review').mkdir(parents=True)
            (shared/'spring-review/SKILL.md').write_text('owned by someone else')
            result=self.run_sync(target,shared,root/'no-env')
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((target/'config.toml').exists())
            self.assertEqual((shared/'spring-review/SKILL.md').read_text(),'owned by someone else')

    def test_claude_links_point_to_installed_skills_except_codex_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'personal';shared=root/'user-skills';claude=root/'claude-skills'
            flags=('--claude-skills-dir',str(claude))
            preview=self.run_sync(target,shared,root/'no-env','--dry-run',*flags)
            self.assertEqual(preview.returncode,0,preview.stderr)
            self.assertFalse(claude.exists())
            self.assertIn('claude skills: link spring-review',preview.stdout)
            result=self.run_sync(target,shared,root/'no-env',*flags)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(preview.stdout,result.stdout)
            link=claude/'spring-review'
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(),(target/'skills/spring-review').resolve())
            self.assertFalse((claude/'find-session').exists())
            self.assertTrue((shared/'find-session').is_symlink())
            again=self.run_sync(target,shared,root/'no-env',*flags)
            self.assertEqual(again.stdout.strip(),'No changes.')

    def test_foreign_claude_skill_blocks_before_any_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'personal';shared=root/'user-skills';claude=root/'claude-skills'
            (claude/'commit').mkdir(parents=True)
            (claude/'commit/SKILL.md').write_text('owned by someone else')
            result=self.run_sync(target,shared,root/'no-env','--claude-skills-dir',str(claude))
            self.assertNotEqual(result.returncode,0)
            self.assertIn('commit',result.stderr)
            self.assertFalse((target/'config.toml').exists())
            self.assertFalse(shared.exists())
            self.assertEqual((claude/'commit/SKILL.md').read_text(),'owned by someone else')

    def test_known_shared_account_resolves_content_but_not_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);primary=root/'personal';other=root/'work'
            primary.mkdir();other.mkdir()
            for name in ('config.toml','AGENTS.md','skills','prompts'):
                (other/name).symlink_to(primary/name)
            (other/'auth.json').write_text('separate')
            self.assertEqual(sync.content_target(other),primary.resolve())
            self.assertEqual((other/'auth.json').read_text(),'separate')
            (other/'prompts').unlink();(other/'prompts').mkdir()
            with self.assertRaises(ValueError):sync.content_target(other)

class HelperEnvironmentTests(unittest.TestCase):
    def test_mysql_missing_configuration_makes_no_external_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            env={k:v for k,v in os.environ.items() if not k.startswith(('MYSQL_READ_', 'AGENT_WORKBENCH_ENV_LOADED', 'AWS_REGION'))}
            env['AGENT_WORKBENCH_ENV_FILE']=str(Path(tmp)/'empty')
            result=subprocess.run(['bash', str(ROOT/'codex/skills/mysql-read/scripts/mysql-read.sh'),
                                   '--target','dev','--database','test','--sql','SELECT 1'],
                                  capture_output=True,text=True,env=env)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('MYSQL_READ_DEV_HOST',result.stderr)



class MigrationTests(unittest.TestCase):
    def test_migration_is_private_idempotent_and_keeps_existing_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'config.toml';env=root/'env'
            config.write_text('''[mcp_servers.mysql-mcp-server]
args=["--hostname","private-db.invalid","--secret_arn","arn:fixture","--database","example","--region","test"]
[mcp_servers.rea]
command="/custom/node/bin/npx"
''')
            env.write_text('MYSQL_READ_DEV_HOST=preserve-existing.invalid\n')
            command=[sys.executable,str(ROOT/'codex/migrate-env.py'),'--config',str(config),'--env-file',str(env)]
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertNotIn('private-db.invalid',result.stdout+result.stderr)
            self.assertNotIn('arn:fixture',result.stdout+result.stderr)
            self.assertIn('MYSQL_READ_DEV_HOST=preserve-existing.invalid',env.read_text())
            self.assertIn('MYSQL_READ_DEV_SECRET_ARN=arn:fixture',env.read_text())
            self.assertEqual(env.stat().st_mode&0o777,0o600)
            before=(env.read_bytes(),env.stat().st_mtime_ns)
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
            self.assertEqual((env.read_bytes(),env.stat().st_mtime_ns),before)

    def test_missing_overrides_preserve_existing_machine_runtime(self):
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'config.toml'
            target.write_text('[mcp_servers.rea]\ncommand="/previous/node/npx"\n[mcp_servers.rea.env]\nPATH="/previous/node:/usr/bin"\n')
            plan=sync.plan_config(ROOT/'codex/config.base.toml',target,environment={})
            rea=tomllib.loads(plan.output)['mcp_servers']['rea']
            self.assertEqual(rea['command'],'/previous/node/npx')
            self.assertEqual(rea['env']['PATH'],'/previous/node:/usr/bin')

if __name__ == '__main__':
    unittest.main()
