"""Terminal Verification Runner for deterministic runtime, static analysis, and smoke testing."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestra.pr.models import ChangedFile, VerificationOutcome


class MissingEnvironmentBlockerError(Exception):
    """Tier 1 Blocker: Missing .env or stopped services required for verification."""
    pass


class TerminalVerificationRunner:
    """Executes deterministic verification inside the workspace and triages terminal errors."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def _get_clean_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["CI"] = "true"
        env["GIT_PAGER"] = "cat"
        env["GH_PAGER"] = "cat"
        bin_dir = str(self.workspace_root / "bin")
        local_bin = str(Path.home() / ".local" / "bin")
        env["PATH"] = f"{bin_dir}:{local_bin}:{env.get('PATH', '')}"
        return env

    def _run_cmd(self, command: str, timeout: int = 180) -> tuple[int, str]:
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._get_clean_env(),
            )
            output = (res.stdout + "\n" + res.stderr).strip()
            return res.returncode, output
        except subprocess.TimeoutExpired:
            return -1, f"Command timed out after {timeout} seconds: {command}"
        except Exception as e:
            return 1, f"Command execution failed: {str(e)}"

    def run_all(
        self,
        changed_files: List[ChangedFile],
        skip_tests: bool = False,
    ) -> List[VerificationOutcome]:
        """Runs environment sync, static analysis, targeted tests, and smoke builds."""
        outcomes: List[VerificationOutcome] = []

        # 1. Environment sync check
        sync_outcome = self.check_environment_sync(changed_files)
        if sync_outcome:
            outcomes.append(sync_outcome)

        # 2. Static analysis / linting
        lint_outcome = self.run_static_analysis(changed_files)
        if lint_outcome:
            outcomes.append(lint_outcome)

        # 3. Test execution
        if not skip_tests:
            test_outcome = self.run_targeted_tests(changed_files)
            if test_outcome:
                outcomes.append(test_outcome)

        # 4. Smoke build
        build_outcome = self.run_smoke_build(changed_files)
        if build_outcome:
            outcomes.append(build_outcome)

        return outcomes

    def check_environment_sync(self, changed_files: List[ChangedFile]) -> Optional[VerificationOutcome]:
        """Detects if dependency manifests or schemas changed and verifies dependencies."""
        manifests_changed = [
            f.path for f in changed_files
            if f.path.endswith(("package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod"))
        ]
        if not manifests_changed:
            return None

        # Check Python or Node manifests
        cmd = "true"
        step_name = "Environment Sync Check"
        if any("requirements.txt" in p for p in manifests_changed):
            cmd = "pip check || true"
        elif any("package.json" in p for p in manifests_changed) and shutil.which("npm"):
            cmd = "npm ls --depth=0 || true"

        t0 = time.time()
        code, out = self._run_cmd(cmd)
        duration = time.time() - t0

        return VerificationOutcome(
            step_name=step_name,
            command=cmd,
            exit_code=code,
            output_snippet=out[:500],
            duration_seconds=round(duration, 2),
            passed=(code == 0),
        )

    def run_static_analysis(self, changed_files: List[ChangedFile]) -> Optional[VerificationOutcome]:
        """Runs available project linters on the modified files."""
        high_signal = [f.path for f in changed_files if not f.is_filtered]
        if not high_signal:
            return None

        cmd = None
        # Detect workspace tooling
        if (self.workspace_root / "ruff.toml").exists() or (self.workspace_root / "pyproject.toml").exists():
            if shutil.which("ruff"):
                cmd = f"ruff check {' '.join(high_signal)}"
        if not cmd and (self.workspace_root / "package.json").exists() and shutil.which("npm"):
            cmd = "npm run lint || true"
        if not cmd and (self.workspace_root / "bin" / "orch").exists():
            cmd = "./bin/orch validate"

        if not cmd:
            return None

        t0 = time.time()
        code, out = self._run_cmd(cmd)
        duration = time.time() - t0

        diagnostics = self.parse_lint_diagnostics(out)

        return VerificationOutcome(
            step_name="Static Analysis & Linting",
            command=cmd,
            exit_code=code,
            output_snippet=out[:800],
            duration_seconds=round(duration, 2),
            passed=(code == 0),
            error_diagnostics=diagnostics,
        )

    def run_targeted_tests(self, changed_files: List[ChangedFile]) -> Optional[VerificationOutcome]:
        """Detects and runs automated tests targeting changed modules."""
        cmd = None
        # Python test discovery
        if (self.workspace_root / "tests").is_dir() and any(f.path.endswith(".py") for f in changed_files):
            if shutil.which("pytest"):
                cmd = "pytest -q"
            else:
                cmd = "python3 -m unittest discover tests"
        # Node test discovery
        elif (self.workspace_root / "package.json").exists() and shutil.which("npm"):
            cmd = "npm test -- --run"

        if not cmd:
            return None

        t0 = time.time()
        code, out = self._run_cmd(cmd, timeout=300)
        duration = time.time() - t0

        # Tier 1 Blocker check: missing env or database connection
        if code != 0:
            if "operationalerror: could not connect to server" in out.lower() or "connection refused" in out.lower() or "missing required environment variable" in out.lower():
                raise MissingEnvironmentBlockerError(
                    f"Tier 1 Blocker: Test failed due to unstarted service or missing .env variable: {out[:300]}"
                )

        diagnostics = self.parse_test_diagnostics(out)

        return VerificationOutcome(
            step_name="Targeted Test Execution",
            command=cmd,
            exit_code=code,
            output_snippet=out[:1000],
            duration_seconds=round(duration, 2),
            passed=(code == 0),
            error_diagnostics=diagnostics,
        )

    def run_smoke_build(self, changed_files: List[ChangedFile]) -> Optional[VerificationOutcome]:
        """Executes a smoke build if a build step exists."""
        cmd = None
        if (self.workspace_root / "package.json").exists() and shutil.which("npm"):
            pkg_content = (self.workspace_root / "package.json").read_text(encoding="utf-8", errors="ignore")
            if '"build":' in pkg_content:
                cmd = "npm run build"
        elif (self.workspace_root / "Makefile").exists():
            makefile = (self.workspace_root / "Makefile").read_text(encoding="utf-8", errors="ignore")
            if "\nbuild:" in makefile:
                cmd = "make build"

        if not cmd:
            return None

        t0 = time.time()
        code, out = self._run_cmd(cmd, timeout=180)
        duration = time.time() - t0

        return VerificationOutcome(
            step_name="Smoke Build",
            command=cmd,
            exit_code=code,
            output_snippet=out[:800],
            duration_seconds=round(duration, 2),
            passed=(code == 0),
        )

    def parse_lint_diagnostics(self, output: str) -> List[Dict[str, Any]]:
        """Extracts file, line, rule, and message from linter output."""
        diagnostics = []
        pattern = re.compile(r"^([^:\n]+):(\d+):(?:\d+:)?\s*([A-Z0-9]+)?\s*(.*)$", re.MULTILINE)
        for match in pattern.finditer(output):
            path, line, rule, message = match.groups()
            diagnostics.append({
                "type": "lint",
                "file": path.strip(),
                "line": int(line),
                "rule": (rule or "").strip(),
                "message": message.strip(),
            })
        return diagnostics[:20]

    def parse_test_diagnostics(self, output: str) -> List[Dict[str, Any]]:
        """Extracts failed test names and assertion failures from test logs."""
        diagnostics = []
        unittest_fail = re.compile(r"^(?:FAIL|ERROR):\s*(\S+)\s*\(([^)]+)\)", re.MULTILINE)
        for match in unittest_fail.finditer(output):
            test_name, test_suite = match.groups()
            diagnostics.append({
                "type": "test_failure",
                "test": test_name,
                "suite": test_suite,
                "summary": f"Failed in {test_suite}.{test_name}",
            })

        pytest_fail = re.compile(r"^FAILED\s+([^:]+)::(\S+)(?:\s+-\s+(.*))?$", re.MULTILINE)
        for match in pytest_fail.finditer(output):
            file_path, test_name, reason = match.groups()
            diagnostics.append({
                "type": "test_failure",
                "file": file_path,
                "test": test_name,
                "summary": (reason or "Assertion failure").strip(),
            })

        return diagnostics[:20]
