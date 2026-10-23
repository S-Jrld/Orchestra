"""Adapter conformance tests for MockAdapter."""

import unittest

from orchestra.adapters.mock import MockAdapter
from orchestra.models import TaskContract, WorkflowStep


class TestMockAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = MockAdapter()

    def test_capabilities_declared(self):
        caps = self.adapter.get_capabilities()
        self.assertTrue(caps["supports_subagents"])
        self.assertTrue(caps["supports_permissions"])

    def test_environment_validation(self):
        ok, issues = self.adapter.validate_environment()
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_step_invocation(self):
        step = WorkflowStep(id="s1", name="Test Step", agent_role="orchestra")
        contract = TaskContract(
            schema_version="1.0.0",
            task_id="t1",
            objective="Do work",
            agent_role="orchestra",
            scope={"allowed_paths": ["."]},
            acceptance_criteria=["Done"],
            verification_command="true",
        )
        res = self.adapter.invoke_step(step, contract, {})
        self.assertEqual(res.status, "succeeded")
        self.assertIn("input_tokens", res.token_usage)
        self.assertEqual(len(self.adapter.invoked_steps), 1)


if __name__ == "__main__":
    unittest.main()
