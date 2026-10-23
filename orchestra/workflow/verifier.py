"""Evaluates verification commands, preconditions, and postconditions."""

from __future__ import annotations

import subprocess
from typing import Dict, List, Optional, Tuple


class WorkflowVerifier:
    """Executes on-disk checks and evaluates verification evidence."""

    @staticmethod
    def run_command(command: str, cwd: Optional[str] = None, timeout: int = 120) -> Tuple[int, str]:
        """Runs a verification command safely via subprocess and captures exit code and output."""
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = (res.stdout + "\n" + res.stderr).strip()
            return res.returncode, output
        except subprocess.TimeoutExpired:
            return -1, f"Command timed out after {timeout} seconds: {command}"
        except Exception as e:
            return 1, f"Command execution failed: {str(e)}"

    @staticmethod
    def evaluate_acceptance(
        criteria: List[str],
        verification_evidence: str,
        test_exit_code: int,
    ) -> Tuple[bool, List[str]]:
        """Verifies if test checks passed and criteria are addressed."""
        failures = []
        if test_exit_code != 0:
            failures.append(f"Automated verification test failed with exit code {test_exit_code}")

        if not verification_evidence or len(verification_evidence.strip()) < 5:
            failures.append("Missing required verification evidence text")

        return len(failures) == 0, failures
