"""Conventional Comments Formatter with location anchoring and GitHub suggested diffs."""

from __future__ import annotations

from typing import List

from orchestra.pr.models import FindingCategory, ReviewFinding


class ConventionalCommentsFormatter:
    """Formats findings into industry-standard Conventional Comments."""

    CATEGORY_BADGES = {
        FindingCategory.BLOCKER: "🔴 **[Blocker]**",
        FindingCategory.MAJOR: "🟠 **[Major]**",
        FindingCategory.MINOR: "🟡 **[Minor]**",
        FindingCategory.NIT: "⚪ **[Nit]**",
        FindingCategory.PRAISE: "🟢 **[Praise]**",
    }

    @classmethod
    def format_finding(cls, finding: ReviewFinding) -> str:
        """Formats an individual finding into a structured markdown block."""
        badge = cls.CATEGORY_BADGES.get(finding.category, f"**[{finding.category.value}]**")
        loc = f"`{finding.path}#L{finding.start_line}`" if finding.start_line == finding.end_line else f"`{finding.path}#L{finding.start_line}-L{finding.end_line}`"

        lines = [
            f"{badge} {finding.principle_rationale}",
            f"- **Location**: {loc}",
            f"- **Severity**: {finding.severity.value} ({finding.merge_impact})",
        ]

        if finding.suggested_diff:
            lines.append("```suggestion")
            lines.append(finding.suggested_diff)
            lines.append("```")

        return "\n".join(lines)

    @classmethod
    def format_all(cls, findings: List[ReviewFinding]) -> str:
        """Formats a list of findings grouped by category priority."""
        if not findings:
            return "No issues or findings recorded."

        order = [
            FindingCategory.BLOCKER,
            FindingCategory.MAJOR,
            FindingCategory.MINOR,
            FindingCategory.NIT,
            FindingCategory.PRAISE,
        ]

        grouped = {cat: [f for f in findings if f.category == cat] for cat in order}
        output_sections = []

        for cat in order:
            cat_findings = grouped[cat]
            if not cat_findings:
                continue
            header = f"### {cat.value}s ({len(cat_findings)})"
            items = "\n\n".join(cls.format_finding(f) for f in cat_findings)
            output_sections.append(f"{header}\n\n{items}")

        return "\n\n---\n\n".join(output_sections)
