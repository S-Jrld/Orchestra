"""Spec-to-DAG Compiler: transforms Spec Kit tasks into declarative Orchestra workflows."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from orchestra.models import Tier, WorkflowDefinition, WorkflowStep
from orchestra.spec.parser import SpecParser, SpecTask
from orchestra.validator import SchemaValidator


class SpecCompiler:
    """Compiles Spec Kit markdown tasks into canonical Orchestra WorkflowDefinitions."""

    VALID_ROLES = {"orchestra", "researcher", "advisor", "tester", "reviewer", "worker"}

    @classmethod
    def normalize_id(cls, raw_id: str) -> str:
        """Normalizes task ID to conform to ^[a-z0-9_-]+$."""
        clean = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_id).lower()
        return clean or "task_step"

    @classmethod
    def compile_tasks(
        cls,
        feature_id: str,
        tasks: List[SpecTask],
        description: Optional[str] = None,
        tier: Tier = Tier.NORMAL,
    ) -> WorkflowDefinition:
        """Converts a list of SpecTasks into a WorkflowDefinition."""
        normalized_feature_id = cls.normalize_id(f"spec-{feature_id}")
        steps: List[WorkflowStep] = []

        # Map original IDs to normalized IDs
        id_map: Dict[str, str] = {t.id: cls.normalize_id(t.id) for t in tasks}

        for task in tasks:
            step_id = id_map[task.id]
            role = task.agent_role.lower()
            if role not in cls.VALID_ROLES:
                role = "orchestra"

            mapped_deps = [id_map[d] for d in task.dependencies if d in id_map]

            step = WorkflowStep(
                id=step_id,
                name=task.title,
                agent_role=role,
                description=f"Generated from Spec Kit task {task.id}",
                required_skills=task.required_skills or ["speckit"],
                dependencies=mapped_deps,
                target_files=task.target_files,
                verification_command=task.verification_command or "true",
            )
            steps.append(step)

        acceptance_criteria = [f"Complete {t.id}: {t.title}" for t in tasks]

        return WorkflowDefinition(
            schema_version="1.0.0",
            id=normalized_feature_id,
            version="1.0.0",
            name=f"Spec Workflow: {feature_id}",
            description=description or f"Compiled from Spec Kit tasks for feature '{feature_id}'",
            tier=tier,
            steps=steps,
            acceptance_criteria=acceptance_criteria,
            budget_profile="Normal",
        )

    @classmethod
    def compile_feature(
        cls,
        feature_dir: Path,
        output_file: Optional[Path] = None,
        schema_path: Optional[Path] = None,
    ) -> Tuple[WorkflowDefinition, Path]:
        """Reads feature_dir/tasks.md, compiles to WorkflowDefinition, validates, and saves JSON."""
        tasks_file = feature_dir / "tasks.md"
        tasks = SpecParser.parse_tasks_file(tasks_file)
        if not tasks:
            raise ValueError(f"No tasks found to compile in {tasks_file}")

        feature_id = feature_dir.name
        workflow = cls.compile_tasks(feature_id, tasks)

        # Convert to dictionary conforming to workflow-definition.json schema
        wf_dict = {
            "schema_version": workflow.schema_version,
            "id": workflow.id,
            "version": workflow.version,
            "name": workflow.name,
            "description": workflow.description,
            "tier": workflow.tier.value,
            "budget_profile": workflow.budget_profile or "Normal",
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "agent_role": s.agent_role,
                    "required_skills": s.required_skills,
                    "dependencies": s.dependencies,
                    "target_files": s.target_files,
                    "verification_command": s.verification_command,
                }
                for s in workflow.steps
            ],
            "acceptance_criteria": workflow.acceptance_criteria,
        }

        # Validate against schema if available
        if schema_path and schema_path.is_file():
            SchemaValidator.assert_valid(wf_dict, schema_path)

        # Determine target file
        if not output_file:
            workflows_dir = feature_dir.parent.parent / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            output_file = workflows_dir / f"{workflow.id}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(wf_dict, f, indent=2)

        return workflow, output_file
