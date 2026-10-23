"""Unit tests for Orchestra CLI."""

import io
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

from orchestra.cli import OrchestraCLI


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.parent.parent
        self.cli = OrchestraCLI(self.root)

    def test_cli_version(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = self.cli.run(["version"])
            self.assertEqual(code, 0)
            self.assertIn("Orchestra v", fake_out.getvalue())

    def test_cli_version_json(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = self.cli.run(["version", "--json"])
            self.assertEqual(code, 0)
            self.assertIn('"orchestra_version"', fake_out.getvalue())

    def test_cli_doctor(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = self.cli.run(["doctor"])
            self.assertEqual(code, 0)
            self.assertIn("Health Check", fake_out.getvalue())

    def test_cli_skills_list(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = self.cli.run(["skills", "list"])
            self.assertEqual(code, 0)
            self.assertIn("superpowers", fake_out.getvalue())

    def test_cli_route_explain(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = self.cli.run(["route", "--task", "Implement user login endpoint", "--explain"])
            self.assertEqual(code, 0)
            self.assertIn("Routing Explanation", fake_out.getvalue())

    def test_cli_run_cancel(self):
        run = self.cli.state_manager.create_run(
            run_id="run_test_cancel_001",
            workflow_id="wf_cancel",
            tier="Tiny",
            adapter_name="mock",
            step_ids=[{"id": "s1", "name": "Step 1", "agent_role": "tester"}],
        )
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = self.cli.run(["run", "cancel", "run_test_cancel_001"])
            self.assertEqual(code, 0)
            self.assertIn("has been cancelled", fake_out.getvalue())

        loaded = self.cli.state_manager.load_run("run_test_cancel_001")
        self.assertIsNotNone(loaded)
        from orchestra.models import RunStatus
        self.assertEqual(loaded.status, RunStatus.CANCELLED)

    def test_cli_workspace_root_fallback(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Change directory to empty temp dir
            import os
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                cli = OrchestraCLI()
                self.assertEqual(cli.workspace_root, self.root)
            finally:
                os.chdir(orig_cwd)


if __name__ == "__main__":
    unittest.main()
