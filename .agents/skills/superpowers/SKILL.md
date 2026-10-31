---
name: superpowers
description: >-
  Use for structured feature development, bugfixes, test-driven development (TDD),
  and subagent orchestration loops. Enforces Red-Green-Refactor cycles and explicit verification.
---

# /superpowers (TDD & Structured Execution Engine)

> Execution engine for structured development, brainstorming, TDD, and subagent orchestration.

## Overview
- **Trigger**: New feature development, non-trivial bugfixes, refactoring, or multi-step execution.
- **Pipeline Stage**: `Execution / Implementation`
- **Token Footprint**: Low-overhead routing; dispatches bite-sized subagents.

## Core Capabilities
1. **Brainstorming**: Interactive intent clarification before code is written.
2. **Writing Plans**: Bite-sized task decomposition (2-5 min per sub-task).
3. **Subagent-Driven Development**: Fresh subagents per task for parallel, isolated execution.
4. **Test-Driven Development**: Strict Red-Green-Refactor enforcement.
5. **Verification Before Completion**: Run automated suites and verify output before finishing.

## Standard Workflow

```
Brainstorm (clarify goals)
       │
       ▼
Write Plan (bite-sized tasks with files & verification)
       │
       ▼
Execute Task Loop:
   1. RED: Write failing automated test
   2. GREEN: Minimal code to pass
   3. REFACTOR: Clean up without breaking tests
   4. VERIFY: Full suite green
       │
       ▼
Delivery & Summary
```

## Verification Gate
- Run automated tests verifying the behavior.
- Capture command, exit code, and passed tests count.
