# Claude Code CLI Integration Guide

Orchestra seamlessly connects with Anthropic's Claude Code CLI tool.

## Integration Structure
- **Project Memory**: `CLAUDE.md` (root memory file read on every session start)
- **Skills Directory**: `.claude/skills/`

## Deployment

Deploy Orchestra guidelines and memory for Claude Code:

```bash
# Using CLI
orch install claude

# Dry run simulation
orch install claude --dry-run
```

When deployed, Orchestra writes constitutional rules and the deterministic routing table directly into `CLAUDE.md`. Claude Code incorporates these constraints on every session initiation, ensuring TDD discipline, Caveman compression voice, and token budgets.

## Capabilities

| Capability | Supported | Notes |
|---|:---:|---|
| Multi-Agent Personas | No | Claude Code runs a single interactive CLI agent |
| Native Permission Prompt Gates | Yes | Claude Code prompts for bash & destructive edits |
| Background Jobs | Yes | Background bash execution |
| Usage & Cost Metrics | Yes | Native reporting of tokens and monetary cost |
| Structured Result Contracts | Emulated | Validated post-turn via JSON schemas |
