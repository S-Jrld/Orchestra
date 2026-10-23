"""Orchestra client adapter implementations."""

from orchestra.adapters.base import ClientAdapter
from orchestra.adapters.mock import MockAdapter
from orchestra.adapters.opencode import OpenCodeAdapter
from orchestra.adapters.antigravity import AntigravityAdapter
from orchestra.adapters.cursor import CursorAdapter
from orchestra.adapters.claude import ClaudeCodeAdapter

__all__ = [
    "ClientAdapter",
    "MockAdapter",
    "OpenCodeAdapter",
    "AntigravityAdapter",
    "CursorAdapter",
    "ClaudeCodeAdapter",
]
