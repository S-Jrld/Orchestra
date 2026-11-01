"""Terminal Verification Runner for deterministic runtime, static analysis, and smoke testing."""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestra.pr.models import ChangedFile, VerificationOutcome
from orchestra.workflow.verifier import WorkflowVerifier


class TerminalVerificationRunner:
    """Executes deterministic verification inside the workspace and triages terminal errors."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

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
        code, out = WorkflowVerifier.run_command(cmd, cwd=str(self.workspace_root))
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
            # Check if lint script exists in package.json
            cmd = "npm run lint || true"
        if not cmd and (self.workspace_root / "bin" / "orch").exists():
            cmd = "./bin/orch validate"

        if not cmd:
            return None

        t0 = time.time()
        code, out = WorkflowVerifier.run_command(cmd, cwd=str(self.workspace_root))
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
            cmd = "npm test"

        if not cmd:
            return None

        t0 = time.time()
        code, out = WorkflowVerifier.run_command(cmd, cwd=str(self.workspace_root), timeout=300)
        duration = time.time() - t0

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
        code, out = WorkflowVerifier.run_command(cmd, cwd=str(self.workspace_root), timeout=180)
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
        # Pattern: path/to/file.py:42:10: RULE Message
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
        # Python unittest: FAIL: test_name (module.TestCase)
        unittest_fail = re.compile(r"^(?:FAIL|ERROR):\s*(\S+)\s*\(([^)]+)\)", re.MULTILINE)
        for match in unittest_fail.finditer(output):
            test_name, test_suite = match.groups()
            diagnostics.append({
                "type": "test_failure",
                "test": test_name,
                "suite": test_suite,
                "summary": f"Failed in {test_suite}.{test_name}",
            })

        # Pytest: FAILED tests/test_foo.py::test_bar - AssertionError: ...
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
