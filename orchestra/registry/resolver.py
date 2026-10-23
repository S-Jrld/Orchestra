"""Deterministic skill selection and conflict resolution engine."""

from __future__ import annotations

import fnmatch
import graphlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from orchestra.models import SkillManifest, Tier


@dataclass
class RoutingCandidate:
    skill: SkillManifest
    score: float
    reasons: List[str] = field(default_factory=list)
    explicitly_requested: bool = False


@dataclass
class ResolutionResult:
    task: str
    inferred_tier: Tier
    selected_skills: List[SkillManifest]
    ambient_skills: List[SkillManifest]
    candidates: List[RoutingCandidate]
    reasons: Dict[str, List[str]]
    excluded: Dict[str, str]
    expanded_dependencies: List[str]
    resolved_conflicts: List[str]
    estimated_context_tokens: int


class SkillResolver:
    """Selects and resolves skills deterministically according to task intents and context bounds."""

    def __init__(self, skills: Dict[str, SkillManifest]):
        self.skills = skills

    def resolve(
        self,
        task: str,
        context_budget_tokens: int = 4000,
        target_files: Optional[List[str]] = None,
    ) -> ResolutionResult:
        normalized_task = self._normalize_task(task)
        inferred_tier = self._infer_tier(normalized_task)
        explicit_ids = self._extract_explicit_skills(normalized_task)

        candidates: List[RoutingCandidate] = []
        reasons: Dict[str, List[str]] = {}
        excluded: Dict[str, str] = {}
        expanded_deps: List[str] = []
        resolved_conflicts: List[str] = []

        # Ambient skills (e.g. caveman) are always active unless explicitly suppressed
        ambient_skills: List[SkillManifest] = []
        for s in self.skills.values():
            if s.kind == "session-ambient":
                ambient_skills.append(s)

        # Score all task-leaf skills
        for s_id, skill in self.skills.items():
            if skill.kind == "session-ambient":
                continue

            score = 0.0
            s_reasons = []
            is_explicit = s_id in explicit_ids

            if is_explicit:
                score += 100.0
                s_reasons.append(f"Explicitly referenced in task: {s_id}")

            # Check command triggers
            cmd_triggers = skill.triggers.get("command_triggers", [])
            for cmd in cmd_triggers:
                if cmd.lower() in normalized_task:
                    score += 50.0
                    s_reasons.append(f"Matched command trigger: {cmd}")

            # Check keyword matches
            keywords = skill.triggers.get("keywords", [])
            for kw in keywords:
                # Word boundary match
                if re.search(r"\b" + re.escape(kw.lower()) + r"\b", normalized_task):
                    score += 10.0
                    s_reasons.append(f"Matched keyword: '{kw}'")

            # Check intent matches
            intents = skill.triggers.get("intents", [])
            for intent in intents:
                if intent.lower() in normalized_task:
                    score += 20.0
                    s_reasons.append(f"Matched intent: '{intent}'")

            # Check file pattern matches if target_files provided
            file_patterns = skill.triggers.get("file_patterns", [])
            if target_files and file_patterns:
                for tf in target_files:
                    for pat in file_patterns:
                        if fnmatch.fnmatch(tf, pat):
                            score += 15.0
                            s_reasons.append(f"Matched file pattern '{pat}' on '{tf}'")

            if score > 0:
                candidates.append(
                    RoutingCandidate(
                        skill=skill,
                        score=score,
                        reasons=s_reasons,
                        explicitly_requested=is_explicit,
                    )
                )

        # Deterministic sorting: highest score first, then alphabetical by ID as tie-breaker
        candidates.sort(key=lambda c: (-c.score, c.skill.id))

        # Select primary candidate (or top candidates based on pipeline)
        selected_map: Dict[str, SkillManifest] = {}
        for cand in candidates:
            # Check conflicts
            has_conflict = False
            for conf in cand.skill.conflicts:
                if conf in selected_map:
                    has_conflict = True
                    resolved_conflicts.append(f"Skipped {cand.skill.id} due to conflict with {conf}")
                    excluded[cand.skill.id] = f"Conflicts with {conf}"
                    break
            if has_conflict:
                continue

            # Per Orchestra single-leaf policy, choose the most specific matching task-leaf
            if len(selected_map) >= 1 and not cand.explicitly_requested:
                excluded[cand.skill.id] = f"Superseded by higher-ranked candidate {list(selected_map.keys())[0]}"
                continue

            selected_map[cand.skill.id] = cand.skill
            reasons[cand.skill.id] = cand.reasons

        # Expand dependencies
        to_expand = list(selected_map.keys())
        dep_graph: Dict[str, Set[str]] = {}

        while to_expand:
            curr_id = to_expand.pop(0)
            curr_skill = self.skills.get(curr_id)
            if not curr_skill:
                continue

            deps = set(curr_skill.dependencies)
            dep_graph[curr_id] = deps

            for dep_id in deps:
                if dep_id not in self.skills:
                    excluded[dep_id] = f"Dependency '{dep_id}' required by '{curr_id}' not found in registry"
                    continue
                if dep_id not in selected_map:
                    dep_skill = self.skills[dep_id]
                    selected_map[dep_id] = dep_skill
                    reasons[dep_id] = [f"Required dependency of {curr_id}"]
                    expanded_deps.append(dep_id)
                    to_expand.append(dep_id)

        # Cycle detection using graphlib.TopologicalSorter
        if dep_graph:
            try:
                sorter = graphlib.TopologicalSorter(dep_graph)
                sorter.prepare()
            except graphlib.CycleError as e:
                cycle_str = " -> ".join(e.args[1]) if len(e.args) > 1 else "cycle detected"
                raise ValueError(f"Dependency cycle detected among skills: {cycle_str}")

        # Budget check & fitting
        total_estimated_tokens = sum(
            s.execution.get("estimated_tokens", 500) for s in ambient_skills
        ) + sum(
            s.execution.get("estimated_tokens", 800) for s in selected_map.values()
        )

        final_selected = list(selected_map.values())

        return ResolutionResult(
            task=task,
            inferred_tier=inferred_tier,
            selected_skills=final_selected,
            ambient_skills=ambient_skills,
            candidates=candidates,
            reasons=reasons,
            excluded=excluded,
            expanded_dependencies=expanded_deps,
            resolved_conflicts=resolved_conflicts,
            estimated_context_tokens=total_estimated_tokens,
        )

    def _normalize_task(self, text: str) -> str:
        return " ".join(text.strip().split()).lower()

    def _infer_tier(self, text: str) -> Tier:
        text_lower = text.lower()
        if any(w in text_lower for w in ["architectur", "adr", "subsystem", "framework", "database redesign", "persistence store"]):
            return Tier.ARCHITECTURAL
        if any(w in text_lower for w in ["cross-module", "auth", "breaking", "migration", "security review"]):
            return Tier.COMPLEX
        if any(w in text_lower for w in ["typo", "formatting", "rename", "comment", "docstring"]):
            return Tier.TINY
        return Tier.NORMAL

    def _extract_explicit_skills(self, text: str) -> Set[str]:
        explicit: Set[str] = set()
        # Look for @skill or /skill
        for match in re.finditer(r"[@/]([a-z0-9_-]+)", text):
            token = match.group(1).replace("-", "_")
            if token in self.skills:
                explicit.add(token)
            # Check alternative hyphen/underscore formats
            alt = token.replace("_", "-")
            for s_id in self.skills:
                if s_id.replace("_", "-") == alt:
                    explicit.add(s_id)
        return explicit
