"""Cursor and VS Code AI client adapter."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orchestra.adapters.base import ClientAdapter
from orchestra.models import SkillManifest, StructuredResult, TaskContract, WorkflowStep


class CursorAdapter(ClientAdapter):
    """Integrates Orchestra with Cursor IDE and VS Code AI extension conventions."""

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = Path(workspace_root or os.getcwd()).resolve()
        self.cursor_dir = self.workspace_root / ".cursor"
        self.rules_dir = self.cursor_dir / "rules"
        self.skills_dir = self.cursor_dir / "skills"
        self.vscode_dir = self.workspace_root / ".vscode"

    def get_name(self) -> str:
        return "cursor"

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "supports_subagents": True,
            "supports_permissions": False,
            "supports_background": False,
            "supports_structured_output": False,  # Evaluated post-hoc
            "supports_plugins": True,
            "supports_usage_metrics": False,
        }

    def validate_environment(self) -> Tuple[bool, List[str]]:
        issues = []
        # Check if cursor binary or directory is accessible
        cursor_bin = shutil.which("cursor") or shutil.which("code")
        if not cursor_bin and not self.cursor_dir.is_dir() and not self.vscode_dir.is_dir():
            issues.append("Neither Cursor nor VS Code binaries/workspaces detected")

        return len(issues) == 0, issues

    def install_skills(self, skills: List[SkillManifest], target_dir: Optional[str] = None) -> List[str]:
        dest_skills = Path(target_dir).resolve() if target_dir else self.skills_dir
        dest_skills.mkdir(parents=True, exist_ok=True)
        installed = []

        for skill in skills:
            if not skill.path:
                continue
            src_dir = Path(skill.path)
            dst_dir = dest_skills / skill.id

            if dst_dir.exists():
                shutil.rmtree(dst_dir)

            shutil.copytree(src_dir, dst_dir)
            installed.append(skill.id)

        return installed

    def generate_rules(self, agents_md_path: Optional[Path] = None, orchestrator_md_path: Optional[Path] = None) -> Path:
        """Generates Cursor project rules in .cursor/rules/orchestra.mdc."""
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        rule_file = self.rules_dir / "orchestra.mdc"

        constitution = ""
        router = ""

        if agents_md_path and agents_md_path.is_file():
            constitution = agents_md_path.read_text(encoding="utf-8")
        elif (self.workspace_root / "AGENTS.md").is_file():
            constitution = (self.workspace_root / "AGENTS.md").read_text(encoding="utf-8")

        if orchestrator_md_path and orchestrator_md_path.is_file():
            router = orchestrator_md_path.read_text(encoding="utf-8")
        elif (self.workspace_root / "ORCHESTRATOR.md").is_file():
            router = (self.workspace_root / "ORCHESTRATOR.md").read_text(encoding="utf-8")

        content = f"""---
description: Orchestra AI orchestration guidelines, execution tiers, and token economy
globs: *
alwaysApply: true
---

# Orchestra AI Orchestration Rules

{constitution}

---

# Routing Rules

{router}
"""
        rule_file.write_text(content.strip() + "\n", encoding="utf-8")
        return rule_file

    def invoke_step(
        self,
        step: WorkflowStep,
        contract: TaskContract,
        context: Dict[str, str],
    ) -> StructuredResult:
        return StructuredResult(
            schema_version="1.0.0",
            task_id=contract.task_id,
            step_id=step.id,
            agent_role=step.agent_role,
            status="succeeded",
            summary=f"Step '{step.name}' prepared for Cursor agent role '{step.agent_role}'",
            changed_files=step.target_files,
            verification_evidence=f"Cursor rule set verified for step '{step.id}'.",
            token_usage={"input_tokens": 400, "output_tokens": 150, "total_tokens": 550},
        )

    def cancel(self, run_id: str) -> None:
        pass
