import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'codex/skills/spring-review/scripts/check_sources.py'


class ReviewRunnerTests(unittest.TestCase):
    def test_missing_tools_are_unverified_and_sources_are_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'src/Example.kt'
            source.parent.mkdir()
            source.write_text('class Example\n')
            result = subprocess.run([sys.executable, str(RUNNER), str(source), '--tool', 'ktlint',
                                     '--output', str(root/'reports')], text=True, capture_output=True,
                                    env={'PATH': '', 'SPRING_REVIEW_KTLINT': str(root/'missing'), 'AGENT_WORKBENCH_ENV_FILE': str(root/'no-env')})
            self.assertEqual(result.returncode, 2, result.stderr)
            import json
            report = json.loads((root/'reports/summary.json').read_text())
            self.assertEqual(report['checks'][0]['status'], 'unavailable')
            self.assertEqual(source.read_text(), 'class Example\n')

    def test_xml_finding_is_not_reported_as_a_pass(self):
        spec = importlib.util.spec_from_file_location('review_tools', RUNNER)
        module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'report.xml'
            path.write_text('<checkstyle><file name="a.kt"><error line="1" message="issue"/></file></checkstyle>')
            self.assertEqual(module.classify('ktlint', 1, path), ('findings', 1))
            self.assertEqual(module.classify('ktlint', 2, path)[0], 'error')
            path.write_text('<pmd><error msg="parsing failed"/></pmd>')
            self.assertEqual(module.classify('pmd', 5, path)[0], 'error')
            path.write_text('not XML')
            self.assertEqual(module.classify('pmd', 0, path)[0], 'error')

    def test_generated_code_and_symlinked_source_are_excluded(self):
        spec = importlib.util.spec_from_file_location('review_tools', RUNNER)
        module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'src').mkdir();(root/'build').mkdir()
            (root/'src/Good.java').write_text('class Good {}')
            (root/'build/Generated.java').write_text('class Generated {}')
            (root/'src/Link.java').symlink_to(root/'build/Generated.java')
            self.assertEqual(module.sources(root),[root/'src/Good.java'])


class ToolInstallationTests(unittest.TestCase):
    def test_bad_checksum_never_publishes_download(self):
        import io
        from unittest.mock import patch
        sys.path.insert(0, str(RUNNER.parent))
        import setup_tools
        with tempfile.TemporaryDirectory() as tmp:
            env={'SPRING_REVIEW_CACHE_DIR': tmp}
            with patch.object(setup_tools.urllib.request, 'urlopen', return_value=io.BytesIO(b'corrupt-download')):
                with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
                    setup_tools.install('ktlint',env)
            self.assertFalse(setup_tools.cached_command('ktlint',env).exists())
            self.assertEqual(list(Path(tmp).iterdir()),[])


if __name__ == '__main__':
    unittest.main()
