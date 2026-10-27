"""Orchestra Workflow DAG execution engine."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from orchestra.adapters.base import ClientAdapter
from orchestra.budget.manager import BudgetManager
from orchestra.models import (
    RunRecord,
    RunStatus,
    StepStatus,
    StructuredResult,
    TaskContract,
    WorkflowDefinition,
    WorkflowStep,
)
from orchestra.security.policy import SecurityPolicyEngine
from orchestra.workflow.scheduler import StepScheduler
from orchestra.workflow.state import RunStateManager
from orchestra.workflow.verifier import WorkflowVerifier


class WorkflowEngine:
    """Executes declarative workflow DAGs with deterministic state management and verification."""

    def __init__(
        self,
        workflow: WorkflowDefinition,
        adapter: ClientAdapter,
        state_manager: RunStateManager,
        budget_manager: BudgetManager,
        security_engine: SecurityPolicyEngine,
        max_workers: int = 2,
    ):
        self.workflow = workflow
        self.adapter = adapter
        self.state_manager = state_manager
        self.budget_manager = budget_manager
        self.security_engine = security_engine
        self.max_workers = max_workers
        self.scheduler = StepScheduler(workflow.steps, max_workers=max_workers)
        self.verifier = WorkflowVerifier()

    def run(
        self,
        run_id: Optional[str] = None,
        task_description: Optional[str] = None,
        context_items: Optional[Dict[str, str]] = None,
    ) -> RunRecord:
        actual_run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        step_meta = [
            {"id": s.id, "name": s.name, "agent_role": s.agent_role}
            for s in self.workflow.steps
        ]

        run_record = self.state_manager.create_run(
            run_id=actual_run_id,
            workflow_id=self.workflow.id,
            tier=self.workflow.tier.value,
            adapter_name=self.adapter.get_name(),
            step_ids=step_meta,
            task_description=task_description,
        )

        completed_steps: Set[str] = set()
        step_results: Dict[str, StructuredResult] = {}

        try:
            while len(completed_steps) < len(self.workflow.steps):
                ready_steps = self.scheduler.get_ready_steps(completed_steps, set())
                if not ready_steps:
                    # Check if all remaining steps were blocked
                    remaining = [s.id for s in self.workflow.steps if s.id not in completed_steps]
                    raise RuntimeError(f"Workflow deadlocked: unable to schedule remaining steps: {remaining}")

                # Execute ready steps
                for step in ready_steps:
                    self._execute_step(actual_run_id, step, context_items, step_results)
                    completed_steps.add(step.id)

            # Evaluate final acceptance criteria
            self._evaluate_final_acceptance(actual_run_id, step_results)
            self.state_manager.complete_run(actual_run_id, RunStatus.SUCCEEDED)

        except Exception as e:
            self.state_manager.complete_run(actual_run_id, RunStatus.FAILED)
            raise

        return self.state_manager.load_run(actual_run_id)

    def _execute_step(
        self,
        run_id: str,
        step: WorkflowStep,
        context_items: Optional[Dict[str, str]],
        step_results: Dict[str, StructuredResult],
    ) -> None:
        self.state_manager.update_step(run_id, step.id, StepStatus.RUNNING)

        # 1. Budget check
        self.budget_manager.check_can_dispatch(estimated_tokens=800)

        # 2. Security checks on target files
        for target_file in step.target_files:
            self.security_engine.validate_file_access(target_file, action="write")

        # 3. Create initial task contract
        contract = TaskContract(
            schema_version="1.0.0",
            task_id=f"{run_id}_{step.id}",
            parent_run_id=run_id,
            step_id=step.id,
            objective=step.name,
            agent_role=step.agent_role,
            scope={"allowed_paths": step.target_files or ["."]},
            acceptance_criteria=[step.name],
            verification_command=step.verification_command or "true",
            selected_skills=step.required_skills,
            input_artifacts={k: v for k, v in (context_items or {}).items()},
        )

        # 4. Invoke step via adapter with closed-loop automated remediation
        retries = 0
        last_error = ""

        while retries <= step.retry_limit:
            # Active step execution context
            step_context = dict(context_items or {})

            if retries > 0:
                # Close the AI delegation loop: feed failure evidence directly into contract
                contract.input_artifacts["delegation_status"] = "remediation"
                contract.input_artifacts["last_failure_reason"] = last_error
                contract.input_artifacts["remediation_attempt"] = f"Attempt {retries + 1} of {step.retry_limit + 1}"
                contract.input_artifacts["remediation_guidance"] = (
                    f"Previous attempt failed verification: {last_error}. "
                    "Analyze failure output, identify root cause, and apply minimal fix within target scope."
                )
                step_context.update({
                    "last_failure_reason": last_error,
                    "remediation_attempt": str(retries + 1),
                })
                self.state_manager.update_step(
                    run_id,
                    step.id,
                    StepStatus.RUNNING,
                    retry_count=retries,
                    error_message=f"Remediating retry {retries}: {last_error[:120]}",
                )

            try:
                result = self.adapter.invoke_step(step, contract, step_context)

                # Record usage
                in_tok = result.token_usage.get("input_tokens", 400)
                out_tok = result.token_usage.get("output_tokens", 200)
                self.budget_manager.record_usage(in_tok, out_tok)

                # 5. On-disk verification if specified
                if step.verification_command:
                    exit_code, output = self.verifier.run_command(step.verification_command)
                    if exit_code != 0:
                        raise RuntimeError(
                            f"Verification failed with exit code {exit_code}: {output[:200]}"
                        )

                # Step Succeeded
                step_results[step.id] = result
                self.state_manager.update_step(
                    run_id,
                    step.id,
                    StepStatus.SUCCEEDED,
                    token_usage={"input_tokens": in_tok, "output_tokens": out_tok, "total_tokens": in_tok + out_tok},
                    retry_count=retries,
                )
                return

            except Exception as e:
                retries += 1
                last_error = str(e)
                if retries > step.retry_limit:
                    self.state_manager.update_step(
                        run_id,
                        step.id,
                        StepStatus.FAILED,
                        error_message=last_error,
                        retry_count=retries,
                    )
                    self._record_escalation(run_id, step, last_error, retries)
                    raise RuntimeError(
                        f"Delegation loop for step '{step.id}' failed after {retries} attempts: {last_error}"
                    )

    def _record_escalation(
        self,
        run_id: str,
        step: WorkflowStep,
        last_error: str,
        attempts: int,
    ) -> None:
        """Records an escalation notice when automated delegation retries are exhausted."""
        workspace_root = getattr(self.state_manager, "root", Path("."))
        escalation_dir = Path(workspace_root) / ".orchestra" / "escalations"
        try:
            escalation_dir.mkdir(parents=True, exist_ok=True)
            notice_file = escalation_dir / f"{run_id}_{step.id}_escalation.md"
            notice_content = f"""# ⚠️ DELEGATION ESCALATION NOTICE

- **Run ID**: `{run_id}`
- **Failed Step**: `{step.id}` ({step.name})
- **Agent Role**: `{step.agent_role}`
- **Attempts Exhausted**: {attempts}
- **Stop Reason**: Delegation loop automated remediation limit reached without passing verification.

## Failure Trace
```text
{last_error}
```

## Recommended Human Diligence Actions
1. Review target files: `{', '.join(step.target_files) if step.target_files else 'None'}`.
2. Check verification command: `{step.verification_command or 'None'}`.
3. If this requires architectural changes or new dependencies, escalate tier to **Complex** or **Architectural** and create an ADR in `DECISIONS.md`.
"""
            notice_file.write_text(notice_content, encoding="utf-8")
        except Exception:
            pass

    def _evaluate_final_acceptance(
        self,
        run_id: str,
        step_results: Dict[str, StructuredResult],
    ) -> None:
        if not self.workflow.acceptance_criteria:
            return

        evidence_combined = "\n".join(
            r.verification_evidence for r in step_results.values() if r.verification_evidence
        )
        passed, failures = self.verifier.evaluate_acceptance(
            criteria=self.workflow.acceptance_criteria,
            verification_evidence=evidence_combined,
            test_exit_code=0,
        )
        if not passed:
            raise RuntimeError(f"Acceptance criteria not met: {failures}")
