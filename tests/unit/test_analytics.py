"""Unit tests for SQLite Run Analytics Engine."""

import tempfile
from pathlib import Path
import unittest

from orchestra.models import RunRecord, RunStatus, StepRunRecord, StepStatus
from orchestra.workflow.analytics import RunAnalyticsDB


class TestRunAnalytics(unittest.TestCase):
    def test_analytics_indexing_and_query(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test_analytics.db"
            analytics = RunAnalyticsDB(db_path)

            step1 = StepRunRecord(
                step_id="step_a",
                name="Step A",
                agent_role="researcher",
                status=StepStatus.SUCCEEDED,
                start_time="2026-10-23T10:00:00+00:00",
                end_time="2026-10-23T10:00:05+00:00",
                token_usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            )
            step2 = StepRunRecord(
                step_id="step_b",
                name="Step B",
                agent_role="tester",
                status=StepStatus.SUCCEEDED,
                start_time="2026-10-23T10:00:05+00:00",
                end_time="2026-10-23T10:00:10+00:00",
                token_usage={"input_tokens": 200, "output_tokens": 100, "total_tokens": 300},
            )

            run = RunRecord(
                schema_version="1.0.0",
                run_id="run_analytics_001",
                workflow_id="wf_analytics",
                tier="Normal",
                status=RunStatus.SUCCEEDED,
                adapter="mock",
                created_at="2026-10-23T10:00:00+00:00",
                completed_at="2026-10-23T10:00:10+00:00",
                step_records=[step1, step2],
                task_description="Test analytics indexing",
                total_token_usage={"input_tokens": 300, "output_tokens": 150, "total_tokens": 450},
                estimated_cost_usd=0.0045,
            )

            # Index run
            analytics.index_run(run)

            # Query run
            rows = analytics.query_runs(status="succeeded")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["run_id"], "run_analytics_001")
            self.assertEqual(rows[0]["total_tokens"], 450)
            self.assertEqual(rows[0]["duration_seconds"], 10.0)

            # Filter by non-matching status
            self.assertEqual(len(analytics.query_runs(status="failed")), 0)

            # Summary stats
            stats = analytics.get_summary_stats()
            self.assertEqual(stats["total_runs"], 1)
            self.assertEqual(stats["succeeded_runs"], 1)
            self.assertEqual(stats["success_rate_percent"], 100.0)
            self.assertEqual(stats["total_tokens_consumed"], 450)
            self.assertIn("Normal", stats["tiers"])
            self.assertIn("researcher", stats["agent_roles"])
            self.assertIn("tester", stats["agent_roles"])

    def test_reindex_existing_runs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            runs_dir = Path(tmp_dir) / "runs"
            runs_dir.mkdir()
            db_path = Path(tmp_dir) / "analytics.db"
            analytics = RunAnalyticsDB(db_path)

            # Write a mock run JSON
            sample_data = {
                "schema_version": "1.0.0",
                "run_id": "run_reindex_test",
                "workflow_id": "wf_reindex",
                "tier": "Tiny",
                "status": "succeeded",
                "adapter": "mock",
                "created_at": "2026-10-23T12:00:00+00:00",
                "completed_at": "2026-10-23T12:00:02+00:00",
                "step_records": [
                    {
                        "step_id": "s1",
                        "name": "Step 1",
                        "agent_role": "orchestra",
                        "status": "succeeded",
                        "token_usage": {"input_tokens": 50, "output_tokens": 20, "total_tokens": 70},
                    }
                ],
                "total_token_usage": {"input_tokens": 50, "output_tokens": 20, "total_tokens": 70},
            }
            import json
            (runs_dir / "run_reindex_test.json").write_text(json.dumps(sample_data))

            count = analytics.index_all_existing_runs(runs_dir)
            self.assertEqual(count, 1)

            results = analytics.query_runs(tier="Tiny")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["run_id"], "run_reindex_test")


if __name__ == "__main__":
    unittest.main()
