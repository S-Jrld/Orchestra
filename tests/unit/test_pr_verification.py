"""Unit tests for TerminalVerificationRunner and diagnostic parsing."""

import unittest
from unittest.mock import patch

from orchestra.pr.models import ChangedFile
from orchestra.pr.verification import TerminalVerificationRunner


class TestTerminalVerification(unittest.TestCase):
    def setUp(self):
        self.runner = TerminalVerificationRunner()

    def test_parse_lint_diagnostics(self):
        lint_output = (
            "orchestra/cli.py:42:10: F401 'os' imported but unused\n"
            "orchestra/pr/safety.py:105: E501 line too long (120 > 88 characters)\n"
        )
        diagnostics = self.runner.parse_lint_diagnostics(lint_output)
        self.assertEqual(len(diagnostics), 2)
        self.assertEqual(diagnostics[0]["file"], "orchestra/cli.py")
        self.assertEqual(diagnostics[0]["line"], 42)
        self.assertEqual(diagnostics[0]["rule"], "F401")

    def test_parse_test_diagnostics(self):
        unittest_output = (
            "FAIL: test_invalid_login (tests.unit.test_auth.TestAuth)\n"
            "Traceback (most recent call last):\n"
            "AssertionError: 401 != 200\n"
        )
        diagnostics = self.runner.parse_test_diagnostics(unittest_output)
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0]["test"], "test_invalid_login")
        self.assertEqual(diagnostics[0]["suite"], "tests.unit.test_auth.TestAuth")

    @patch("orchestra.workflow.verifier.WorkflowVerifier.run_command")
    def test_environment_sync_detection(self, mock_cmd):
        mock_cmd.return_value = (0, "No broken requirements found.")
        changed = [ChangedFile(path="requirements.txt", status="modified")]
        outcome = self.runner.check_environment_sync(changed)
        self.assertIsNotNone(outcome)
        self.assertTrue(outcome.passed)


if __name__ == "__main__":
    unittest.main()
