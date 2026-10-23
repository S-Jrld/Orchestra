# Orchestra Specification & Schemas

The Orchestra Specification formalizes all interactions, inputs, and outputs across the orchestration lifecycle using Draft 2020-12 JSON Schemas.

## Canonical Schemas

| Schema | File Path | Purpose |
|---|---|---|
| **Skill Manifest** | [`schemas/skill-manifest.json`](../schemas/skill-manifest.json) | Metadata, triggers, capabilities, and dependencies for skills |
| **Agent Profile** | [`schemas/agent-profile.json`](../schemas/agent-profile.json) | Canonical agent definition, permissions, and tool controls |
| **Workflow Definition** | [`schemas/workflow-definition.json`](../schemas/workflow-definition.json) | Declarative DAG workflow specification |
| **Task Contract** | [`schemas/task-contract.json`](../schemas/task-contract.json) | Bounded subagent Execution Brief contract |
| **Execution Policy** | [`schemas/execution-policy.json`](../schemas/execution-policy.json) | Security sandbox, path allowlists, and approval gates |
| **Structured Result** | [`schemas/structured-result.json`](../schemas/structured-result.json) | Output contract returned by specialist subagents |
| **Verification Report** | [`schemas/verification-report.json`](../schemas/verification-report.json) | Empirical completion evidence format |
| **Run Record** | [`schemas/run-record.json`](../schemas/run-record.json) | Structured execution trace for audit and recovery |

## Schema Validation

Validate any payload against a schema using the CLI or programmatic API:

```bash
# Validate all skills in workspace
orch skills validate

# Validate a declarative workflow definition
orch workflow validate workflows/feature-tdd.json
```
