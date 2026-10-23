# Orchestra Canonical Specification

The Orchestra Canonical Specification defines vendor-neutral, machine-readable, and testable contracts for AI-assisted and autonomous software engineering.

---

## Specification Documents

1. [Versioning Specification](versioning.md) (`spec/versioning.md`): Semantic versioning rules across specification, manifests, skills, workflows, and runtime interfaces.
2. [Lifecycle Specification](lifecycle.md) (`spec/lifecycle.md`): End-to-end task execution lifecycle from intake to completion verification.
3. [Compatibility Specification](compatibility.md) (`spec/compatibility.md`): Canonical abstraction layer and capability negotiation with client runtimes.
4. [Error Code Specification](errors.md) (`spec/errors.md`): Actionable, normalized error taxonomy and resolution guidelines.
5. [Security & Trust Specification](security.md) (`spec/security.md`): Threat model, permission scopes, sandboxing, and runtime guardrails.

---

## Canonical Schemas

All contracts are defined as JSON Schema Draft 2020-12 files located in `schemas/`:
- `schemas/skill-manifest.json`: Portable skill manifests
- `schemas/agent-profile.json`: Unified agent profiles
- `schemas/workflow-definition.json`: Declarative DAG workflows
- `schemas/task-contract.json`: Subagent execution briefs
- `schemas/execution-policy.json`: Security and runtime policies
- `schemas/structured-result.json`: Agent return payloads
- `schemas/verification-report.json`: Completion proof reports
- `schemas/run-record.json`: Observability & audit records
