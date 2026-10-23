"""Topological step scheduler with concurrency control and file conflict detection."""

from __future__ import annotations

import graphlib
from typing import Dict, List, Set

from orchestra.models import WorkflowStep


class StepScheduler:
    """Schedules workflow steps based on dependency DAG and shared-file safety."""

    def __init__(self, steps: List[WorkflowStep], max_workers: int = 4):
        self.steps = {s.id: s for s in steps}
        self.max_workers = max_workers
        self._validate_dag()

    def _validate_dag(self) -> None:
        graph: Dict[str, Set[str]] = {}
        for s_id, step in self.steps.items():
            deps = set(step.dependencies)
            # Ensure dependencies exist
            for d in deps:
                if d not in self.steps:
                    raise ValueError(f"Step '{s_id}' depends on undefined step '{d}'")
            graph[s_id] = deps

        try:
            sorter = graphlib.TopologicalSorter(graph)
            sorter.prepare()
        except graphlib.CycleError as e:
            raise ValueError(f"Workflow dependency cycle detected: {e}")

    def get_linear_order(self) -> List[str]:
        graph: Dict[str, Set[str]] = {s_id: set(s.dependencies) for s_id, s in self.steps.items()}
        sorter = graphlib.TopologicalSorter(graph)
        return list(sorter.static_order())

    def get_ready_steps(
        self,
        completed_step_ids: Set[str],
        active_step_ids: Set[str],
    ) -> List[WorkflowStep]:
        """Returns steps whose dependencies are fully met and have no file conflicts with active steps."""
        ready: List[WorkflowStep] = []
        active_files: Set[str] = set()

        for a_id in active_step_ids:
            active_step = self.steps.get(a_id)
            if active_step:
                active_files.update(active_step.target_files)

        for s_id, step in self.steps.items():
            if s_id in completed_step_ids or s_id in active_step_ids:
                continue

            # Check if all dependencies are satisfied
            deps_satisfied = all(d in completed_step_ids for d in step.dependencies)
            if not deps_satisfied:
                continue

            # Check for file modification conflicts with actively running steps
            conflicts = any(f in active_files for f in step.target_files)
            if conflicts:
                continue

            ready.append(step)

        return ready[: self.max_workers]
