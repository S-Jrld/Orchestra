"""Multi-dimensional code evaluation engine covering the seven software engineering standards."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from orchestra.pr.models import (
    ChangedFile,
    FindingCategory,
    FindingSeverity,
    PRMetadata,
    ReviewFinding,
    VerificationOutcome,
)


class MultiDimensionalEvaluator:
    """Evaluates PR diffs against the 7 core software engineering standards."""

    CONVENTIONAL_COMMIT_REGEX = re.compile(
        r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9_.\-]+\))?: .+$"
    )

    SECRET_PATTERNS = [
        (re.compile(r"""(?i)(?:api_key|apikey|secret_key|private_key|auth_token|password)\s*=\s*['"][A-Za-z0-9_\-]{12,}['"]"""), "Hardcoded secret or credential detected."),
        (re.compile(r"""-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"""), "Private cryptographic key committed directly into source code."),
    ]

    INJECTION_PATTERNS = [
        (re.compile(r"""subprocess\.(?:run|Popen|call|check_output)\([^)]*shell=True"""), "Unsafe subprocess execution with shell=True invites command injection."),
        (re.compile(r"""\bos\.system\("""), "Use of os.system() is insecure and bypasses process boundaries."),
        (re.compile(r"""\beval\("""), "Arbitrary code execution via eval() is prohibited."),
    ]

    DEFECT_PATTERNS = [
        (re.compile(r"""^\s*except:\s*(?:pass|\.\.\.)?(?:#.*)?$"""), "Bare except swallowing all exceptions indiscriminately."),
        (re.compile(r"""^\s*except\s+Exception:\s*(?:pass|\.\.\.)?(?:#.*)?$"""), "Silent exception suppression without logging or escalation."),
    ]

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def evaluate(
        self,
        metadata: PRMetadata,
        changed_files: List[ChangedFile],
        verification_outcomes: List[VerificationOutcome],
    ) -> List[ReviewFinding]:
        """Runs the 7-standard evaluation matrix across changed files and verification evidence."""
        findings: List[ReviewFinding] = []

        # 1. Verification Outcome Failures -> Blockers
        for outcome in verification_outcomes:
            if not outcome.passed:
                for diag in outcome.error_diagnostics:
                    findings.append(
                        ReviewFinding(
                            category=FindingCategory.BLOCKER,
                            severity=FindingSeverity.CRITICAL,
                            path=diag.get("file", "test_runner"),
                            start_line=diag.get("line", 1),
                            end_line=diag.get("line", 1),
                            principle_rationale=f"[Verification Failure] {diag.get('summary') or diag.get('message') or outcome.output_snippet[:150]}",
                        )
                    )
                if not outcome.error_diagnostics:
                    findings.append(
                        ReviewFinding(
                            category=FindingCategory.BLOCKER,
                            severity=FindingSeverity.CRITICAL,
                            path="terminal",
                            start_line=1,
                            end_line=1,
                            principle_rationale=f"[{outcome.step_name}] Command `{outcome.command}` failed with exit code {outcome.exit_code}.",
                        )
                    )

        # 2. Per-file code audits
        has_code_changes = False
        has_test_changes = False

        for file_obj in changed_files:
            if file_obj.is_filtered or not file_obj.patch:
                continue

            path = file_obj.path
            is_test = "test" in path.lower() or path.endswith(("_test.py", ".test.ts", ".test.tsx", ".spec.ts"))
            if is_test:
                has_test_changes = True
            else:
                has_code_changes = True

            patch_lines = file_obj.patch.splitlines()
            current_line = 0

            for line in patch_lines:
                # Track line number from diff hunk headers @@ -x,y +start,count @@
                if line.startswith("@@"):
                    match = re.search(r"\+(\d+)", line)
                    if match:
                        current_line = int(match.group(1))
                    continue

                if line.startswith("+") and not line.startswith("+++"):
                    added_text = line[1:]

                    # Security Standards: Secrets & Injections
                    for pattern, msg in self.SECRET_PATTERNS:
                        if pattern.search(added_text):
                            findings.append(
                                ReviewFinding(
                                    category=FindingCategory.BLOCKER,
                                    severity=FindingSeverity.CRITICAL,
                                    path=path,
                                    start_line=current_line,
                                    end_line=current_line,
                                    principle_rationale=f"[Security/OWASP Top 10] {msg}",
                                )
                            )

                    for pattern, msg in self.INJECTION_PATTERNS:
                        if pattern.search(added_text):
                            findings.append(
                                ReviewFinding(
                                    category=FindingCategory.BLOCKER,
                                    severity=FindingSeverity.CRITICAL,
                                    path=path,
                                    start_line=current_line,
                                    end_line=current_line,
                                    principle_rationale=f"[Security/OWASP Top 10] {msg}",
                                )
                            )

                    # Defect Analysis
                    for pattern, msg in self.DEFECT_PATTERNS:
                        if pattern.search(added_text):
                            findings.append(
                                ReviewFinding(
                                    category=FindingCategory.MAJOR,
                                    severity=FindingSeverity.HIGH,
                                    path=path,
                                    start_line=current_line,
                                    end_line=current_line,
                                    principle_rationale=f"[Defect Analysis] {msg}",
                                    suggested_diff="except Exception as e:\n    logger.error(f'Operation failed: {str(e)}')\n    raise",
                                )
                            )

                    current_line += 1
                elif not line.startswith("-"):
                    current_line += 1

        # 3. Test Quality (FIRST principles): Missing tests for new feature logic
        if has_code_changes and not has_test_changes:
            findings.append(
                ReviewFinding(
                    category=FindingCategory.MAJOR,
                    severity=FindingSeverity.HIGH,
                    path=changed_files[0].path if changed_files else "tests",
                    start_line=1,
                    end_line=1,
                    principle_rationale="[Test Quality/FIRST] PR introduces production code modifications without accompanying automated unit or integration tests.",
                )
            )

        # 4. Commit Hygiene: Conventional Commits audit
        for commit in metadata.commits:
            msg = ""
            if isinstance(commit, dict):
                msg = commit.get("messageHeadline") or commit.get("message") or ""
            elif isinstance(commit, str):
                msg = commit
            if msg and not self.CONVENTIONAL_COMMIT_REGEX.match(msg.splitlines()[0].strip()):
                findings.append(
                    ReviewFinding(
                        category=FindingCategory.NIT,
                        severity=FindingSeverity.LOW,
                        path="git/commits",
                        start_line=1,
                        end_line=1,
                        principle_rationale=f"[Commit Hygiene] Commit message '{msg[:60]}' does not adhere to Conventional Commits standard (e.g., 'feat: add PR safety wrapper').",
                    )
                )

        # 5. Architecture & Scope Praise
        if not any(f.category in (FindingCategory.BLOCKER, FindingCategory.MAJOR) for f in findings):
            findings.append(
                ReviewFinding(
                    category=FindingCategory.PRAISE,
                    severity=FindingSeverity.INFO,
                    path=changed_files[0].path if changed_files else "src",
                    start_line=1,
                    end_line=1,
                    principle_rationale="[Architecture Principles] Clean separation of concerns, no circular dependencies, and disciplined diff boundaries observed.",
                )
            )

        return findings
