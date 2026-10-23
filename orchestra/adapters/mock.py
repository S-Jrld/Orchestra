"""In-memory mock adapter for deterministic runtime and integration testing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from orchestra.adapters.base import ClientAdapter
from orchestra.models import SkillManifest, StructuredResult, TaskContract, WorkflowStep


class MockAdapter(ClientAdapter):
    """Deterministic mock adapter simulating agent responses and token metrics."""

    def __init__(
        self,
        step_responses: Optional[Dict[str, StructuredResult]] = None,
        simulate_failure_step: Optional[str] = None,
    ):
        self.step_responses = step_responses or {}
        self.simulate_failure_step = simulate_failure_step
        self.invoked_steps: List[WorkflowStep] = []
        self.installed_skills: List[str] = []

    def get_name(self) -> str:
        return "mock"

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "supports_subagents": True,
            "supports_permissions": True,
            "supports_background": True,
            "supports_structured_output": True,
            "supports_plugins": True,
            "supports_usage_metrics": True,
        }

    def validate_environment(self) -> Tuple[bool, List[str]]:
        return True, []

    def install_skills(self, skills: List[SkillManifest], target_dir: str) -> List[str]:
        installed = [s.id for s in skills]
        self.installed_skills.extend(installed)
        return installed

    def invoke_step(
        self,
        step: WorkflowStep,
        contract: TaskContract,
        context: Dict[str, str],
    ) -> StructuredResult:
        self.invoked_steps.append(step)

        if self.simulate_failure_step and step.id == self.simulate_failure_step:
            raise RuntimeError(f"Simulated failure on step: {step.id}")

        if step.id in self.step_responses:
            return self.step_responses[step.id]

        # Default simulated successful response conforming to StructuredResult schema
        return StructuredResult(
            schema_version="1.0.0",
            task_id=contract.task_id,
            step_id=step.id,
            agent_role=step.agent_role,
            status="succeeded",
            summary=f"Mock step '{step.name}' executed successfully.",
            changed_files=step.target_files,
            verification_evidence=f"Simulated verification for step {step.id} passed cleanly.",
            tests_run=[
                {
                    "command": step.verification_command or "true",
                    "exit_code": 0,
                    "passed": 1,
                    "failed": 0,
                    "output_snippet": "1 passed in 0.01s",
                }
            ],
            token_usage={"input_tokens": 350, "output_tokens": 150, "total_tokens": 500},
        )

    def cancel(self, run_id: str) -> None:
        pass
