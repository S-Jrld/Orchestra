"""Unit tests for MultiDimensionalEvaluator and the 7 software standards."""

import unittest

from orchestra.pr.evaluator import MultiDimensionalEvaluator
from orchestra.pr.models import (
    ChangedFile,
    FindingCategory,
    PRMetadata,
    VerificationOutcome,
)


class TestMultiDimensionalEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = MultiDimensionalEvaluator()

    def test_security_hardcoded_secret_detected_as_blocker(self):
        patch = (
            "@@ -10,3 +10,4 @@\n"
            "+def get_client():\n"
            "+    api_key = 'abcdef1234567890secret'\n"
            "+    return Client(api_key)\n"
        )
        files = [ChangedFile(path="src/client.py", status="modified", patch=patch)]
        meta = PRMetadata(
            number=1,
            title="feat: client",
            body="Adds client",
            author="dev",
            base_ref="main",
            head_ref="feat",
            commits=[{"messageHeadline": "feat: client"}],
        )

        findings = self.evaluator.evaluate(meta, files, [])
        blockers = [f for f in findings if f.category == FindingCategory.BLOCKER]
        self.assertTrue(any("secret" in b.principle_rationale.lower() for b in blockers))

    def test_security_shell_injection_detected_as_blocker(self):
        patch = (
            "@@ -1,3 +1,4 @@\n"
            "+import subprocess\n"
            "+def run(cmd):\n"
            "+    subprocess.run(cmd, shell=True)\n"
        )
        files = [ChangedFile(path="src/exec.py", status="modified", patch=patch)]
        meta = PRMetadata(
            number=2,
            title="feat: exec",
            body="Adds exec",
            author="dev",
            base_ref="main",
            head_ref="feat",
            commits=[{"messageHeadline": "feat: exec"}],
        )

        findings = self.evaluator.evaluate(meta, files, [])
        blockers = [f for f in findings if f.category == FindingCategory.BLOCKER]
        self.assertTrue(any("shell=true" in b.principle_rationale.lower() for b in blockers))

    def test_defect_bare_except_detected_as_major(self):
        patch = (
            "@@ -1,4 +1,5 @@\n"
            "+try:\n"
            "+    do_work()\n"
            "+except:\n"
            "+    pass\n"
        )
        files = [ChangedFile(path="src/worker.py", status="modified", patch=patch)]
        meta = PRMetadata(
            number=3,
            title="fix: worker",
            body="Fix worker",
            author="dev",
            base_ref="main",
            head_ref="fix",
            commits=[{"messageHeadline": "fix: worker"}],
        )

        findings = self.evaluator.evaluate(meta, files, [])
        majors = [f for f in findings if f.category == FindingCategory.MAJOR]
        self.assertTrue(any("bare except" in m.principle_rationale.lower() for m in majors))

    def test_test_quality_missing_tests_detected_as_major(self):
        patch = "@@ -1,2 +1,3 @@\n+def new_feature(): return True\n"
        files = [ChangedFile(path="src/feature.py", status="modified", patch=patch)]
        meta = PRMetadata(
            number=4,
            title="feat: new feature",
            body="New feature without test",
            author="dev",
            base_ref="main",
            head_ref="feat",
            commits=[{"messageHeadline": "feat: new feature"}],
        )

        findings = self.evaluator.evaluate(meta, files, [])
        majors = [f for f in findings if f.category == FindingCategory.MAJOR]
        self.assertTrue(any("without accompanying automated unit" in m.principle_rationale for m in majors))

    def test_commit_hygiene_nonconventional_commit_detected_as_nit(self):
        files = [ChangedFile(path="tests/test_x.py", status="modified", patch="@@ -1,1 +1,2 @@\n+pass\n")]
        meta = PRMetadata(
            number=5,
            title="update stuff",
            body="Description",
            author="dev",
            base_ref="main",
            head_ref="patch",
            commits=[{"messageHeadline": "updated stuff quickly"}],
        )

        findings = self.evaluator.evaluate(meta, files, [])
        nits = [f for f in findings if f.category == FindingCategory.NIT]
        self.assertTrue(any("conventional commits" in n.principle_rationale.lower() for n in nits))

    def test_verification_failure_converted_to_blocker(self):
        meta = PRMetadata(
            number=6,
            title="fix: bug",
            body="Fix bug",
            author="dev",
            base_ref="main",
            head_ref="fix",
            commits=[{"messageHeadline": "fix: bug"}],
        )
        outcomes = [
            VerificationOutcome(
                step_name="Targeted Tests",
                command="pytest",
                exit_code=1,
                output_snippet="1 failed in 0.2s",
                passed=False,
                error_diagnostics=[{"file": "tests/test_foo.py", "line": 42, "summary": "AssertionError"}],
            )
        ]
        findings = self.evaluator.evaluate(meta, [], outcomes)
        blockers = [f for f in findings if f.category == FindingCategory.BLOCKER]
        self.assertTrue(len(blockers) >= 1)
        self.assertEqual(blockers[0].path, "tests/test_foo.py")


if __name__ == "__main__":
    unittest.main()
