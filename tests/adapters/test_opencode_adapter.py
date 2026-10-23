"""Adapter conformance tests for OpenCodeAdapter."""

import tempfile
from pathlib import Path
import unittest

from orchestra.adapters.opencode import OpenCodeAdapter
from orchestra.models import SkillManifest


class TestOpenCodeAdapter(unittest.TestCase):
    def test_environment_validation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            adapter = OpenCodeAdapter(tmp_dir)
            ok, issues = adapter.validate_environment()
            # On this machine, opencode is installed in PATH
            self.assertTrue(adapter.agents_dir.is_dir())
            self.assertTrue(adapter.skills_dir.is_dir())

    def test_skill_installation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            adapter = OpenCodeAdapter(tmp_dir)
            # Create a mock source skill
            skill_src = Path(tmp_dir) / "src_skill"
            skill_src.mkdir()
            (skill_src / "SKILL.md").write_text("# Mock Skill")

            manifest = SkillManifest(
                schema_version="1.0.0",
                id="test_skill",
                name="Test Skill",
                version="1.0.0",
                kind="task-leaf",
                summary="Summary",
                triggers={"intents": ["test"], "keywords": ["test"]},
                capabilities=["testing"],
                path=str(skill_src),
            )

            installed = adapter.install_skills([manifest])
            self.assertEqual(installed, ["test_skill"])
            dest_file = adapter.skills_dir / "test_skill" / "SKILL.md"
            self.assertTrue(dest_file.is_file())


if __name__ == "__main__":
    unittest.main()
