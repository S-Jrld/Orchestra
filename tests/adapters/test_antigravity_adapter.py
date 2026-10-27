"""Adapter conformance tests for AntigravityAdapter."""

import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from orchestra.adapters.antigravity import AntigravityAdapter
from orchestra.models import SkillManifest


class TestAntigravityAdapter(unittest.TestCase):
    def test_environment_validation(self):
        adapter = AntigravityAdapter()
        with patch("shutil.which", return_value="/usr/local/bin/agy"):
            ok, issues = adapter.validate_environment()
            self.assertTrue(ok)
            self.assertEqual(len(issues), 0)

        with patch("shutil.which", return_value=None):
            ok_missing, issues_missing = adapter.validate_environment()
            self.assertFalse(ok_missing)
            self.assertIn("not found in PATH", issues_missing[0])

    def test_plugin_packaging(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            adapter = AntigravityAdapter(tmp_dir)
            out_dir = Path(tmp_dir) / "packaged"
            plugin_dir = adapter.package_plugin(out_dir)

            self.assertTrue(plugin_dir.is_dir())
            manifest_file = plugin_dir / "plugin.json"
            self.assertTrue(manifest_file.is_file())

            with open(manifest_file) as f:
                data = json.load(f)
            self.assertEqual(data["name"], "orchestra")

    def test_workspace_skill_staging(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            adapter = AntigravityAdapter(tmp_dir)
            skill_src = Path(tmp_dir) / "src_skill"
            skill_src.mkdir()
            (skill_src / "SKILL.md").write_text("# Antigravity Skill")

            manifest = SkillManifest(
                schema_version="1.0.0",
                id="agy_skill",
                name="Agy Skill",
                version="1.0.0",
                kind="task-leaf",
                summary="Summary",
                triggers={"intents": ["test"], "keywords": ["test"]},
                capabilities=["testing"],
                path=str(skill_src),
            )

            installed = adapter.install_skills([manifest])
            self.assertEqual(installed, ["agy_skill"])
            self.assertTrue((adapter.skills_dir / "agy_skill" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
