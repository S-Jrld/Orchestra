"""Unit tests for Security Guardrails and Secret Redaction."""

from pathlib import Path
import unittest

from orchestra.models import AgentPermission, AgentProfile
from orchestra.security.policy import SecurityPolicyEngine, SecurityViolationError
from orchestra.security.sandbox import PathSandbox, SecretRedactor


class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.parent.parent
        self.engine = SecurityPolicyEngine(self.root)

    def test_path_traversal_rejection(self):
        sandbox = PathSandbox([self.root])
        # Safe inside root
        self.assertTrue(sandbox.is_safe_path(self.root / "README.md"))
        self.assertTrue(sandbox.is_safe_path(self.root / "src" / "test.py"))

        # Unsafe outside root
        self.assertFalse(sandbox.is_safe_path("/etc/passwd"))
        self.assertFalse(sandbox.is_safe_path(self.root / ".." / ".." / "etc" / "shadow"))

    def test_protected_patterns_blocked(self):
        with self.assertRaises(SecurityViolationError):
            self.engine.validate_file_access(".git/config", action="write")

        with self.assertRaises(SecurityViolationError):
            self.engine.validate_file_access(".env", action="read")

        with self.assertRaises(SecurityViolationError):
            self.engine.validate_file_access("id_rsa", action="read")

    def test_secret_redaction(self):
        raw_text = "Here is my secret token: gh_token=ghp_ABC123456789012345678901234567890123 and sk-proj-12345678901234567890123456789012"
        redacted = SecretRedactor.redact(raw_text)

        self.assertNotIn("ghp_ABC123456789012345678901234567890123", redacted)
        self.assertNotIn("sk-proj-12345678901234567890123456789012", redacted)
        self.assertIn("[REDACTED_AI_API_KEY]", redacted)

    def test_agent_permission_enforcement(self):
        researcher = AgentProfile(
            schema_version="1.0.0",
            id="researcher",
            name="Researcher",
            role="exploration",
            mode="subagent",
            description="Read-only",
            capabilities=["read"],
            permissions=[
                AgentPermission(action="read", resource="*", effect="allow"),
                AgentPermission(action="write", resource="*", effect="deny"),
            ],
        )

        # Allow read
        self.engine.validate_agent_action(researcher, "read", "src/file.py")

        # Deny write
        with self.assertRaises(SecurityViolationError):
            self.engine.validate_agent_action(researcher, "write", "src/file.py")


if __name__ == "__main__":
    unittest.main()
