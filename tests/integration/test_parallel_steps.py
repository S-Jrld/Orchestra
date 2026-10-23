"""Integration tests for topological step scheduling and concurrency isolation."""

import unittest

from orchestra.models import WorkflowStep
from orchestra.workflow.scheduler import StepScheduler


class TestParallelSteps(unittest.TestCase):
    def test_topological_linear_order(self):
        steps = [
            WorkflowStep(id="step_c", name="C", agent_role="orchestra", dependencies=["step_b"]),
            WorkflowStep(id="step_a", name="A", agent_role="researcher", dependencies=[]),
            WorkflowStep(id="step_b", name="B", agent_role="advisor", dependencies=["step_a"]),
        ]
        scheduler = StepScheduler(steps)
        order = scheduler.get_linear_order()
        self.assertEqual(order, ["step_a", "step_b", "step_c"])

    def test_independent_parallel_ready_steps(self):
        steps = [
            WorkflowStep(id="step_init", name="Init", agent_role="researcher", dependencies=[]),
            WorkflowStep(id="step_test1", name="Test 1", agent_role="tester", dependencies=["step_init"], target_files=["tests/t1.py"]),
            WorkflowStep(id="step_test2", name="Test 2", agent_role="tester", dependencies=["step_init"], target_files=["tests/t2.py"]),
        ]
        scheduler = StepScheduler(steps, max_workers=2)

        # Before init completes: only init is ready
        ready_init = scheduler.get_ready_steps(completed_step_ids=set(), active_step_ids=set())
        self.assertEqual([s.id for s in ready_init], ["step_init"])

        # After init completes: both test1 and test2 are ready concurrently!
        ready_parallel = scheduler.get_ready_steps(completed_step_ids={"step_init"}, active_step_ids=set())
        ready_ids = {s.id for s in ready_parallel}
        self.assertEqual(ready_ids, {"step_test1", "step_test2"})

    def test_shared_file_conflict_blocks_concurrency(self):
        steps = [
            WorkflowStep(id="step_w1", name="Worker 1", agent_role="orchestra", dependencies=[], target_files=["src/shared.py"]),
            WorkflowStep(id="step_w2", name="Worker 2", agent_role="orchestra", dependencies=[], target_files=["src/shared.py"]),
        ]
        scheduler = StepScheduler(steps, max_workers=2)

        # If step_w1 is actively running, step_w2 must not be scheduled concurrently due to target_files collision!
        ready = scheduler.get_ready_steps(completed_step_ids=set(), active_step_ids={"step_w1"})
        self.assertEqual(ready, [], "Should block step_w2 while step_w1 modifies shared.py")


if __name__ == "__main__":
    unittest.main()
