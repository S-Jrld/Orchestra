"""Routing decision explanation generator for human inspection and CLI diagnostics."""

from __future__ import annotations

import json
from typing import Any, Dict

from orchestra.registry.resolver import ResolutionResult


class RoutingExplainer:
    """Formats resolution decisions into clear human-readable or JSON reports."""

    @staticmethod
    def to_dict(res: ResolutionResult) -> Dict[str, Any]:
        return {
            "task": res.task,
            "inferred_tier": res.inferred_tier.value,
            "ambient_skills": [s.id for s in res.ambient_skills],
            "selected_skills": [s.id for s in res.selected_skills],
            "estimated_context_tokens": res.estimated_context_tokens,
            "candidates_considered": [
                {
                    "id": c.skill.id,
                    "score": c.score,
                    "reasons": c.reasons,
                    "explicit": c.explicitly_requested,
                }
                for c in res.candidates
            ],
            "selection_reasons": res.reasons,
            "excluded_candidates": res.excluded,
            "expanded_dependencies": res.expanded_dependencies,
            "resolved_conflicts": res.resolved_conflicts,
        }

    @staticmethod
    def format_text(res: ResolutionResult) -> str:
        lines = [
            "=== Orchestra Routing Explanation ===",
            f"Task: \"{res.task}\"",
            f"Inferred Tier: {res.inferred_tier.value}",
            f"Estimated Context: ~{res.estimated_context_tokens} tokens",
            "",
            "Ambient Session Skills (Active across session):",
        ]
        for s in res.ambient_skills:
            lines.append(f"  • {s.id} ({s.name})")

        lines.append("")
        lines.append("Selected Task Skills:")
        if res.selected_skills:
            for s in res.selected_skills:
                lines.append(f"  ✓ {s.id} ({s.name})")
                for r in res.reasons.get(s.id, []):
                    lines.append(f"      - {r}")
        else:
            lines.append("  (None selected — using default engineering standard protocols)")

        if res.candidates:
            lines.append("")
            lines.append("Candidates Evaluated:")
            for c in res.candidates:
                status = "SELECTED" if any(s.id == c.skill.id for s in res.selected_skills) else "EXCLUDED"
                lines.append(f"  [{status}] {c.skill.id} (Score: {c.score:.1f})")
                for r in c.reasons:
                    lines.append(f"      + {r}")

        if res.excluded:
            lines.append("")
            lines.append("Exclusions & Pruning:")
            for s_id, reason in res.excluded.items():
                lines.append(f"  ✗ {s_id}: {reason}")

        if res.expanded_dependencies:
            lines.append("")
            lines.append("Expanded Dependencies:")
            for dep in res.expanded_dependencies:
                lines.append(f"  + {dep}")

        if res.resolved_conflicts:
            lines.append("")
            lines.append("Resolved Conflicts:")
            for conf in res.resolved_conflicts:
                lines.append(f"  ! {conf}")

        return "\n".join(lines)
