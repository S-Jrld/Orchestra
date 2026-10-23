"""Skill manifest loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from orchestra.models import SkillManifest
from orchestra.validator import SchemaValidator, SchemaValidationError


class ManifestLoader:
    """Loads, validates, and instantiates SkillManifest objects."""

    def __init__(self, schema_path: Optional[Union[str, Path]] = None):
        if schema_path is None:
            # Default to canonical schemas directory
            schema_path = Path(__file__).parent.parent.parent / "schemas" / "skill-manifest.json"
        self.schema_path = Path(schema_path)

    def load(self, manifest_file: Union[str, Path]) -> SkillManifest:
        path = Path(manifest_file)
        if not path.is_file():
            raise FileNotFoundError(f"Manifest not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        errors = SchemaValidator.validate(data, self.schema_path)
        if errors:
            raise SchemaValidationError(f"Invalid manifest at {path}:\n" + "\n".join(errors))

        return SkillManifest(
            schema_version=data["schema_version"],
            id=data["id"],
            name=data["name"],
            version=data["version"],
            kind=data["kind"],
            summary=data["summary"],
            triggers=data["triggers"],
            capabilities=data["capabilities"],
            source=data.get("source"),
            dependencies=data.get("dependencies", []),
            conflicts=data.get("conflicts", []),
            resources=data.get("resources", {}),
            compatibility=data.get("compatibility", {}),
            execution=data.get("execution", {}),
            security=data.get("security", {}),
            path=str(path.parent.resolve()),
        )
