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
            engine.run(run_id="run_retry_test")
        self.assertIn("failed after 2 attempts", str(ctx.exception))

        # Verify escalation notice created
        escalation_notice = self.root / ".orchestra" / "escalations" / "run_retry_test_failing_step_escalation.md"
        self.assertTrue(escalation_notice.is_file())
        self.assertIn("DELEGATION ESCALATION NOTICE", escalation_notice.read_text())

    def test_closed_loop_remediation_success(self):
        steps = [
            WorkflowStep(
                id="remediation_step",
                name="Remediation Step",
                agent_role="tester",
                dependencies=[],
                retry_limit=2,
            ),
        ]
        wf = WorkflowDefinition(
            schema_version="1.0.0",
            id="test-remediation",
            version="1.0.0",
            name="Remediation Test",
            description="Testing closed-loop remediation",
            tier=Tier.TINY,
            steps=steps,
            acceptance_criteria=[],
        )

        # Adapter that fails once then succeeds after observing failure reason
        class RemediationAdapter(MockAdapter):
            def __init__(self):
                super().__init__()
                self.calls = 0
                self.observed_failure_reason = None

            def invoke_step(self, step, contract, context):
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("Syntax error in test file")
                # On retry, verify remediation contract artifacts were injected
                self.observed_failure_reason = contract.input_artifacts.get("last_failure_reason")
                self.delegation_status = contract.input_artifacts.get("delegation_status")
                return StructuredResult(
                    schema_version="1.0.0",
                    task_id=contract.task_id,
                    step_id=step.id,
                    agent_role=step.agent_role,
                    status="succeeded",
                    summary="Resolved on retry",
                    changed_files=[],
                    verification_evidence="Test suite passed on remediation",
                )

        adapter = RemediationAdapter()
        profile = BudgetProfileManager.get_profile(Tier.TINY.value)
        b_mgr = BudgetManager(profile)

        engine = WorkflowEngine(wf, adapter, self.state_mgr, b_mgr, self.sec)
        record = engine.run(run_id="run_remediation_test")

        self.assertEqual(record.status, RunStatus.SUCCEEDED)
        self.assertEqual(adapter.calls, 2)
        self.assertIn("Syntax error in test file", adapter.observed_failure_reason)
        self.assertEqual(adapter.delegation_status, "remediation")
        self.assertEqual(record.step_records[0].retry_count, 1)


if __name__ == "__main__":
    unittest.main()
