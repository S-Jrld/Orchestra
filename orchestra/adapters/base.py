"""Abstract Base Class for Orchestra client adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from orchestra.models import SkillManifest, StructuredResult, TaskContract, WorkflowStep


class ClientAdapter(ABC):
    """Canonical adapter interface translating Orchestra workflows to specific agent hosts."""

    @abstractmethod
    def get_name(self) -> str:
        """Returns the unique identifier of the adapter."""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """Returns declared capabilities (e.g. supports_subagents, supports_permissions)."""
        pass

    @abstractmethod
    def validate_environment(self) -> Tuple[bool, List[str]]:
        """Checks if client CLI tools and required directories exist on disk."""
        pass

    @abstractmethod
    def install_skills(self, skills: List[SkillManifest], target_dir: str) -> List[str]:
        """Packages and deploys skills in the client's native format."""
        pass

    @abstractmethod
    def invoke_step(
        self,
        step: WorkflowStep,
        contract: TaskContract,
        context: Dict[str, str],
    ) -> StructuredResult:
        """Executes a workflow step using the client runtime."""
        pass

    @abstractmethod
    def cancel(self, run_id: str) -> None:
        """Cancels an active execution run."""
        pass
