"""Unit tests for JSON Schema Draft 2020-12 validation."""

import json
from pathlib import Path
import unittest

from orchestra.validator import SchemaValidator


class TestSchemas(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.parent.parent
        self.schemas_dir = self.root / "schemas"

    def test_all_manifests_valid(self):
        schema = self.schemas_dir / "skill-manifest.json"
        manifests = list(self.root.glob("skills/*/manifest.json"))
        self.assertGreaterEqual(len(manifests), 8)

        for m_path in manifests:
            with self.subTest(manifest=m_path.parent.name):
                with open(m_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                errors = SchemaValidator.validate(data, schema)
                self.assertEqual(errors, [], f"Errors in {m_path}: {errors}")

    def test_manifest_missing_required_field_fails(self):
        schema = self.schemas_dir / "skill-manifest.json"
        invalid_data = {
            "schema_version": "1.0.0",
            "id": "broken",
            # missing name, version, kind, summary, triggers, capabilities
        }
        errors = SchemaValidator.validate(invalid_data, schema)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("missing required property" in e for e in errors))

    def test_workflow_definition_schema(self):
        schema = self.schemas_dir / "workflow-definition.json"
        wf_file = self.root / "workflows" / "feature-tdd.json"
        with open(wf_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        errors = SchemaValidator.validate(data, schema)
        self.assertEqual(errors, [])

    def test_agent_profile_schema(self):
        schema = self.schemas_dir / "agent-profile.json"
        valid_agent = {
            "schema_version": "1.0.0",
            "id": "researcher",
            "name": "Researcher",
            "role": "code_exploration",
            "mode": "subagent",
            "description": "Read-only exploration specialist",
            "capabilities": ["read", "search"],
            "permissions": [
                {"action": "read", "resource": "*", "effect": "allow"},
                {"action": "edit", "resource": "*", "effect": "deny"},
            ],
        }
        self.assertEqual(SchemaValidator.validate(valid_agent, schema), [])

    def test_structured_result_schema(self):
        schema = self.schemas_dir / "structured-result.json"
        valid_res = {
            "schema_version": "1.0.0",
            "task_id": "task_123",
            "step_id": "step_1",
            "agent_role": "tester",
            "status": "succeeded",
            "summary": "Failing test created",
            "changed_files": ["tests/test_x.py"],
            "verification_evidence": "Confirmed pytest failed on Red cycle",
        }
        self.assertEqual(SchemaValidator.validate(valid_res, schema), [])


if __name__ == "__main__":
    unittest.main()
