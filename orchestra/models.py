"""Canonical data models for the Orchestra framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Tier(str, Enum):
    AMBIENT = "Ambient"
    TINY = "Tiny"
    NORMAL = "Normal"
    COMPLEX = "Complex"
    ARCHITECTURAL = "Architectural"


class StepStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SkillManifest:
    schema_version: str
    id: str
    name: str
    version: str
    kind: str
    summary: str
    triggers: Dict[str, List[str]]
    capabilities: List[str]
    source: Optional[Dict[str, str]] = None
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    compatibility: Dict[str, Any] = field(default_factory=dict)
    execution: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)
    path: Optional[str] = None


@dataclass
class AgentPermission:
    action: str
    resource: str
    effect: str


@dataclass
class AgentProfile:
    schema_version: str
    id: str
    name: str
    role: str
    mode: str
    description: str
    capabilities: List[str]
    permissions: List[AgentPermission]
    color: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=list)
    denied_tools: List[str] = field(default_factory=list)
    model_preferences: Dict[str, Any] = field(default_factory=dict)
    limits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    id: str
    name: str
    agent_role: str
    description: Optional[str] = None
    required_skills: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    target_files: List[str] = field(default_factory=list)
    verification_command: Optional[str] = None
    timeout_seconds: int = 180
    retry_limit: int = 2
    approval_gate: bool = False
    budget_fraction: float = 1.0
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)


@dataclass
class WorkflowDefinition:
    schema_version: str
    id: str
    version: str
    name: str
    description: str
    tier: Tier
    steps: List[WorkflowStep]
    acceptance_criteria: List[str]
    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    budget_profile: Optional[str] = None


@dataclass
class TaskContract:
    schema_version: str
    task_id: str
    objective: str
    agent_role: str
    scope: Dict[str, Any]
    acceptance_criteria: List[str]
    verification_command: str
    parent_run_id: Optional[str] = None
    step_id: Optional[str] = None
    selected_skills: List[str] = field(default_factory=list)
    input_artifacts: Dict[str, str] = field(default_factory=dict)
    budget_allocation: Dict[str, Any] = field(default_factory=dict)
    stop_condition: Optional[str] = None


@dataclass
class StructuredResult:
    schema_version: str
    task_id: str
    step_id: str
    agent_role: str
    status: str
    summary: str
    changed_files: List[str]
    verification_evidence: str
    tests_run: List[Dict[str, Any]] = field(default_factory=list)
    unresolved_risks: List[str] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)


@dataclass
class VerificationReport:
    schema_version: str
    status: str
    tier: str
    target_changes: List[str]
    automated_tests: List[Dict[str, Any]]
    lint_status: Dict[str, Any]
    unverified_surfaces: List[str] = field(default_factory=list)


@dataclass
class BudgetLimit:
    max_calls: int = 20
    max_input_tokens: int = 50000
    max_output_tokens: int = 15000
    max_total_tokens: int = 65000
    max_duration_seconds: int = 600
    max_parallel_workers: int = 4
    max_cost_usd: Optional[float] = None


@dataclass
class StepRunRecord:
    step_id: str
    name: str
    agent_role: str
    status: StepStatus
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    retry_count: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class RunRecord:
    schema_version: str
    run_id: str
    workflow_id: str
    tier: str
    status: RunStatus
    adapter: str
    created_at: str
    step_records: List[StepRunRecord]
    task_description: Optional[str] = None
    model: Optional[str] = None
    selected_skills: List[str] = field(default_factory=list)
    completed_at: Optional[str] = None
    total_token_usage: Dict[str, int] = field(default_factory=dict)
    estimated_cost_usd: float = 0.0
