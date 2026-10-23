"""Integration tests for Run State Persistence and Recovery."""

import tempfile
from pathlib import Path
import unittest

from orchestra.models import RunStatus, StepStatus
from orchestra.workflow.state import RunStateManager


class TestRunState(unittest.TestCase):
    def test_run_persistence_and_recovery(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = RunStateManager(tmp_dir)
            step_meta = [
                {"id": "step_a", "name": "Step A", "agent_role": "researcher"},
                {"id": "step_b", "name": "Step B", "agent_role": "advisor"},
            ]
            run = mgr.create_run(
                run_id="run_test_001",
                workflow_id="wf_example",
                tier="Normal",
                adapter_name="mock",
                step_ids=step_meta,
                task_description="Sample task",
            )

            self.assertEqual(run.run_id, "run_test_001")
            self.assertEqual(run.status, RunStatus.RUNNING)

            # Update step A to running, then succeeded
            mgr.update_step("run_test_001", "step_a", StepStatus.RUNNING)
            mgr.update_step("run_test_001", "step_a", StepStatus.SUCCEEDED, token_usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150})

            # Reload run from disk
            loaded = mgr.load_run("run_test_001")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.total_token_usage["total_tokens"], 150)
            self.assertEqual(loaded.step_records[0].status, StepStatus.SUCCEEDED)

            # Complete run
            mgr.complete_run("run_test_001", RunStatus.SUCCEEDED)
            completed = mgr.load_run("run_test_001")
            self.assertEqual(completed.status, RunStatus.SUCCEEDED)
            self.assertIsNotNone(completed.completed_at)

            # Verify audit trail exists and has events
            audit_file = Path(tmp_dir) / ".orchestra" / "audit.jsonl"
            self.assertTrue(audit_file.is_file())
            lines = audit_file.read_text().strip().split("\n")
            self.assertGreaterEqual(len(lines), 4)


if __name__ == "__main__":
    unittest.main()
