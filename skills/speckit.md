# SKILL ADAPTER: SPEC-KIT

> Spec-Driven Development (SDD) toolkit enforcing specification, clarification, technical planning, checklists, task decomposition, and consistency analysis before code execution.

## Overview
- **Trigger**: New features, architectural changes, complex refactors requiring specification before implementation.
- **Pipeline Stage**: `Specification & Planning`
- **Output Artifacts**: `specs/<feature>/spec.md`, `specs/<feature>/plan.md`, `specs/<feature>/tasks.md`.

## Lifecycle Stages

```
Constitution (AGENTS.md)
       │
       ▼
1. Specify (/speckit.specify -> specs/<feature>/spec.md)
       │
       ▼
2. Clarify (/speckit.clarify)
       │
       ▼
3. Plan (/speckit.plan -> specs/<feature>/plan.md)
       │
       ▼
4. Checklist (/speckit.checklist)
       │
       ▼
5. Tasks (/speckit.tasks -> specs/<feature>/tasks.md)
       │
       ▼
6. Analyze (/speckit.analyze)
       │
       ▼
7. Compile & Execute (orch spec compile / orch spec run)
       │
       ▼
8. Converge (/speckit.converge)
```

## CLI Commands
- `orch spec init <feature-id>`: Scaffolds `specs/<feature-id>/` with SDD templates.
- `orch spec validate <feature-id>`: Cross-analyzes spec, plan, and tasks.
- `orch spec compile <feature-id>`: Compiles `tasks.md` to declarative Orchestra DAG JSON.
- `orch spec run <feature-id>`: Compiles and executes the feature DAG.
