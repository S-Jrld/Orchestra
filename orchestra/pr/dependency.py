"""Dependency Graph and Impact Tracer across modified files."""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from orchestra.pr.models import ChangedFile


class DependencyGraphTracer:
    """Traces imports and references to find upstream callers and downstream dependencies."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def trace_impact(self, changed_files: List[ChangedFile]) -> Dict[str, List[str]]:
        """Maps each non-filtered changed file to upstream files in the workspace that import it."""
        impact_map: Dict[str, List[str]] = {}
        high_signal_files = [f.path for f in changed_files if not f.is_filtered]

        if not high_signal_files:
            return impact_map

        # Map each changed file path to plausible module identifiers
        identifiers: Dict[str, Set[str]] = {}
        for path_str in high_signal_files:
            p = Path(path_str)
            names = {p.stem, p.name}
            # For python: package.module
            if p.suffix == ".py":
                parts = p.with_suffix("").parts
                names.add(".".join(parts))
                names.add(parts[-1])
            # For js/ts: relative path stems
            elif p.suffix in (".js", ".jsx", ".ts", ".tsx"):
                names.add(f"./{p.stem}")
                names.add(f"../{p.stem}")
                names.add(p.stem)
            identifiers[path_str] = names
            impact_map[path_str] = []

        # Scan workspace files for references
        for root, dirs, files in os.walk(self.workspace_root):
            # Ignore hidden and vendor directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "vendor", "__pycache__", "dist", "build")]
            for file in files:
                rel_path = str((Path(root) / file).relative_to(self.workspace_root))
                # Skip self
                if rel_path in identifiers:
                    continue

                if file.endswith(".py"):
                    self._check_python_references(Path(root) / file, rel_path, identifiers, impact_map)
                elif file.endswith((".js", ".jsx", ".ts", ".tsx")):
                    self._check_js_references(Path(root) / file, rel_path, identifiers, impact_map)

        return impact_map

    def _check_python_references(
        self,
        full_path: Path,
        rel_path: str,
        identifiers: Dict[str, Set[str]],
        impact_map: Dict[str, List[str]],
    ) -> None:
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(full_path))
        except Exception:
            return

        imported_modules: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module)

        for changed_path, candidates in identifiers.items():
            for cand in candidates:
                if any(cand == mod or mod.startswith(cand + ".") for mod in imported_modules):
                    if rel_path not in impact_map[changed_path]:
                        impact_map[changed_path].append(rel_path)

    def _check_js_references(
        self,
        full_path: Path,
        rel_path: str,
        identifiers: Dict[str, Set[str]],
        impact_map: Dict[str, List[str]],
    ) -> None:
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        import_pattern = re.compile(r"""(?:import|from|require)\s*\(?['"]([^'"]+)['"]\)?""")
        matches = set(import_pattern.findall(content))

        for changed_path, candidates in identifiers.items():
            for cand in candidates:
                if any(cand in m for m in matches):
                    if rel_path not in impact_map[changed_path]:
                        impact_map[changed_path].append(rel_path)
