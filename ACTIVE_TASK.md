# ACTIVE TASK

> Current single-task truth. Overwrite when complete; keep under 30 lines.

## Goal
Implement local VS Code PR orchestration workflow in Orchestra: pre-flight safety snapshot, ingestion pipeline, terminal verification, 7-standard evaluation, Conventional Comments, and review synthesis.

## Classification
- **Tier**: Normal
- **Active Skill / Protocol**: [protocols/ENGINEERING_STANDARDS.md](protocols/ENGINEERING_STANDARDS.md), [skills/speckit.md](skills/speckit.md)
- **Activated Roles**: Principal AI Systems Architect & Staff DevOps Engineer

## Scope & Target Files
- `orchestra/pr/`: Core safety, ingestion, dependency, verification, evaluator, formatter, synthesizer modules
- `orchestra/cli.py`: `orch pr review` subcommand integration
- `schemas/pr-review-record.json`: Review schema
- `workflows/pr-orchestration.json`: Workflow DAG
- `templates/PR_REVIEW_REPORT.md` & `templates/PR_REVIEW_PROMPT.md`: Review templates
- `tests/unit/test_pr_*.py`: Comprehensive unit test suite

## Checklist
- [x] 1. Phase 1 Discovery: Topology audit, tooling inventory, boundary definition
- [x] 2. Phase 8 Spec & Approval: Drafted and approved `pr-orchestration-spec.md`
- [x] 3. Modular Build: Core `orchestra/pr/` package implementation
- [x] 4. CLI & Schema: Added `orch pr review`, review schema, workflow DAG
- [x] 5. Automated Tests: 96/96 passing across all test suites
- [x] 6. Dry-Run Validation: Verified end-to-end review on REACH PR #20 with zero workspace corruption

## Blockers & Open Decisions
- None. System is fully operational and validated.
