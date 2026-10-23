# Cursor & VS Code AI Integration Guide

Orchestra provides native adapter support for Cursor IDE and VS Code AI extension environments.

## Integration Structure
- **Rules File**: `.cursor/rules/orchestra.mdc`
- **Portable Skills**: `.cursor/skills/<skill-id>/SKILL.md`
- **Workspace Config**: `.vscode/settings.json`

## Installation

Deploy Orchestra rules and portable skills for Cursor:

```bash
# Using CLI
orch install cursor

# Dry run simulation
orch install cursor --dry-run
```

When installed, Orchestra generates `.cursor/rules/orchestra.mdc` with `alwaysApply: true`, ensuring Cursor respects the Orchestra constitutional kernel (`AGENTS.md`) and routing table (`ORCHESTRATOR.md`) during every conversational and composer generation turn.

## Capabilities

| Capability | Supported | Notes |
|---|:---:|---|
| Multi-Agent Personas | Yes | Maps to specialist roles in Composer |
| Permission Sandboxing | No | Cursor runs commands in active developer terminal |
| Background Jobs | No | Synchronous turn model |
| Structured Schema Enforcement | Emulated | Post-turn schema evaluation |
| Plugin Packaging | Yes | Exportable skill bundles |
