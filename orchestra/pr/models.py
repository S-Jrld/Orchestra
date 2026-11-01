"""Data models for the Orchestra PR orchestration workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FindingCategory(str, Enum):
    BLOCKER = "Blocker"
    MAJOR = "Major"
    MINOR = "Minor"
    NIT = "Nit"
    PRAISE = "Praise"


class FindingSeverity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"


class ReviewVerdict(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


@dataclass
class ChangedFile:
    path: str
    status: str  # added, modified, deleted, renamed
    additions: int = 0
    deletions: int = 0
    patch: str = ""
    is_filtered: bool = False
    filter_reason: Optional[str] = None


@dataclass
class PRMetadata:
    number: int
    title: str
    body: str
    author: str
    base_ref: str
    head_ref: str
    head_sha: str = ""
    commits: List[Dict[str, Any]] = field(default_factory=list)
    files: List[ChangedFile] = field(default_factory=list)
    url: str = ""


@dataclass
class VerificationOutcome:
    step_name: str
    command: str
    exit_code: int
    output_snippet: str
    duration_seconds: float = 0.0
    passed: bool = True
    error_diagnostics: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ReviewFinding:
    category: FindingCategory
    severity: FindingSeverity
    path: str
    start_line: int
    end_line: int
    principle_rationale: str
    suggested_diff: Optional[str] = None
    merge_impact: str = "Non-blocking"

    def __post_init__(self):
        if self.category in (FindingCategory.BLOCKER, FindingCategory.MAJOR):
            self.merge_impact = "Blocks merge"
        else:
            self.merge_impact = "Non-blocking"


@dataclass
class WorkspaceSnapshot:
    original_branch: str
    original_sha: str
    stash_pushed: bool = False
    stash_ref: Optional[str] = None
    timestamp: str = ""


@dataclass
class PRReviewReport:
    pr_number: int
    pr_title: str
    author: str
    base_ref: str
    head_ref: str
    verdict: ReviewVerdict
    executive_summary: str
    verification_outcomes: List[VerificationOutcome] = field(default_factory=list)
    findings: List[ReviewFinding] = field(default_factory=list)
    impacted_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    created_at: str = ""
