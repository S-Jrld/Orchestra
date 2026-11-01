"""Unit tests for ReviewSynthesizer and deterministic verdict calculations."""

import tempfile
import unittest
from pathlib import Path

from orchestra.pr.models import (
    FindingCategory,
    FindingSeverity,
    PRMetadata,
    ReviewFinding,
    ReviewVerdict,
    VerificationOutcome,
)
from orchestra.pr.synthesizer import ReviewSynthesizer


class TestReviewSynthesizer(unittest.TestCase):
    def setUp(self):
        self.synthesizer = ReviewSynthesizer()

    def test_verdict_approve_clean_tests_and_findings(self):
        outcomes = [
            VerificationOutcome(
                step_name="Tests",
                command="pytest",
                exit_code=0,
                output_snippet="Passed",
                passed=True,
            )
        ]
        findings = [
            ReviewFinding(
                category=FindingCategory.PRAISE,
                severity=FindingSeverity.INFO,
                path="src/a.py",
                start_line=1,
                end_line=1,
                principle_rationale="Clean implementation.",
            )
        ]
        verdict = self.synthesizer.determine_verdict(outcomes, findings)
        self.assertEqual(verdict, ReviewVerdict.APPROVE)

    def test_verdict_request_changes_on_blocker(self):
        outcomes = [
            VerificationOutcome(
                step_name="Tests",
                command="pytest",
                exit_code=0,
                output_snippet="Passed",
                passed=True,
            )
        ]
        findings = [
            ReviewFinding(
                category=FindingCategory.BLOCKER,
                severity=FindingSeverity.CRITICAL,
                path="src/a.py",
                start_line=1,
                end_line=1,
                principle_rationale="Command injection.",
            )
        ]
        verdict = self.synthesizer.determine_verdict(outcomes, findings)
        self.assertEqual(verdict, ReviewVerdict.REQUEST_CHANGES)

    def test_verdict_request_changes_on_test_failure(self):
        outcomes = [
            VerificationOutcome(
                step_name="Tests",
                command="pytest",
                exit_code=1,
                output_snippet="1 failed",
                passed=False,
            )
        ]
        verdict = self.synthesizer.determine_verdict(outcomes, [])
        self.assertEqual(verdict, ReviewVerdict.REQUEST_CHANGES)

    def test_verdict_comment_on_nit(self):
        outcomes = [
            VerificationOutcome(
                step_name="Tests",
                command="pytest",
                exit_code=0,
                output_snippet="Passed",
                passed=True,
            )
        ]
        findings = [
            ReviewFinding(
                category=FindingCategory.NIT,
                severity=FindingSeverity.LOW,
                path="src/a.py",
                start_line=1,
                end_line=1,
                principle_rationale="Naming style.",
            )
        ]
        verdict = self.synthesizer.determine_verdict(outcomes, findings)
        self.assertEqual(verdict, ReviewVerdict.COMMENT)

    def test_render_markdown_and_save(self):
        meta = PRMetadata(
            number=42,
            title="feat: test pr",
            body="PR body",
            author="tester",
            base_ref="main",
            head_ref="feat-test",
        )
        report = self.synthesizer.build_report(meta, [], [])
        md = self.synthesizer.render_markdown(report)
        self.assertIn("# Pull Request Review: #42", md)
        self.assertIn("✅ **APPROVE**", md)

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = self.synthesizer.save_report(report, output_dir=Path(tmp_dir))
            self.assertTrue(path.exists())
            self.assertIn("PR-42-review.md", path.name)


if __name__ == "__main__":
    unittest.main()
