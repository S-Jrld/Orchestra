"""Integration tests for Declarative Workflow Engine."""

from pathlib import Path
import unittest

from orchestra.adapters.mock import MockAdapter
from orchestra.budget.manager import BudgetManager
from orchestra.budget.profiles import BudgetProfileManager
from orchestra.models import RunStatus, StepStatus, StructuredResult, Tier, WorkflowDefinition, WorkflowStep
from orchestra.security.policy import SecurityPolicyEngine
from orchestra.workflow.engine import WorkflowEngine
from orchestra.workflow.state import RunStateManager


class TestWorkflowEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.parent.parent
        self.state_mgr = RunStateManager(self.root)
        self.sec = SecurityPolicyEngine(self.root)

    def test_end_to_end_workflow_run(self):
        steps = [
            WorkflowStep(
                id="step1",
                name="First Step",
                agent_role="researcher",
                dependencies=[],
                verification_command="true",
            ),
            WorkflowStep(
                id="step2",
                name="Second Step",
                agent_role="orchestra",
                dependencies=["step1"],
                verification_command="true",
            ),
        ]
        wf = WorkflowDefinition(
            schema_version="1.0.0",
            id="test-e2e",
            version="1.0.0",
            name="E2E Test Workflow",
            description="Testing end-to-end DAG execution",
            tier=Tier.NORMAL,
            steps=steps,
            acceptance_criteria=["All steps green"],
        )

        adapter = MockAdapter()
        profile = BudgetProfileManager.get_profile(Tier.NORMAL.value)
        b_mgr = BudgetManager(profile)

        engine = WorkflowEngine(wf, adapter, self.state_mgr, b_mgr, self.sec)
        record = engine.run(task_description="Test E2E run")

        self.assertEqual(record.status, RunStatus.SUCCEEDED)
        self.assertEqual(len(record.step_records), 2)
        self.assertTrue(all(s.status == StepStatus.SUCCEEDED for s in record.step_records))
        self.assertEqual(len(adapter.invoked_steps), 2)

    def test_workflow_retry_on_failure(self):
        steps = [
            WorkflowStep(
                id="failing_step",
                name="Failing Step",
                agent_role="tester",
                dependencies=[],
                retry_limit=1,
            ),
        ]
        wf = WorkflowDefinition(
            schema_version="1.0.0",
            id="test-retry",
            version="1.0.0",
            name="Retry Test",
            description="Testing retry behavior",
            tier=Tier.TINY,
            steps=steps,
            acceptance_criteria=[],
        )

        # Mock adapter configured to fail on failing_step
        adapter = MockAdapter(simulate_failure_step="failing_step")
        profile = BudgetProfileManager.get_profile(Tier.TINY.value)
        b_mgr = BudgetManager(profile)

        engine = WorkflowEngine(wf, adapter, self.state_mgr, b_mgr, self.sec)

        with self.assertRaises(RuntimeError) as ctx:
            engine.run()
        self.assertIn("failed after 2 attempts", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
