"""Review synthesis, deterministic verdict calculation, and publishing gate."""

from __future__ import annotations

import datetime
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from orchestra.pr.formatter import ConventionalCommentsFormatter
from orchestra.pr.models import (
    FindingCategory,
    PRMetadata,
    PRReviewReport,
    ReviewFinding,
    ReviewVerdict,
    VerificationOutcome,
)


class ReviewSynthesizer:
    """Compiles markdown review reports, computes verdicts, and handles human-in-the-loop publishing."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def determine_verdict(
        self,
        verification_outcomes: List[VerificationOutcome],
        findings: List[ReviewFinding],
    ) -> ReviewVerdict:
        """Computes a deterministic review verdict based on verification and findings severity."""
        # 1. Any failed verification check blocks merge
        if any(not outcome.passed for outcome in verification_outcomes):
            return ReviewVerdict.REQUEST_CHANGES

        # 2. Any Blocker or Major finding blocks merge
        has_blocker = any(f.category == FindingCategory.BLOCKER for f in findings)
        has_major = any(f.category == FindingCategory.MAJOR for f in findings)
        if has_blocker or has_major:
            return ReviewVerdict.REQUEST_CHANGES

        # 3. If there are Minor or Nit findings, comment with suggestions
        has_minor_or_nit = any(f.category in (FindingCategory.MINOR, FindingCategory.NIT) for f in findings)
        if has_minor_or_nit:
            return ReviewVerdict.COMMENT

        # 4. Clean pass
        return ReviewVerdict.APPROVE

    def build_report(
        self,
        metadata: PRMetadata,
        verification_outcomes: List[VerificationOutcome],
        findings: List[ReviewFinding],
        impacted_dependencies: Optional[Dict[str, List[str]]] = None,
    ) -> PRReviewReport:
        """Synthesizes the complete PRReviewReport dataclass."""
        verdict = self.determine_verdict(verification_outcomes, findings)
        created_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Draft executive summary
        summary_parts = [
            f"Review for PR #{metadata.number} ('{metadata.title}') by @{metadata.author}.",
            f"Evaluated branch `{metadata.head_ref}` against target `{metadata.base_ref}`.",
            f"Deterministic Verdict: **{verdict.value}**.",
        ]
        if verdict == ReviewVerdict.APPROVE:
            summary_parts.append("All automated verification checks passed and code meets architectural standards.")
        elif verdict == ReviewVerdict.REQUEST_CHANGES:
            summary_parts.append("Changes are required before merging due to failing tests or critical/major findings.")
        else:
            summary_parts.append("Verification checks passed. Non-blocking suggestions and polish items identified.")

        return PRReviewReport(
            pr_number=metadata.number,
            pr_title=metadata.title,
            author=metadata.author,
            base_ref=metadata.base_ref,
            head_ref=metadata.head_ref,
            verdict=verdict,
            executive_summary=" ".join(summary_parts),
            verification_outcomes=verification_outcomes,
            findings=findings,
            impacted_dependencies=impacted_dependencies or {},
            created_at=created_at,
        )

    def render_markdown(self, report: PRReviewReport) -> str:
        """Renders the review report to formatted GitHub Markdown."""
        verdict_badge = {
            ReviewVerdict.APPROVE: "✅ **APPROVE**",
            ReviewVerdict.REQUEST_CHANGES: "❌ **REQUEST CHANGES**",
            ReviewVerdict.COMMENT: "💬 **COMMENT**",
        }.get(report.verdict, report.verdict.value)

        lines = [
            f"# Pull Request Review: #{report.pr_number} — {report.pr_title}",
            "",
            f"- **Author**: @{report.author}",
            f"- **Branch**: `{report.head_ref}` $\\to$ `{report.base_ref}`",
            f"- **Generated At**: {report.created_at}",
            f"- **Recommendation**: {verdict_badge}",
            "",
            "## 1. Executive Summary",
            report.executive_summary,
            "",
            "## 2. Terminal Verification Scorecard",
            "| Step | Command | Exit Code | Duration | Status |",
            "|---|---|---|---|---|",
        ]

        if not report.verification_outcomes:
            lines.append("| None | N/A | 0 | 0.0s | SKIPPED |")
        else:
            for v in report.verification_outcomes:
                status_icon = "✅ PASSED" if v.passed else "❌ FAILED"
                lines.append(f"| {v.step_name} | `{v.command}` | {v.exit_code} | {v.duration_seconds}s | {status_icon} |")

        if report.impacted_dependencies:
            lines.extend([
                "",
                "## 3. Impacted Workspace Dependencies",
                "| Modified File | Upstream Importers |",
                "|---|---|",
            ])
            for changed, importers in report.impacted_dependencies.items():
                imp_str = ", ".join(f"`{i}`" for i in importers) if importers else "_No internal callers detected_"
                lines.append(f"| `{changed}` | {imp_str} |")

        lines.extend([
            "",
            "## 4. Multi-Dimensional Review Findings",
            ConventionalCommentsFormatter.format_all(report.findings),
        ])

        return "\n".join(lines)

    def save_report(self, report: PRReviewReport, output_dir: Optional[Path] = None) -> Path:
        """Saves the markdown review to disk."""
        target_dir = (output_dir or (self.workspace_root / ".orchestra" / "reviews")).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"PR-{report.pr_number}-review.md"
        content = self.render_markdown(report)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def publish_review(self, report: PRReviewReport, dry_run: bool = False) -> bool:
        """Human-in-the-loop publishing gate executing `gh pr review`."""
        if dry_run:
            return False

        body = self.render_markdown(report)
        flag = {
            ReviewVerdict.APPROVE: "--approve",
            ReviewVerdict.REQUEST_CHANGES: "--request-changes",
            ReviewVerdict.COMMENT: "--comment",
        }.get(report.verdict, "--comment")

        cmd = ["gh", "pr", "review", str(report.pr_number), flag, "--body", body]
        try:
            res = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False
