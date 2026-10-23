# OpenCode Integration Guide

Orchestra seamlessly deploys into OpenCode, establishing `@orchestra` as your single primary agent while orchestrating specialist subagents behind the scenes.

## Configuration Paths
- Configuration Root: `~/.config/opencode/`
- Constitutional Guide: `~/.config/opencode/AGENTS.md`
- Task Router: `~/.config/opencode/ORCHESTRATOR.md`
- Agents Directory: `~/.config/opencode/agents/`
- Skills Directory: `~/.config/opencode/skills/`

## Deployment

Deploy Orchestra to OpenCode using the installer or CLI:

```bash
# Using CLI
orch install opencode

# Using bash installer with dry-run
bash scripts/install.sh opencode --dry-run

# Live installation
bash scripts/install.sh opencode
```

## Agent Suite in OpenCode

| Agent File | Role | Configured Mode | Visibility |
|---|---|:---:|:---:|
| `agents/orchestra.md` | Primary Orchestrator | `mode: primary` | Visible in UI picker |
| `agents/researcher.md`| Codebase Exploration | `mode: subagent` | Hidden internal worker |
| `agents/advisor.md`   | Contract Design | `mode: subagent` | Hidden internal worker |
| `agents/tester.md`    | TDD Red/Green Cycles | `mode: subagent` | Hidden internal worker |
| `agents/reviewer.md`  | Threat & Scope Audit | `mode: subagent` | Hidden internal worker |

Legacy agents (such as `worker.md` or `superpowers-orchestrator.md`) are automatically demoted to `mode: subagent` to keep your picker menu clean.
