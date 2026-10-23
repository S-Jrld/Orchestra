"""Lightweight, zero-dependency JSON Schema Draft 2020-12 validator."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class SchemaValidationError(Exception):
    def __init__(self, message: str, path: str = "$", schema_path: str = ""):
        super().__init__(f"Schema validation error at {path}: {message}")
        self.message = message
        self.path = path
        self.schema_path = schema_path


class SchemaValidator:
    """Validates JSON data against Draft 2020-12 schemas without external dependencies."""

    @staticmethod
    def load_schema(schema_path_or_dict: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(schema_path_or_dict, dict):
            return schema_path_or_dict
        p = Path(schema_path_or_dict)
        if not p.exists():
            raise FileNotFoundError(f"Schema file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def validate(
        cls,
        data: Any,
        schema: Union[str, Path, Dict[str, Any]],
        path: str = "$",
    ) -> List[str]:
        """Validates data against schema. Returns list of error messages (empty if valid)."""
        schema_dict = cls.load_schema(schema)
        errors: List[str] = []
        cls._validate_node(data, schema_dict, path, errors)
        return errors

    @classmethod
    def is_valid(cls, data: Any, schema: Union[str, Path, Dict[str, Any]]) -> bool:
        return len(cls.validate(data, schema)) == 0

    @classmethod
    def assert_valid(cls, data: Any, schema: Union[str, Path, Dict[str, Any]]) -> None:
        errors = cls.validate(data, schema)
        if errors:
            raise SchemaValidationError("\n- " + "\n- ".join(errors))

    @classmethod
    def _validate_node(
        cls,
        data: Any,
        schema: Dict[str, Any],
        path: str,
        errors: List[str],
    ) -> None:
        # Check type
        expected_type = schema.get("type")
        if expected_type:
            if not cls._check_type(data, expected_type):
                errors.append(f"{path}: expected type '{expected_type}', got '{type(data).__name__}'")
                return  # skip further checks if type is wrong

        # Enum check
        if "enum" in schema:
            if data not in schema["enum"]:
                errors.append(f"{path}: value {data!r} not in allowed enum {schema['enum']}")

        # String constraints
        if isinstance(data, str):
            if "minLength" in schema and len(data) < schema["minLength"]:
                errors.append(f"{path}: string length {len(data)} < minLength {schema['minLength']}")
            if "maxLength" in schema and len(data) > schema["maxLength"]:
                errors.append(f"{path}: string length {len(data)} > maxLength {schema['maxLength']}")
            if "pattern" in schema:
                if not re.search(schema["pattern"], data):
                    errors.append(f"{path}: string '{data}' does not match pattern '{schema['pattern']}'")

        # Number constraints
        if isinstance(data, (int, float)) and not isinstance(data, bool):
            if "minimum" in schema and data < schema["minimum"]:
                errors.append(f"{path}: value {data} < minimum {schema['minimum']}")
            if "maximum" in schema and data > schema["maximum"]:
                errors.append(f"{path}: value {data} > maximum {schema['maximum']}")

        # Array constraints
        if isinstance(data, list):
            if "minItems" in schema and len(data) < schema["minItems"]:
                errors.append(f"{path}: array length {len(data)} < minItems {schema['minItems']}")
            if "maxItems" in schema and len(data) > schema["maxItems"]:
                errors.append(f"{path}: array length {len(data)} > maxItems {schema['maxItems']}")
            if "items" in schema and isinstance(schema["items"], dict):
                item_schema = schema["items"]
                for i, item in enumerate(data):
                    cls._validate_node(item, item_schema, f"{path}[{i}]", errors)

        # Object constraints
        if isinstance(data, dict):
            # Required fields
            if "required" in schema:
                for req in schema["required"]:
                    if req not in data:
                        errors.append(f"{path}: missing required property '{req}'")

            # Properties
            properties = schema.get("properties", {})
            additional_allowed = schema.get("additionalProperties", True)

            for key, val in data.items():
                if key in properties:
                    cls._validate_node(val, properties[key], f"{path}.{key}", errors)
                else:
                    if additional_allowed is False:
                        errors.append(f"{path}: unrecognized property '{key}' not allowed")
                    elif isinstance(additional_allowed, dict):
                        cls._validate_node(val, additional_allowed, f"{path}.{key}", errors)

    @staticmethod
    def _check_type(val: Any, expected: Union[str, List[str]]) -> bool:
        if isinstance(expected, list):
            return any(SchemaValidator._check_type(val, t) for t in expected)

        if expected == "string":
            return isinstance(val, str)
        elif expected == "integer":
            return isinstance(val, int) and not isinstance(val, bool)
        elif expected == "number":
            return isinstance(val, (int, float)) and not isinstance(val, bool)
        elif expected == "boolean":
            return isinstance(val, bool)
        elif expected == "array":
            return isinstance(val, list)
        elif expected == "object":
            return isinstance(val, dict)
        elif expected == "null":
            return val is None
        return True
