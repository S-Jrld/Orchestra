"""Progressive context builder managing L0/L1/L2/L3 tiers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from orchestra.models import SkillManifest


@dataclass
class ContextItem:
    layer: str  # L0, L1, L2, L3
    path: str
    content: str
    token_count: int
    content_hash: str
    reason: str


@dataclass
class ContextManifest:
    items: List[ContextItem]
    total_tokens: int
    layer_tokens: Dict[str, int] = field(default_factory=dict)

    def assemble_prompt(self) -> str:
        parts = []
        for it in self.items:
            parts.append(f"<!-- Layer: {it.layer} ({it.path}) [{it.reason}] -->\n{it.content}")
        return "\n\n".join(parts)


class ContextBuilder:
    """Assembles minimal required context adhering to Orchestra's 3-layer economy."""

    def __init__(self, root_dir: Union[str, Path]):
        self.root = Path(root_dir).resolve()

    def estimate_tokens(self, text: str) -> int:
        """Token count estimation (~4 characters per token / 4/3 words)."""
        words = len(text.split())
        chars = len(text)
        return max(words * 4 // 3, chars // 4, 1)

    def hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def build_context(
        self,
        task: str,
        selected_skills: Optional[List[SkillManifest]] = None,
        task_artifacts: Optional[Dict[str, str]] = None,
        include_l1: bool = True,
    ) -> ContextManifest:
        items: List[ContextItem] = []
        layer_tokens: Dict[str, int] = {"L0": 0, "L1": 0, "L2": 0, "L3": 0}

        # 1. L0 Kernel: AGENTS.md (Constitutional)
        agents_file = self.root / "AGENTS.md"
        if agents_file.is_file():
            content = agents_file.read_text(encoding="utf-8")
            tokens = self.estimate_tokens(content)
            items.append(
                ContextItem(
                    layer="L0",
                    path="AGENTS.md",
                    content=content,
                    token_count=tokens,
                    content_hash=self.hash_content(content),
                    reason="Permanent constitutional kernel & ambient engines (Caveman + Ponytail)",
                )
            )
            layer_tokens["L0"] += tokens

        # 2. L1 Router: ORCHESTRATOR.md (Transient)
        if include_l1:
            router_file = self.root / "ORCHESTRATOR.md"
            if router_file.is_file():
                content = router_file.read_text(encoding="utf-8")
                tokens = self.estimate_tokens(content)
                items.append(
                    ContextItem(
                        layer="L1",
                        path="ORCHESTRATOR.md",
                        content=content,
                        token_count=tokens,
                        content_hash=self.hash_content(content),
                        reason="Transient task & skill classification router",
                    )
                )
                layer_tokens["L1"] += tokens

        # 3. L2 Targeted Leaf Skills (Single active domain leaf)
        if selected_skills:
            for skill in selected_skills:
                # Look for SKILL.md in skill path
                if skill.path:
                    skill_md = Path(skill.path) / "SKILL.md"
                    if skill_md.is_file():
                        content = skill_md.read_text(encoding="utf-8")
                        tokens = self.estimate_tokens(content)
                        items.append(
                            ContextItem(
                                layer="L2",
                                path=f"skills/{skill.id}/SKILL.md",
                                content=content,
                                token_count=tokens,
                                content_hash=self.hash_content(content),
                                reason=f"Selected task-leaf skill: {skill.name}",
                            )
                        )
                        layer_tokens["L2"] += tokens

        # 4. L3 Task Artifacts & Evidence
        if task_artifacts:
            for art_name, art_content in task_artifacts.items():
                tokens = self.estimate_tokens(art_content)
                items.append(
                    ContextItem(
                        layer="L3",
                        path=art_name,
                        content=art_content,
                        token_count=tokens,
                        content_hash=self.hash_content(art_content),
                        reason=f"Task artifact: {art_name}",
                    )
                )
                layer_tokens["L3"] += tokens

        total = sum(it.token_count for it in items)
        return ContextManifest(
            items=items,
            total_tokens=total,
            layer_tokens=layer_tokens,
        )
