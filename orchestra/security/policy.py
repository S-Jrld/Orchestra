"""Execution policy engine enforcing least-privilege security boundaries."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from orchestra.models import AgentProfile
from orchestra.security.sandbox import PathSandbox, SecretRedactor


class SecurityViolationError(Exception):
    pass


class SecurityPolicyEngine:
    """Evaluates agent actions, tools, and file paths against security policies."""

    FORBIDDEN_FILE_PATTERNS = [
        "**/.git/**",
        "**/.env*",
        "**/id_rsa*",
        "**/id_ed25519*",
        "**/credentials*",
        "/etc/**",
        "/root/**",
        "~/.ssh/**",
    ]

    def __init__(self, workspace_root: Union[str, Path]):
        self.workspace_root = Path(workspace_root).resolve()
        self.sandbox = PathSandbox([self.workspace_root])

    def validate_file_access(self, target_path: str, action: str = "read") -> None:
        """Validates that a file target is safe to read/write."""
        # 1. Sandbox boundary check
        self.sandbox.assert_safe_path(self.workspace_root / target_path)

        # 2. Forbidden pattern checks
        normalized = str(Path(target_path)).replace("\\", "/")
        for pattern in self.FORBIDDEN_FILE_PATTERNS:
            if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(f"/{normalized}", pattern):
                raise SecurityViolationError(
                    f"Access denied: file '{target_path}' matches protected security pattern '{pattern}'"
                )

    def validate_agent_action(self, agent: AgentProfile, action: str, resource: str) -> None:
        """Validates if agent permissions allow the requested action."""
        # Check explicit permissions
        allowed = False
        denied = False

        for perm in agent.permissions:
            if perm.action == action or perm.action == "*":
                if fnmatch.fnmatch(resource, perm.resource):
                    if perm.effect == "deny":
                        denied = True
                        break
                    elif perm.effect == "allow":
                        allowed = True

        if denied or not allowed:
            raise SecurityViolationError(
                f"Agent '{agent.id}' is denied permission for action '{action}' on resource '{resource}'"
            )

    def redact_text(self, text: str) -> str:
        return SecretRedactor.redact(text)
