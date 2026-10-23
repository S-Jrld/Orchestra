# Orchestra Compatibility Specification

Orchestra is designed as a model-agnostic, client-agnostic orchestration layer.

## Adapter Capability Negotiation

Every client adapter must declare its capabilities explicitly:

| Capability Flag | Description | OpenCode | Antigravity CLI | Mock |
|---|---|:---:|:---:|:---:|
| `supports_subagents` | Client natively supports isolated subagents | Yes | Yes (Interactive/Subagents) | Yes |
| `supports_permissions` | Client natively enforces tool/file permissions | Yes (Agent Frontmatter) | Yes (Sandbox) | Yes |
| `supports_background` | Client supports asynchronous/background execution | Yes | Yes (Tasks) | Yes |
| `supports_structured_output` | Client natively accepts a JSON schema for output | Emulated | Yes (`--json-schema`) | Yes |
| `supports_plugins` | Client packages skills, rules, and hooks into plugins | Yes | Yes (`plugins/`) | Yes |
| `supports_usage_metrics` | Client reports exact token and cost metrics | Emulated | Partial | Yes |

## Graceful Degradation
- If a client lacks native subagent isolation, Orchestra executes specialist steps sequentially within the primary agent session using bounded prompt handoffs (`EXECUTION_BRIEF.md`).
- If a client lacks native JSON schema enforcement, Orchestra's runtime validates output post-turn against `schemas/structured-result.json` and issues a corrective prompt if malformed.
