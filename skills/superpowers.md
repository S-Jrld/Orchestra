# SKILL ADAPTER: SUPERPOWERS

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
Loop per task:
  1. Dispatch subagent with Execution Brief
  2. Subagent writes failing test (RED)
  3. Subagent writes minimal code (GREEN)
  4. Reviewer audits diff
       │
       ▼
Verify full test suite green
       │
       ▼
Finish & report status honestly
```

## Commands
When available in the host environment (OpenCode / Antigravity):
- Brainstorming: Activate `brainstorming` skill
- Planning: Activate `writing-plans` skill
- TDD: Activate `test-driven-development` skill
- Verification: Activate `verification-before-completion` skill
