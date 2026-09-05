from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "codex"))
import sync as codex_sync


BASE = '''[features]
multi_agent = true

[mcp_servers.example]
command = "npx"
args = ["--new"]

[mcp_servers.example.env]
FIXED = "new"
'''
LOCAL = '''# Preferences selected in the app
model = "current-model"
model_reasoning_effort = "max"
service_tier = "fast"

[features]
multi_agent = false
app_feature = true

[mcp_servers.example]
command = "old-command"
args = ["--old"]
enabled = false

[mcp_servers.example.env]
FIXED = "old"
LOCAL_ONLY = "private-value-do-not-print"

[mcp_servers.node_repl]
command = "/app/runtime"

[plugins."runtime@bundled"]
enabled = true

[desktop]
theme = "current-theme"
'''


def snapshot(root: Path) -> dict:
    if not root.exists():
        return {}
    result = {}
    for path in sorted(root.rglob("*")):
        name = str(path.relative_to(root))
        if path.is_symlink():
            result[name] = ("symlink", os.readlink(path))
        elif path.is_file():
            result[name] = (
                hashlib.sha256(path.read_bytes()).hexdigest(),
                path.stat().st_mode & 0o777,
                path.stat().st_mtime_ns,
            )
    return result


class CodexSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex-sync-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "repo" / "codex"
        self.target = self.root / "target"
        self.source.mkdir(parents=True)
        self.target.mkdir()
        for name in ("sync.sh", "sync.py"):
            if (REPO / "codex" / name).exists():
                shutil.copy2(REPO / "codex" / name, self.source / name)
        self.write_source("config.base.toml", BASE)
        self.write_source("AGENTS.user.md", "new instructions\n")
        self.write_source("prompts/managed.md", "new prompt\n")
        self.write_source("skills/demo/SKILL.md", "new skill\n")
        self.write_source("skills/demo/scripts/run.sh", "#!/bin/sh\nexit 0\n")
        (self.source / "skills/demo/scripts/run.sh").chmod(0o755)
        self.write_source("skills/.system/builtin/SKILL.md", "old bundled skill\n")
        self.write_target("config.toml", LOCAL)
        (self.target / "config.toml").chmod(0o600)
        self.write_target("AGENTS.md", "old instructions\n")
        self.write_target("prompts/managed.md", "old prompt\n")
        self.write_target("prompts/local-only.md", "keep this prompt\n")
        self.write_target("skills/demo/SKILL.md", "old skill\n")
        self.write_target("skills/demo/obsolete.md", "remove within owned skill\n")
        self.write_target("skills/.system/builtin/SKILL.md", "new bundled skill\n")
        self.write_target("skills/.system/new-builtin/SKILL.md", "keep bundled skill\n")
        self.write_target("skills/local-only/SKILL.md", "keep local skill\n")

    def write_source(self, name, content):
        self.write(self.source / name, content)

    def write_target(self, name, content):
        self.write(self.target / name, content)

    @staticmethod
    def write(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def run_sync(self, *args):
        command = ["/bin/bash", str(self.source / "sync.sh"), "--target-dir", str(self.target)]
        return subprocess.run(command + list(args), capture_output=True, text=True)

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_repository_base_only_manages_mcp_and_features(self):
        base = tomllib.loads((REPO / "codex/config.base.toml").read_text())
        self.assertEqual(set(base), {"features", "mcp_servers"})

    def test_managed_keys_update_without_removing_app_settings(self):
        before = tomllib.loads(LOCAL)
        self.assert_success(self.run_sync())
        after = tomllib.loads((self.target / "config.toml").read_text())
        for name in ("model", "model_reasoning_effort", "service_tier", "plugins", "desktop"):
            self.assertEqual(after[name], before[name])
        self.assertTrue(after["features"]["multi_agent"])
        self.assertTrue(after["features"]["app_feature"])
        self.assertEqual(after["mcp_servers"]["node_repl"], before["mcp_servers"]["node_repl"])
        server = after["mcp_servers"]["example"]
        self.assertEqual(server["command"], "npx")
        self.assertEqual(server["args"], ["--new"])
        self.assertFalse(server["enabled"])
        self.assertEqual(server["env"], {"FIXED": "new", "LOCAL_ONLY": "private-value-do-not-print"})
        self.assertEqual((self.target / "config.toml").stat().st_mode & 0o777, 0o600)

    def test_only_owned_skill_contents_are_deleted(self):
        protected = [
            "skills/.system/builtin/SKILL.md",
            "skills/.system/new-builtin/SKILL.md",
            "skills/local-only/SKILL.md",
            "prompts/local-only.md",
        ]
        before = {name: (self.target / name).read_bytes() for name in protected}
        self.assert_success(self.run_sync())
        for name in protected:
            self.assertEqual((self.target / name).read_bytes(), before[name])
        self.assertFalse((self.target / "skills/demo/obsolete.md").exists())
        self.assertEqual((self.target / "skills/demo/SKILL.md").read_text(), "new skill\n")
        self.assertTrue((self.target / "skills/demo/scripts/run.sh").stat().st_mode & 0o111)

    def test_removing_a_skill_from_repo_does_not_delete_local_skill(self):
        shutil.rmtree(self.source / "skills/demo")
        before = snapshot(self.target / "skills")
        self.assert_success(self.run_sync())
        self.assertEqual(snapshot(self.target / "skills"), before)

    def test_dry_run_previews_same_changes_without_writes_or_secret_values(self):
        before = snapshot(self.target)
        preview = self.run_sync("--dry-run")
        self.assert_success(preview)
        self.assertEqual(snapshot(self.target), before)
        self.assertIn("features.multi_agent", preview.stdout)
        self.assertIn("mcp_servers.example.args", preview.stdout)
        self.assertIn("obsolete.md", preview.stdout)
        self.assertIn("deleting", preview.stdout)
        self.assertNotIn("private-value-do-not-print", preview.stdout + preview.stderr)
        applied = self.run_sync()
        self.assert_success(applied)
        self.assertEqual(preview.stdout, applied.stdout)

    def test_repeated_sync_does_not_rewrite_unchanged_files(self):
        self.assert_success(self.run_sync())
        before = snapshot(self.target)
        self.assert_success(self.run_sync())
        self.assertEqual(snapshot(self.target), before)

    def test_identical_instructions_are_not_reported_as_a_change(self):
        self.write_target("AGENTS.md", (self.source / "AGENTS.user.md").read_text())
        result = self.run_sync("--dry-run")
        self.assert_success(result)
        self.assertNotIn("AGENTS.md:", result.stdout)

    def test_invalid_target_toml_leaves_every_target_unchanged(self):
        self.write_target("config.toml", "invalid = [\n")
        before = snapshot(self.target)
        result = self.run_sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(snapshot(self.target), before)

    def test_invalid_base_toml_leaves_every_target_unchanged(self):
        self.write_source("config.base.toml", "invalid = [\n")
        before = snapshot(self.target)
        result = self.run_sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(snapshot(self.target), before)

    def test_app_owned_keys_in_base_are_rejected_before_writes(self):
        self.write_source("config.base.toml", 'model_reasoning_effort = "high"\n' + BASE)
        before = snapshot(self.target)
        result = self.run_sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("model_reasoning_effort", result.stderr)
        self.assertEqual(snapshot(self.target), before)

    def test_unmanaged_toml_arrays_and_dates_survive_managed_update(self):
        extra = '''
[local_metadata]
date = 2026-09-05
time = 12:34:56.123
timestamp = 2026-09-05T12:34:56+09:00
"quoted\\tkey" = "control\\u0001value"
nested = [{ name = "one", values = [1, 2] }]

[[skills.config]]
path = "/local/example/SKILL.md"
enabled = false
'''
        self.write_target("config.toml", LOCAL + extra)
        before = tomllib.loads(LOCAL + extra)
        self.assert_success(self.run_sync())
        after = tomllib.loads((self.target / "config.toml").read_text())
        self.assertEqual(after["skills"], before["skills"])
        self.assertEqual(after["local_metadata"], before["local_metadata"])

    def test_fresh_target_preview_and_sync(self):
        shutil.rmtree(self.target)
        preview = self.run_sync("--dry-run")
        self.assert_success(preview)
        self.assertFalse(self.target.exists())
        self.assert_success(self.run_sync())
        self.assertEqual(tomllib.loads((self.target / "config.toml").read_text()), tomllib.loads(BASE))
        self.assertTrue((self.target / "skills/demo/SKILL.md").exists())
        self.assertFalse((self.target / "skills/.system").exists())

    def test_symlinked_managed_target_is_rejected_before_any_changes(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.write(outside / "keep.md", "keep unrelated data\n")
        shutil.rmtree(self.target / "skills/demo")
        (self.target / "skills/demo").symlink_to(outside, target_is_directory=True)
        before = snapshot(self.target)
        result = self.run_sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(snapshot(self.target), before)
        self.assertEqual((outside / "keep.md").read_text(), "keep unrelated data\n")

    def test_app_change_while_staging_config_is_preserved(self):
        target = self.target / "config.toml"
        plan = codex_sync.plan_config(self.source / "config.base.toml", target)
        app_update = LOCAL.replace('model_reasoning_effort = "max"', 'model_reasoning_effort = "low"')
        with patch.object(codex_sync.os, "fsync", side_effect=lambda _: target.write_text(app_update)):
            with self.assertRaisesRegex(ValueError, "changed during sync"):
                plan.apply()
        self.assertEqual(target.read_text(), app_update)
        self.assertEqual(list(self.target.glob(".config.toml.sync-*")), [])

    def test_failed_config_replace_keeps_original_and_removes_temporary_file(self):
        target = self.target / "config.toml"
        plan = codex_sync.plan_config(self.source / "config.base.toml", target)
        original = snapshot(self.target)
        with patch.object(codex_sync.os, "replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaisesRegex(OSError, "simulated replace failure"):
                plan.apply()
        self.assertEqual(snapshot(self.target), original)


if __name__ == "__main__":
    unittest.main()
