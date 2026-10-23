"""Adapter conformance tests for CursorAdapter."""

import tempfile
from pathlib import Path
import unittest

from orchestra.adapters.cursor import CursorAdapter
from orchestra.models import SkillManifest, TaskContract, WorkflowStep


class TestCursorAdapter(unittest.TestCase):
    def test_capabilities_declared(self):
        adapter = CursorAdapter()
        caps = adapter.get_capabilities()
        self.assertTrue(caps["supports_plugins"])
        self.assertTrue(caps["supports_subagents"])
        self.assertFalse(caps["supports_permissions"])

    def test_environment_validation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            adapter = CursorAdapter(tmp_dir)
            ok, issues = adapter.validate_environment()
            # In empty directory without cursor binary or .cursor/.vscode
            # Now create .cursor directory
            (Path(tmp_dir) / ".cursor").mkdir()
            ok_after, issues_after = adapter.validate_environment()
            self.assertTrue(ok_after)

    def test_skill_installation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            adapter = CursorAdapter(tmp_dir)
            skill_src = Path(tmp_dir) / "source_skill"
            skill_src.mkdir()
            (skill_src / "SKILL.md").write_text("# Test Skill")

            manifest = SkillManifest(
                schema_version="1.0.0",
                id="cursor_test_skill",
                name="Cursor Test",
                version="1.0.0",
                kind="task-leaf",
                summary="Summary",
                triggers={"intents": ["test"], "keywords": ["test"]},
                capabilities=["test"],
                path=str(skill_src),
            )

            installed = adapter.install_skills([manifest])
            self.assertEqual(installed, ["cursor_test_skill"])
            dest = adapter.skills_dir / "cursor_test_skill" / "SKILL.md"
            self.assertTrue(dest.is_file())

    def test_rule_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "AGENTS.md").write_text("Constitutional Rules Here")
            (root / "ORCHESTRATOR.md").write_text("Routing Rules Here")

            adapter = CursorAdapter(str(root))
            rule_path = adapter.generate_rules()
            self.assertTrue(rule_path.is_file())
            content = rule_path.read_text()
            self.assertIn("Constitutional Rules Here", content)
            self.assertIn("Routing Rules Here", content)
            self.assertIn("alwaysApply: true", content)

    def test_step_invocation(self):
        adapter = CursorAdapter()
        step = WorkflowStep(
            id="cursor_step",
            name="Cursor Code Step",
            agent_role="orchestra",
            dependencies=[],
            target_files=["src/app.py"],
        )
        contract = TaskContract(
            schema_version="1.0.0",
            task_id="task_cursor_001",
            objective="Build component",
            agent_role="orchestra",
            scope={"allowed_paths": ["src/app.py"]},
            acceptance_criteria=["Tests green"],
            verification_command="pytest",
        )
        res = adapter.invoke_step(step, contract, {})
        self.assertEqual(res.status, "succeeded")
        self.assertIn("src/app.py", res.changed_files)


if __name__ == "__main__":
    unittest.main()
