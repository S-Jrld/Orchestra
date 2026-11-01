---
name: speckit
description: >-
  Use for Spec-Driven Development (SDD), feature specifications, technical architecture planning,
  and compiling markdown tasks into deterministic Orchestra DAG workflows.
---

# /speckit (Spec-Driven Development Toolkit)

> Spec-Driven Development (SDD) toolkit enforcing specification, clarification, technical planning, checklists, task decomposition, and consistency analysis before code execution.

## Overview
- **Trigger**: New features, architectural changes, complex refactors requiring specification before implementation.
- **Pipeline Stage**: `Specification & Planning`
- **Output Artifacts**: `specs/<feature>/spec.md`, `specs/<feature>/plan.md`, `specs/<feature>/tasks.md`.

## Lifecycle Stages

```
Constitution (AGENTS.md + .specify/memory/constitution.md)
       │
       ▼
1. Specify (/speckit.specify -> specs/<feature>/spec.md)
   Focus: WHAT & WHY. User stories, acceptance criteria, boundaries. Zero tech stack syntax.
       │
       ▼
2. Clarify (/speckit.clarify)
   Focus: Quality gate interrogating edge cases, ambiguities, and implicit assumptions.
       │
       ▼
3. Plan (/speckit.plan -> specs/<feature>/plan.md)
   Focus: HOW. Architecture, contracts, schemas, tech stack, component interactions.
       │
       ▼
4. Checklist (/speckit.checklist)
   Focus: Acceptance criteria readiness check against constitutional constraints.
       │
       ▼
5. Tasks (/speckit.tasks -> specs/<feature>/tasks.md)
   Focus: Granular, dependency-ordered, testable tasks with roles and targets.
       │
       ▼
6. Analyze (/speckit.analyze)
   Focus: Cross-artifact consistency audit (spec.md <-> plan.md <-> tasks.md).
       │
       ▼
7. Compile & Execute (orch spec compile / orch spec run)
   Focus: Compiles tasks.md into Orchestra WorkflowDefinition DAG for deterministic execution.
       │
       ▼
8. Converge (/speckit.converge)
   Focus: Acceptance verification, regression test proof, and security audit sign-off.
```

## Task Checklist Notation (Compilable to DAG)

Format tasks in `specs/<feature>/tasks.md` with optional bracketed metadata for automated DAG scheduling:

```markdown
- [ ] [T01] Define interface schema [role: advisor, target: src/models.py, verify: python3 -m unittest tests/test_models.py]
- [ ] [T02] Write failing endpoint test [role: tester, deps: T01, target: tests/test_api.py, verify: pytest tests/test_api.py]
- [ ] [T03] Implement endpoint handler [role: orchestra, deps: T02, target: src/api.py, verify: pytest tests/test_api.py]
- [ ] [T04] Audit security and diff [role: reviewer, deps: T03, verify: ./bin/orch doctor]
```

## CLI Commands
- `orch spec init <feature-id>`: Scaffolds `specs/<feature-id>/` with SDD templates.
- `orch spec validate <feature-id>`: Runs consistency checks across spec, plan, and tasks.
- `orch spec compile <feature-id>`: Compiles `tasks.md` to declarative Orchestra DAG JSON.
- `orch spec run <feature-id>`: Compiles and executes the feature DAG with automated TDD verification.
