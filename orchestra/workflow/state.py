"""Run state persistence, audit trail logging, and recovery manager."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from orchestra.models import RunRecord, RunStatus, StepRunRecord, StepStatus
from orchestra.workflow.analytics import RunAnalyticsDB


class RunStateManager:
    """Persists execution runs to disk and provides audit logs."""

    def __init__(self, workspace_root: Union[str, Path], enable_analytics: bool = True):
        self.root = Path(workspace_root).resolve()
        self.runs_dir = self.root / ".orchestra" / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.root / ".orchestra" / "audit.jsonl"
        self.analytics_db = RunAnalyticsDB(self.root / ".orchestra" / "analytics.db") if enable_analytics else None

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_run(
        self,
        run_id: str,
        workflow_id: str,
        tier: str,
        adapter_name: str,
        step_ids: List[Dict[str, str]],
        task_description: Optional[str] = None,
        selected_skills: Optional[List[str]] = None,
    ) -> RunRecord:
        step_records = [
            StepRunRecord(
                step_id=s["id"],
                name=s["name"],
                agent_role=s["agent_role"],
                status=StepStatus.PENDING,
            )
            for s in step_ids
        ]

        run = RunRecord(
            schema_version="1.0.0",
            run_id=run_id,
            workflow_id=workflow_id,
            tier=tier,
            status=RunStatus.RUNNING,
            adapter=adapter_name,
            created_at=self._now_iso(),
            step_records=step_records,
            task_description=task_description,
            selected_skills=selected_skills or [],
            total_token_usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            estimated_cost_usd=0.0,
        )
        self.save_run(run)
        self._append_audit("run_created", run_id, {"workflow_id": workflow_id, "tier": tier})
        return run

    def save_run(self, run: RunRecord) -> None:
        run_file = self.runs_dir / f"{run.run_id}.json"
        temp_file = self.runs_dir / f"{run.run_id}.tmp"

        data = asdict(run)
        # Convert enums to values
        data["status"] = run.status.value if isinstance(run.status, RunStatus) else run.status
        for s in data["step_records"]:
            if isinstance(s["status"], StepStatus):
                s["status"] = s["status"].value

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp_file.replace(run_file)

        if self.analytics_db:
            try:
                self.analytics_db.index_run(run)
            except Exception:
                pass

    def load_run(self, run_id: str) -> Optional[RunRecord]:
        run_file = self.runs_dir / f"{run_id}.json"
        if not run_file.is_file():
            return None

        with open(run_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        step_records = [
            StepRunRecord(
                step_id=s["step_id"],
                name=s["name"],
                agent_role=s["agent_role"],
                status=StepStatus(s["status"]),
                start_time=s.get("start_time"),
                end_time=s.get("end_time"),
                retry_count=s.get("retry_count", 0),
                token_usage=s.get("token_usage", {}),
                error_message=s.get("error_message"),
            )
            for s in data["step_records"]
        ]

        return RunRecord(
            schema_version=data["schema_version"],
            run_id=data["run_id"],
            workflow_id=data["workflow_id"],
            tier=data["tier"],
            status=RunStatus(data["status"]),
            adapter=data["adapter"],
            created_at=data["created_at"],
            step_records=step_records,
            task_description=data.get("task_description"),
            model=data.get("model"),
            selected_skills=data.get("selected_skills", []),
            completed_at=data.get("completed_at"),
            total_token_usage=data.get("total_token_usage", {}),
            estimated_cost_usd=data.get("estimated_cost_usd", 0.0),
        )

    def list_runs(self) -> List[Dict[str, Any]]:
        runs = []
        for rf in sorted(self.runs_dir.glob("*.json")):
            try:
                with open(rf, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    runs.append({
                        "run_id": d.get("run_id"),
                        "workflow_id": d.get("workflow_id"),
                        "tier": d.get("tier"),
                        "status": d.get("status"),
                        "created_at": d.get("created_at"),
                        "completed_at": d.get("completed_at"),
                    })
            except Exception:
                continue
        return runs

    def update_step(
        self,
        run_id: str,
        step_id: str,
        status: StepStatus,
        token_usage: Optional[Dict[str, int]] = None,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None,
    ) -> None:
        run = self.load_run(run_id)
        if not run:
            return

        updated_retry = 0
        for s in run.step_records:
            if s.step_id == step_id:
                s.status = status
                if status == StepStatus.RUNNING and not s.start_time:
                    s.start_time = self._now_iso()
                elif status in (StepStatus.SUCCEEDED, StepStatus.FAILED, StepStatus.CANCELLED):
                    s.end_time = self._now_iso()

                if token_usage:
                    s.token_usage = token_usage
                    run.total_token_usage["input_tokens"] += token_usage.get("input_tokens", 0)
                    run.total_token_usage["output_tokens"] += token_usage.get("output_tokens", 0)
                    run.total_token_usage["total_tokens"] += token_usage.get("total_tokens", 0)

                if error_message:
                    s.error_message = error_message
                if retry_count is not None:
                    s.retry_count = retry_count
                updated_retry = s.retry_count
                break

        self.save_run(run)
        self._append_audit(
            "step_updated",
            run_id,
            {"step_id": step_id, "status": status.value, "retry_count": updated_retry},
        )

    def complete_run(self, run_id: str, status: RunStatus) -> None:
        run = self.load_run(run_id)
        if not run:
            return
        run.status = status
        run.completed_at = self._now_iso()
        self.save_run(run)
        self._append_audit("run_completed", run_id, {"status": status.value})

    def _append_audit(self, event: str, run_id: str, details: Dict[str, Any]) -> None:
        record = {
            "timestamp": self._now_iso(),
            "event": event,
            "run_id": run_id,
            "details": details,
        }
        with open(self.audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
