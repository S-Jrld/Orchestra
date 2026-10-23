"""Regression tests verifying existing contracts, scripts, and token bounds."""

import subprocess
from pathlib import Path
import unittest


class TestRegression(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.parent.parent

    def test_validate_sh_passes(self):
        cmd = ["bash", "scripts/validate.sh"]
        res = subprocess.run(cmd, cwd=str(self.root), capture_output=True, text=True)
        self.assertEqual(
            res.returncode,
            0,
            f"scripts/validate.sh failed with exit code {res.returncode}:\n{res.stdout}\n{res.stderr}",
        )
        self.assertIn("ALL CHECKS PASSED", res.stdout)

    def test_constitution_bounds(self):
        agents_md = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        lines = len(agents_md.strip().split("\n"))
        self.assertLessEqual(lines, 90, f"AGENTS.md has {lines} lines, exceeding 90 line bound")

    def test_router_bounds(self):
        router_md = (self.root / "ORCHESTRATOR.md").read_text(encoding="utf-8")
        lines = len(router_md.strip().split("\n"))
        self.assertLessEqual(lines, 90, f"ORCHESTRATOR.md has {lines} lines, exceeding 90 line bound")

    def test_primary_agent_mode(self):
        orch_md = (self.root / "agents" / "orchestra.md").read_text(encoding="utf-8")
        self.assertIn("mode: primary", orch_md)

        for spec in ["advisor", "researcher", "reviewer", "tester"]:
            sub_md = (self.root / "agents" / f"{spec}.md").read_text(encoding="utf-8")
            self.assertIn("mode: subagent", sub_md)


if __name__ == "__main__":
    unittest.main()
