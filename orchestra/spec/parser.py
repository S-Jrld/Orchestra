"""Spec Kit markdown parser, validator, and scaffolding."""

from __future__ import annotations

import graphlib
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class SpecTask:
    id: str
    title: str
    agent_role: str = "orchestra"
    dependencies: List[str] = field(default_factory=list)
    target_files: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    verification_command: str = "true"
    completed: bool = False
    raw_line: str = ""


class SpecParser:
    """Parses Spec Kit markdown files (spec.md, plan.md, tasks.md)."""

    # Matches "- [ ] [T01] Task title [role: ..., deps: ...]"
    # or "- [ ] T01: Task title [role: ...]"
    # or "- [ ] Task title"
    TASK_REGEX = re.compile(
        r"^\s*-\s*\[(?P<status>[ xX])\]\s+(?:\[(?P<id_bracket>[A-Za-z0-9_-]+)\]|(?P<id_colon>[A-Za-z0-9_-]+):)?\s*(?P<title>[^\[\n]+?)(?:\s+\[(?P<tags>[^\]]+)\])?\s*$"
    )

    @classmethod
    def parse_tasks_content(cls, content: str) -> List[SpecTask]:
        """Parses markdown checklist content into a list of SpecTasks."""
        tasks: List[SpecTask] = []
        auto_index = 1
        previous_id: Optional[str] = None

        for line in content.splitlines():
            line_str = line.strip()
            if not line_str.startswith("- ["):
                continue

            match = cls.TASK_REGEX.match(line_str)
            if not match:
                continue

            status_char = match.group("status")
            completed = status_char.lower() == "x"

            raw_id = match.group("id_bracket") or match.group("id_colon")
            if not raw_id:
                task_id = f"T{auto_index:02d}"
                auto_index += 1
            else:
                task_id = raw_id.strip()

            title = match.group("title").strip()
            tags_str = match.group("tags") or ""

            agent_role = "orchestra"
            dependencies: List[str] = []
            target_files: List[str] = []
            required_skills: List[str] = ["speckit"]
            verification_command = "true"

            if tags_str:
                parsed_tags = cls._parse_tags(tags_str)
                if "role" in parsed_tags:
                    agent_role = parsed_tags["role"]
                if "deps" in parsed_tags or "depends_on" in parsed_tags:
                    deps_val = parsed_tags.get("deps") or parsed_tags.get("depends_on") or ""
                    dependencies = [
                        d.strip()
                        for d in deps_val.split(",")
                        if d.strip() and d.strip().lower() != "none"
                    ]
                if "target" in parsed_tags or "targets" in parsed_tags:
                    t_val = parsed_tags.get("target") or parsed_tags.get("targets") or ""
                    target_files = [t.strip() for t in t_val.split(",") if t.strip()]
                if "verify" in parsed_tags:
                    verification_command = parsed_tags["verify"]
                if "skills" in parsed_tags:
                    s_val = parsed_tags["skills"]
                    required_skills = [s.strip() for s in s_val.split(",") if s.strip()]
            else:
                if previous_id and not dependencies:
                    dependencies = [previous_id]

            previous_id = task_id

            tasks.append(
                SpecTask(
                    id=task_id,
                    title=title,
                    agent_role=agent_role,
                    dependencies=dependencies,
                    target_files=target_files,
                    required_skills=required_skills,
                    verification_command=verification_command,
                    completed=completed,
                    raw_line=line_str,
                )
            )

        return tasks

    @staticmethod
    def _parse_tags(tags_str: str) -> Dict[str, str]:
        """Parses comma-delimited key: value pairs inside brackets."""
        result: Dict[str, str] = {}
        pairs = re.split(r",\s*(?=[a-zA-Z0-9_-]+\s*:)", tags_str)
        for pair in pairs:
            if ":" in pair:
                k, v = pair.split(":", 1)
                result[k.strip().lower()] = v.strip()
        return result

    @classmethod
    def validate_task_dependencies(cls, tasks: List[SpecTask]) -> List[str]:
        """Validates that all dependencies exist and the task graph has no cycles."""
        errors: List[str] = []
        task_ids = {t.id for t in tasks}

        graph: Dict[str, Set[str]] = {}
        for t in tasks:
            graph[t.id] = set()
            for dep in t.dependencies:
                if dep not in task_ids:
                    errors.append(f"Task '{t.id}' references undefined dependency '{dep}'")
                else:
                    graph[t.id].add(dep)

        if not errors:
            ts = graphlib.TopologicalSorter(graph)
            try:
                ts.prepare()
            except graphlib.CycleError as e:
                cycle_nodes = list(e.args[1]) if len(e.args) > 1 else []
                errors.append(f"Cyclic dependency detected among tasks: {cycle_nodes or e}")

        return errors

    @classmethod
    def parse_tasks_file(cls, path: Path) -> List[SpecTask]:
        """Reads and parses tasks.md, validating dependencies."""
        if not path.is_file():
            raise FileNotFoundError(f"tasks.md not found at {path}")
        content = path.read_text(encoding="utf-8")
        tasks = cls.parse_tasks_content(content)
        dep_errors = cls.validate_task_dependencies(tasks)
        if dep_errors:
            raise ValueError(f"Invalid tasks dependency graph in {path}:\n" + "\n".join(dep_errors))
        return tasks


class SpecScaffold:
    """Scaffolds and validates feature specification workspaces under specs/."""

    SPEC_TEMPLATE = """# Feature Specification: {feature_id}

## 1. Objective & User Stories
- As a user, I want [capability], so that [outcome].

## 2. Functional Requirements
- FR-01: [Requirement description]
- FR-02: [Requirement description]

## 3. Non-Functional Constraints
- Adhere strictly to Orchestra L0 AGENTS.md and engineering contracts.
- Zero external dependencies beyond standard library unless approved.

## 4. Out of Scope
- [Explicit boundary of what will NOT be built]

## 5. Acceptance Criteria
- [ ] Automated tests green.
- [ ] Security audit clean with zero vulnerabilities.
"""

    PLAN_TEMPLATE = """# Technical Plan: {feature_id}

## 1. Architecture Overview
- **Tier**: Normal
- **Component Boundaries**:
  - Model / Schema layer
  - Core implementation logic
  - Verification & testing harness

## 2. Interfaces & Contracts
- Exact function signatures and data structures.

## 3. Threat Model & Security Boundaries
- Server-side validation of inputs.
- No hardcoded secrets or credentials.

## 4. Verification Command
- Automated test command: `python3 -m unittest ...`
"""

    TASKS_TEMPLATE = """# Tasks: {feature_id}

- [ ] [T01] Define interface schema and contracts [role: advisor, target: src/models.py, verify: true]
- [ ] [T02] Write failing automated test (RED) [role: tester, deps: T01, target: tests/test_feature.py, verify: true]
- [ ] [T03] Implement minimal solution (GREEN) [role: orchestra, deps: T02, target: src/feature.py, verify: true]
- [ ] [T04] Audit security and diff [role: reviewer, deps: T03, verify: ./bin/orch doctor]
"""

    CHECKLIST_TEMPLATE = """# Quality Checklist: {feature_id}

- [ ] Constitution: Aligned with Orchestra L0 Kernel
- [ ] Scope: Confined to active tier stop conditions
- [ ] Verifiability: Every task defines an executable bash verification command
"""

    @classmethod
    def init_feature(cls, specs_dir: Path, feature_id: str) -> Path:
        """Initializes a new feature specification directory."""
        feature_dir = specs_dir / feature_id
        feature_dir.mkdir(parents=True, exist_ok=True)

        files = {
            "spec.md": cls.SPEC_TEMPLATE.format(feature_id=feature_id),
            "plan.md": cls.PLAN_TEMPLATE.format(feature_id=feature_id),
            "tasks.md": cls.TASKS_TEMPLATE.format(feature_id=feature_id),
            "checklist.md": cls.CHECKLIST_TEMPLATE.format(feature_id=feature_id),
        }

        for filename, content in files.items():
            dest = feature_dir / filename
            if not dest.exists():
                dest.write_text(content, encoding="utf-8")

        return feature_dir

    @classmethod
    def validate_feature(cls, feature_dir: Path) -> List[str]:
        """Validates consistency across spec.md, plan.md, and tasks.md."""
        issues: List[str] = []
        if not feature_dir.is_dir():
            return [f"Feature directory not found: {feature_dir}"]

        for req in ["spec.md", "plan.md", "tasks.md"]:
            f = feature_dir / req
            if not f.is_file():
                issues.append(f"Missing required artifact: {req}")
            elif f.stat().st_size == 0:
                issues.append(f"Empty artifact: {req}")

        tasks_file = feature_dir / "tasks.md"
        if tasks_file.is_file() and tasks_file.stat().st_size > 0:
            try:
                tasks = SpecParser.parse_tasks_file(tasks_file)
                if not tasks:
                    issues.append("tasks.md contains no valid task checklist items")
            except Exception as e:
                issues.append(f"tasks.md validation error: {e}")

        return issues
