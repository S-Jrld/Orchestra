# Google Antigravity CLI Integration Guide

Orchestra integrates natively with the Google Antigravity CLI (`agy`) and Antigravity IDE environments.

## Integration Locations
- **Workspace Skills**: `.agents/skills/<skill_name>/SKILL.md`
- **Workspace Rules**: `AGENTS.md` and `.agents/rules/*.md`
- **Global Rules**: `~/.gemini/antigravity-cli/rules/ORCHESTRA_AGENTS.md`
- **Plugin Packaging**: `.agents/plugins/orchestra/plugin.json`

## Installation

Deploy Orchestra rules and portable skills for Antigravity:

```bash
# Using CLI
orch install antigravity

# Using installer script
bash scripts/install.sh antigravity
```

## Antigravity CLI Features Utilized
- **Native JSON Schema Output**: Antigravity CLI natively accepts `--json-schema` to enforce structured result contracts.
- **Headless Prompt Execution**: `agy --print --mode auto` executes deterministic steps non-interactively.
- **Sandboxed Terminals**: Antigravity CLI enforces restricted execution via `--sandbox`.
