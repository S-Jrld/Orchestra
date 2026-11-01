"""Unit tests for Orchestra Spec Kit parser, scaffolding, and compiler."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from orchestra.cli import OrchestraCLI
from orchestra.models import Tier
from orchestra.spec import SpecCompiler, SpecParser, SpecScaffold, SpecTask
from orchestra.validator import SchemaValidator


class TestSpecParser(unittest.TestCase):
    def test_parse_bracketed_tasks(self):
        content = """# Feature Tasks
- [ ] [T01] Define schema [role: advisor, target: src/models.py, verify: pytest tests/test_m.py]
- [ ] [T02] Write failing test [role: tester, deps: T01, target: tests/test_m.py, verify: pytest]
- [x] [T03] Implement code [role: orchestra, deps: T02, target: src/models.py, verify: pytest]
"""
        tasks = SpecParser.parse_tasks_content(content)
        self.assertEqual(len(tasks), 3)

        self.assertEqual(tasks[0].id, "T01")
        self.assertEqual(tasks[0].title, "Define schema")
        self.assertEqual(tasks[0].agent_role, "advisor")
        self.assertEqual(tasks[0].target_files, ["src/models.py"])
        self.assertEqual(tasks[0].verification_command, "pytest tests/test_m.py")
        self.assertFalse(tasks[0].completed)

        self.assertEqual(tasks[1].id, "T02")
        self.assertEqual(tasks[1].agent_role, "tester")
        self.assertEqual(tasks[1].dependencies, ["T01"])

        self.assertEqual(tasks[2].id, "T03")
        self.assertEqual(tasks[2].agent_role, "orchestra")
        self.assertEqual(tasks[2].dependencies, ["T02"])
        self.assertTrue(tasks[2].completed)

    def test_parse_colon_tasks(self):
        content = """
- [ ] T01: Initial setup [role: advisor, verify: true]
- [ ] T02: Build feature [role: orchestra, deps: T01, verify: true]
"""
        tasks = SpecParser.parse_tasks_content(content)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].id, "T01")
        self.assertEqual(tasks[0].title, "Initial setup")
        self.assertEqual(tasks[1].id, "T02")
        self.assertEqual(tasks[1].dependencies, ["T01"])

    def test_parse_auto_sequencing(self):
        content = """
- [ ] First step
- [ ] Second step
- [ ] Third step
"""
        tasks = SpecParser.parse_tasks_content(content)
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].id, "T01")
        self.assertEqual(tasks[0].dependencies, [])

        self.assertEqual(tasks[1].id, "T02")
        self.assertEqual(tasks[1].dependencies, ["T01"])

        self.assertEqual(tasks[2].id, "T03")
        self.assertEqual(tasks[2].dependencies, ["T02"])

    def test_cycle_detection(self):
        tasks = [
            SpecTask(id="T01", title="Task 1", dependencies=["T02"]),
            SpecTask(id="T02", title="Task 2", dependencies=["T01"]),
        ]
        errors = SpecParser.validate_task_dependencies(tasks)
        self.assertTrue(any("Cyclic dependency" in e for e in errors))

    def test_undefined_dependency(self):
        tasks = [
            SpecTask(id="T01", title="Task 1", dependencies=["T99"]),
        ]
        errors = SpecParser.validate_task_dependencies(tasks)
        self.assertTrue(any("undefined dependency 'T99'" in e for e in errors))


class TestSpecScaffoldAndCompiler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.specs_dir = self.root / "specs"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scaffold_init_and_validate(self):
        feat_dir = SpecScaffold.init_feature(self.specs_dir, "demo-feature")
        self.assertTrue((feat_dir / "spec.md").is_file())
        self.assertTrue((feat_dir / "plan.md").is_file())
        self.assertTrue((feat_dir / "tasks.md").is_file())
        self.assertTrue((feat_dir / "checklist.md").is_file())

        issues = SpecScaffold.validate_feature(feat_dir)
        self.assertEqual(issues, [])

    def test_compile_to_workflow_definition(self):
        tasks = [
            SpecTask(id="T01", title="Contract", agent_role="advisor", verification_command="true"),
            SpecTask(id="T02", title="Test", agent_role="tester", dependencies=["T01"], verification_command="true"),
            SpecTask(id="T03", title="Code", agent_role="orchestra", dependencies=["T02"], verification_command="true"),
        ]
        wf = SpecCompiler.compile_tasks("auth-v2", tasks, tier=Tier.NORMAL)
        self.assertEqual(wf.id, "spec-auth-v2")
        self.assertEqual(len(wf.steps), 3)
        self.assertEqual(wf.steps[0].id, "t01")
        self.assertEqual(wf.steps[0].agent_role, "advisor")
        self.assertEqual(wf.steps[1].dependencies, ["t01"])

    def test_compile_feature_and_schema_validation(self):
        feat_dir = SpecScaffold.init_feature(self.specs_dir, "search-api")
        schema_path = Path(__file__).parent.parent.parent / "schemas" / "workflow-definition.json"

        wf, json_path = SpecCompiler.compile_feature(
            feat_dir,
            output_file=self.root / "spec-search-api.json",
            schema_path=schema_path,
        )
        self.assertTrue(json_path.is_file())

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        errors = SchemaValidator.validate(data, schema_path)
        self.assertEqual(errors, [])


class TestCLISpecCommands(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        # copy schemas to temp root
        repo_root = Path(__file__).parent.parent.parent
        schemas_dst = self.root / "schemas"
        schemas_dst.mkdir(parents=True, exist_ok=True)
        for s in (repo_root / "schemas").glob("*.json"):
            (schemas_dst / s.name).write_text(s.read_text())

        self.cli = OrchestraCLI(workspace_root=self.root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_spec_lifecycle(self):
        # 1. orch spec init
        rc_init = self.cli.run(["spec", "init", "user-auth"])
        self.assertEqual(rc_init, 0)
        self.assertTrue((self.root / "specs" / "user-auth" / "tasks.md").is_file())

        # 2. orch spec validate
        rc_val = self.cli.run(["spec", "validate", "user-auth"])
        self.assertEqual(rc_val, 0)

        # 3. orch spec compile
        rc_comp = self.cli.run(["spec", "compile", "user-auth"])
        self.assertEqual(rc_comp, 0)
        self.assertTrue((self.root / "workflows" / "spec-user-auth.json").is_file())

        # 4. orch spec run
        rc_run = self.cli.run(["spec", "run", "user-auth", "--adapter", "mock"])
        self.assertEqual(rc_run, 0)


if __name__ == "__main__":
    unittest.main()
