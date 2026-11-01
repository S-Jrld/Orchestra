"""Unit tests for ConventionalCommentsFormatter."""

import unittest

from orchestra.pr.formatter import ConventionalCommentsFormatter
from orchestra.pr.models import FindingCategory, FindingSeverity, ReviewFinding


class TestConventionalCommentsFormatter(unittest.TestCase):
    def test_format_individual_finding(self):
        finding = ReviewFinding(
            category=FindingCategory.BLOCKER,
            severity=FindingSeverity.CRITICAL,
            path="src/auth.py",
            start_line=10,
            end_line=12,
            principle_rationale="Hardcoded secret key in client initializer.",
            suggested_diff="api_key = os.getenv('API_KEY')",
        )
        formatted = ConventionalCommentsFormatter.format_finding(finding)
        self.assertIn("🔴 **[Blocker]**", formatted)
        self.assertIn("`src/auth.py#L10-L12`", formatted)
        self.assertIn("Critical (Blocks merge)", formatted)
        self.assertIn("```suggestion", formatted)
        self.assertIn("api_key = os.getenv('API_KEY')", formatted)

    def test_format_all_grouping_and_ordering(self):
        findings = [
            ReviewFinding(
                category=FindingCategory.NIT,
                severity=FindingSeverity.LOW,
                path="src/a.py",
                start_line=1,
                end_line=1,
                principle_rationale="Minor typo in docstring.",
            ),
            ReviewFinding(
                category=FindingCategory.BLOCKER,
                severity=FindingSeverity.CRITICAL,
                path="src/b.py",
                start_line=5,
                end_line=5,
                principle_rationale="Critical vulnerability.",
            ),
        ]
        formatted = ConventionalCommentsFormatter.format_all(findings)
        # Blockers must appear before Nits
        blocker_pos = formatted.find("### Blockers")
        nit_pos = formatted.find("### Nits")
        self.assertTrue(blocker_pos != -1)
        self.assertTrue(nit_pos != -1)
        self.assertLess(blocker_pos, nit_pos)


if __name__ == "__main__":
    unittest.main()
