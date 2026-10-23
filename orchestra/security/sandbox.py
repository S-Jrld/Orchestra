"""Path traversal verification and secret redaction."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Union


class PathSandbox:
    """Validates that all accessed paths reside within authorized workspace roots."""

    def __init__(self, allowed_roots: List[Union[str, Path]]):
        self.allowed_roots = [Path(r).resolve() for r in allowed_roots]

    def is_safe_path(self, target_path: Union[str, Path]) -> bool:
        resolved = Path(target_path).resolve()
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def assert_safe_path(self, target_path: Union[str, Path]) -> None:
        if not self.is_safe_path(target_path):
            raise PermissionError(
                f"Security violation: path '{target_path}' is outside approved workspace roots: {self.allowed_roots}"
            )


class SecretRedactor:
    """Redacts sensitive credentials, tokens, private keys, and passwords from logs and prompts."""

    SECRET_PATTERNS = [
        # Generic API keys & bearer tokens
        (re.compile(r"(?i)(bearer|token|api_?key|auth|secret|password)[\s=:\"']+([a-zA-Z0-9_\-\.]{16,})[\"']?"), r"\1=[REDACTED_SECRET]"),
        # GitHub tokens
        (re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,255}"), "[REDACTED_GITHUB_TOKEN]"),
        # OpenAI / Anthropic keys
        (re.compile(r"sk-(proj-)?[A-Za-z0-9_-]{32,}"), "[REDACTED_AI_API_KEY]"),
        # AWS Access Key ID
        (re.compile(r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"), "[REDACTED_AWS_KEY]"),
        # Private RSA / SSH Keys
        (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    ]

    @classmethod
    def redact(cls, text: str) -> str:
        if not text:
            return text
        result = text
        for pattern, replacement in cls.SECRET_PATTERNS:
            result = pattern.sub(replacement, result)
        return result
