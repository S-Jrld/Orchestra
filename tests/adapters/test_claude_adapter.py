"""Adapter conformance tests for ClaudeCodeAdapter."""

import tempfile
from pathlib import Path
import unittest

from orchestra.adapters.claude import ClaudeCodeAdapter
from orchestra.models import SkillManifest, TaskContract, WorkflowStep


class TestClaudeAdapter(unittest.TestCase):
    def test_capabilities_declared(self):
        adapter = ClaudeCodeAdapter()
        caps = adapter.get_capabilities()
        self.assertTrue(caps["supports_permissions"])
        self.assertTrue(caps["supports_usage_metrics"])
        self.assertFalse(caps["supports_subagents"])

    def test_environment_validation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            adapter = ClaudeCodeAdapter(tmp_dir)
            # Create CLAUDE.md
            (Path(tmp_dir) / "CLAUDE.md").write_text("# Claude Context")
            ok, issues = adapter.validate_environment()
            self.assertTrue(ok)

    def test_memory_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "AGENTS.md").write_text("Claude Constitution")
            (root / "ORCHESTRATOR.md").write_text("Claude Router")

            adapter = ClaudeCodeAdapter(str(root))
            memory_file = adapter.generate_memory()
            self.assertTrue(memory_file.is_file())
            content = memory_file.read_text()
            self.assertIn("Claude Constitution", content)
            self.assertIn("Claude Router", content)

    def test_step_invocation(self):
        adapter = ClaudeCodeAdapter()
        step = WorkflowStep(
            id="claude_step",
            name="Claude TDD Step",
            agent_role="tester",
            dependencies=[],
            target_files=["tests/test_foo.py"],
        )
        contract = TaskContract(
            schema_version="1.0.0",
            task_id="task_claude_001",
            objective="Write test",
            agent_role="tester",
            scope={"allowed_paths": ["tests/test_foo.py"]},
            acceptance_criteria=["Fails initially"],
            verification_command="pytest",
        )
        res = adapter.invoke_step(step, contract, {})
        self.assertEqual(res.status, "succeeded")
        self.assertIn("token_usage", res.__dict__)
        self.assertGreater(res.token_usage["total_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
