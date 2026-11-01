# ACTIVE TASK

> Current single-task truth. Overwrite when complete; keep under 30 lines.

## Goal
Integrate GitHub Spec Kit into Orchestra: portable skill, declarative SDD workflow, Spec-to-DAG compiler, and CLI tooling.

## Classification
- **Tier**: Complex
- **Active Skill / Protocol**: [protocols/ENGINEERING_STANDARDS.md](protocols/ENGINEERING_STANDARDS.md), [protocols/SUBAGENT_DISPATCH.md](protocols/SUBAGENT_DISPATCH.md)
- **Activated Roles**: Lead Architect → Core Runtime Developer → QA Tester

## Scope & Target Files
- `skills/speckit/`: Skill manifest & token-dense markdown instructions
- `workflows/spec-driven-development.json`: Declarative 8-stage SDD workflow
- `orchestra/spec/`: Parser, validator, and DAG compiler
- `orchestra/cli.py`: `orch spec {init,validate,compile,run}` commands
- `tests/unit/test_spec_compiler.py`: Unit tests for parser, compiler, and CLI
- `ORCHESTRATOR.md`: Route table update
- `scripts/validate.sh`: Repository validation suite update

## Checklist
- [x] 1. Create portable `speckit` skill (`manifest.json`, `SKILL.md`, `skills/speckit.md`)
- [x] 2. Create `workflows/spec-driven-development.json`
- [x] 3. Implement `orchestra/spec/` (parser and compiler)
- [x] 4. Add `orch spec` CLI commands
- [x] 5. Write unit tests in `tests/unit/test_spec_compiler.py` (9/9 passed)
- [x] 6. Update `ORCHESTRATOR.md` and `scripts/validate.sh`
- [x] 7. Verify all suites pass (71/71 tests green, 100% validate.sh clean), create walkthrough

## Blockers & Open Decisions
- None. Spec Kit fully integrated and verified.
