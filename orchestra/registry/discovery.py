"""Local skill discovery and indexing across workspaces and environments."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from orchestra.models import SkillManifest
from orchestra.registry.manifest import ManifestLoader


class SkillDiscovery:
    """Discovers and indexes skills from filesystem locations."""

    def __init__(self, loader: Optional[ManifestLoader] = None):
        self.loader = loader or ManifestLoader()
        self._skills_cache: Dict[str, SkillManifest] = {}

    def discover_workspace(self, root_dir: Union[str, Path]) -> Dict[str, SkillManifest]:
        """Scans root_dir/skills/ and root_dir/.agents/skills/ for manifest.json."""
        root = Path(root_dir).resolve()
        skills: Dict[str, SkillManifest] = {}

        candidate_dirs = [
            root / "skills",
            root / ".agents" / "skills",
            root / ".opencode" / "skills",
        ]

        for c_dir in candidate_dirs:
            if not c_dir.is_dir():
                continue
            for entry in sorted(c_dir.iterdir()):
                if entry.is_dir():
                    manifest_path = entry / "manifest.json"
                    if manifest_path.is_file():
                        try:
                            manifest = self.loader.load(manifest_path)
                            skills[manifest.id] = manifest
                        except Exception as e:
                            # Log and skip invalid manifests
                            print(f"[SkillDiscovery] Warning: Failed to load {manifest_path}: {e}")

        self._skills_cache = skills
        return skills

    def get_skill(self, skill_id: str) -> Optional[SkillManifest]:
        return self._skills_cache.get(skill_id)

    def list_skills(self) -> List[SkillManifest]:
        return list(self._skills_cache.values())
