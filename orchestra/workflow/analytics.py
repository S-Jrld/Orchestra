"""SQLite query and analytics engine for historical and active workflow runs."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from orchestra.models import RunRecord, RunStatus, StepRunRecord, StepStatus


class RunAnalyticsDB:
    """Manages SQLite index of execution runs for fast search and aggregate analytics."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path or ".orchestra/analytics.db").resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initializes SQLite schema and indexes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_id TEXT,
                    tier TEXT,
                    status TEXT,
                    adapter TEXT,
                    created_at TEXT,
                    completed_at TEXT,
                    duration_seconds REAL DEFAULT 0.0,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    estimated_cost_usd REAL DEFAULT 0.0,
                    task_description TEXT,
                    model TEXT,
                    step_count INTEGER DEFAULT 0,
                    failed_step_count INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS step_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    step_id TEXT,
                    name TEXT,
                    agent_role TEXT,
                    status TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds REAL DEFAULT 0.0,
                    retry_count INTEGER DEFAULT 0,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    error_message TEXT,
                    FOREIGN KEY (run_id) REFERENCES runs (run_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_status ON runs (status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_tier ON runs (tier)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs (created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_step_runs_run_id ON step_runs (run_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_step_runs_role ON step_runs (agent_role)")
            conn.commit()

    def index_run(self, run: RunRecord) -> None:
        """Upserts a run record and its steps into the SQLite database."""
        status_str = run.status.value if isinstance(run.status, RunStatus) else str(run.status)

        # Calculate duration if possible
        duration = 0.0
        if run.created_at and run.completed_at:
            try:
                t0 = datetime.fromisoformat(run.created_at)
                t1 = datetime.fromisoformat(run.completed_at)
                duration = max(0.0, (t1 - t0).total_seconds())
            except Exception:
                pass

        step_count = len(run.step_records)
        failed_count = sum(
            1 for s in run.step_records
            if (s.status.value if isinstance(s.status, StepStatus) else str(s.status)) == "failed"
        )

        in_tok = run.total_token_usage.get("input_tokens", 0)
        out_tok = run.total_token_usage.get("output_tokens", 0)
        tot_tok = run.total_token_usage.get("total_tokens", in_tok + out_tok)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO runs (
                    run_id, workflow_id, tier, status, adapter,
                    created_at, completed_at, duration_seconds,
                    input_tokens, output_tokens, total_tokens,
                    estimated_cost_usd, task_description, model,
                    step_count, failed_step_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    workflow_id=excluded.workflow_id,
                    tier=excluded.tier,
                    status=excluded.status,
                    adapter=excluded.adapter,
                    completed_at=excluded.completed_at,
                    duration_seconds=excluded.duration_seconds,
                    input_tokens=excluded.input_tokens,
                    output_tokens=excluded.output_tokens,
                    total_tokens=excluded.total_tokens,
                    estimated_cost_usd=excluded.estimated_cost_usd,
                    task_description=excluded.task_description,
                    model=excluded.model,
                    step_count=excluded.step_count,
                    failed_step_count=excluded.failed_step_count
            """, (
                run.run_id, run.workflow_id, run.tier, status_str, run.adapter,
                run.created_at, run.completed_at, duration,
                in_tok, out_tok, tot_tok,
                run.estimated_cost_usd, run.task_description, run.model,
                step_count, failed_count
            ))

            # Delete old step runs for this run and re-insert
            cursor.execute("DELETE FROM step_runs WHERE run_id = ?", (run.run_id,))

            for s in run.step_records:
                s_stat = s.status.value if isinstance(s.status, StepStatus) else str(s.status)
                s_dur = 0.0
                if s.start_time and s.end_time:
                    try:
                        st0 = datetime.fromisoformat(s.start_time)
                        st1 = datetime.fromisoformat(s.end_time)
                        s_dur = max(0.0, (st1 - st0).total_seconds())
                    except Exception:
                        pass

                s_in = s.token_usage.get("input_tokens", 0)
                s_out = s.token_usage.get("output_tokens", 0)
                s_tot = s.token_usage.get("total_tokens", s_in + s_out)

                cursor.execute("""
                    INSERT INTO step_runs (
                        run_id, step_id, name, agent_role, status,
                        start_time, end_time, duration_seconds,
                        retry_count, input_tokens, output_tokens,
                        total_tokens, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run.run_id, s.step_id, s.name, s.agent_role, s_stat,
                    s.start_time, s.end_time, s_dur,
                    s.retry_count, s_in, s_out, s_tot, s.error_message
                ))

            conn.commit()

    def index_all_existing_runs(self, runs_dir: Path) -> int:
        """Scans on-disk JSON runs and indexes all of them into SQLite."""
        if not runs_dir.is_dir():
            return 0
        count = 0
        for rf in runs_dir.glob("*.json"):
            try:
                with open(rf, "r", encoding="utf-8") as f:
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
                run = RunRecord(
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
                self.index_run(run)
                count += 1
            except Exception:
                continue
        return count

    def query_runs(
        self,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        workflow_id: Optional[str] = None,
        adapter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Queries runs based on structured filter parameters."""
        query = "SELECT * FROM runs WHERE 1=1"
        params: List[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if tier:
            query += " AND tier = ?"
            params.append(tier)
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)
        if adapter:
            query += " AND adapter = ?"
            params.append(adapter)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculates aggregate metrics across all historical runs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END) as succeeded_runs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_runs,
                    SUM(total_tokens) as total_tokens,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(estimated_cost_usd) as total_cost_usd,
                    AVG(duration_seconds) as avg_duration_seconds
                FROM runs
            """)
            summary_row = cursor.fetchone()

            # Breakdown by tier
            cursor.execute("""
                SELECT tier, COUNT(*) as count, AVG(total_tokens) as avg_tokens
                FROM runs GROUP BY tier
            """)
            tier_rows = cursor.fetchall()
            tiers = {row["tier"]: {"count": row["count"], "avg_tokens": round(row["avg_tokens"] or 0, 1)} for row in tier_rows}

            # Failure rate by agent role
            cursor.execute("""
                SELECT agent_role, COUNT(*) as step_count,
                       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
                FROM step_runs GROUP BY agent_role
            """)
            role_rows = cursor.fetchall()
            roles = {
                row["agent_role"]: {
                    "total_steps": row["step_count"],
                    "failed_steps": row["failed_count"],
                }
                for row in role_rows
            }

            tot = summary_row["total_runs"] or 0
            succ = summary_row["succeeded_runs"] or 0
            rate = round((succ / tot * 100.0), 1) if tot > 0 else 0.0

            return {
                "total_runs": tot,
                "succeeded_runs": succ,
                "failed_runs": summary_row["failed_runs"] or 0,
                "cancelled_runs": summary_row["cancelled_runs"] or 0,
                "success_rate_percent": rate,
                "total_tokens_consumed": summary_row["total_tokens"] or 0,
                "total_cost_usd": round(summary_row["total_cost_usd"] or 0.0, 4),
                "avg_duration_seconds": round(summary_row["avg_duration_seconds"] or 0.0, 2),
                "tiers": tiers,
                "agent_roles": roles,
            }

    def get_delegation_metrics(self) -> Dict[str, Any]:
        """Calculates detailed metrics on the AI delegation loop across all steps."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_steps,
                    SUM(CASE WHEN status = 'succeeded' AND retry_count = 0 THEN 1 ELSE 0 END) as first_pass_success,
                    SUM(CASE WHEN status = 'succeeded' AND retry_count > 0 THEN 1 ELSE 0 END) as remediated_success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_steps,
                    SUM(retry_count) as total_retries
                FROM step_runs
            """)
            row = cursor.fetchone()

            total = row["total_steps"] or 0
            first_pass = row["first_pass_success"] or 0
            remediated = row["remediated_success"] or 0
            failed = row["failed_steps"] or 0
            retries = row["total_retries"] or 0

            remediated_attempts = remediated + failed
            remediation_efficiency = (
                round((remediated / remediated_attempts * 100.0), 1)
                if remediated_attempts > 0
                else 100.0
            )

            # Role-level breakdown
            cursor.execute("""
                SELECT 
                    agent_role,
                    COUNT(*) as total_steps,
                    SUM(CASE WHEN status = 'succeeded' AND retry_count = 0 THEN 1 ELSE 0 END) as first_pass,
                    SUM(CASE WHEN status = 'succeeded' AND retry_count > 0 THEN 1 ELSE 0 END) as remediated,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(retry_count) as retries
                FROM step_runs
                GROUP BY agent_role
            """)
            role_breakdown = {}
            for r in cursor.fetchall():
                role_breakdown[r["agent_role"]] = {
                    "total_steps": r["total_steps"],
                    "first_pass": r["first_pass"],
                    "remediated": r["remediated"],
                    "failed": r["failed"],
                    "total_retries": r["retries"],
                }

            return {
                "total_dispatched_steps": total,
                "first_pass_success": first_pass,
                "remediated_success": remediated,
                "failed_steps": failed,
                "total_retries": retries,
                "first_pass_rate_percent": round((first_pass / total * 100.0), 1) if total > 0 else 0.0,
                "remediation_efficiency_percent": remediation_efficiency,
                "roles": role_breakdown,
            }

    def suggest_rule_improvements(self, min_occurrences: int = 1) -> List[Dict[str, str]]:
        """Analyzes historical step failures and retries to synthesize actionable rule/protocol refinements."""
        suggestions = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT agent_role, COUNT(*) as failed_count, GROUP_CONCAT(error_message, ' ||| ') as error_traces
                FROM step_runs
                WHERE (status = 'failed' OR retry_count > 0) AND error_message IS NOT NULL AND error_message != ''
                GROUP BY agent_role
                HAVING COUNT(*) >= ?
            """, (min_occurrences,))

            for row in cursor.fetchall():
                role = row["agent_role"]
                failed_count = row["failed_count"]
                traces = row["error_traces"] or ""

                if "verification" in traces.lower() or "exit code" in traces.lower():
                    suggestions.append({
                        "role": role,
                        "category": "Verification Failure",
                        "impact": f"{failed_count} step(s) failed on-disk verification",
                        "recommendation": (
                            f"Update 'protocols/ENGINEERING_STANDARDS.md': Add explicit pre-verification checklist "
                            f"or mock fixtures for @{role} before invoking test suites."
                        ),
                    })
                elif "security" in traces.lower() or "access denied" in traces.lower() or "boundary" in traces.lower():
                    suggestions.append({
                        "role": role,
                        "category": "Security Boundary Violation",
                        "impact": f"{failed_count} step(s) tripped path sandbox restrictions",
                        "recommendation": (
                            f"Review 'protocols/SUBAGENT_DISPATCH.md': Ensure Orchestrator populates allowed_paths "
                            f"in TaskContract scope to encompass all needed directories for @{role}."
                        ),
                    })
                elif "timeout" in traces.lower():
                    suggestions.append({
                        "role": role,
                        "category": "Step Timeout",
                        "impact": f"{failed_count} step(s) timed out",
                        "recommendation": (
                            f"Decompose @{role} tasks into smaller atomic steps in workflow definitions "
                            f"or raise step.timeout_seconds."
                        ),
                    })
                else:
                    suggestions.append({
                        "role": role,
                        "category": "Execution Failure",
                        "impact": f"{failed_count} step(s) failed with runtime errors",
                        "recommendation": (
                            f"Review recent error traces for @{role}. If recurring, codify guardrails or "
                            f"negative constraints into 'agents/{role}.md' or relevant skill leaf."
                        ),
                    })

        return suggestions
