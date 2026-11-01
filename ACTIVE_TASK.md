# ACTIVE TASK

> Current single-task truth. Overwrite when complete; keep under 30 lines.

## Goal
Integrate Panniantong/Agent-Reach into Orchestra: portable skill, deep-research workflow, router entry, adapter distribution, and push to GitHub.

## Classification
- **Tier**: Normal
- **Active Skill / Protocol**: [protocols/ENGINEERING_STANDARDS.md](protocols/ENGINEERING_STANDARDS.md), [protocols/SUBAGENT_DISPATCH.md](protocols/SUBAGENT_DISPATCH.md)
- **Activated Roles**: Lead Architect → Integration Developer

## Scope & Target Files
- `skills/agent_reach/`: Manifest and SKILL.md
- `skills/agent_reach.md`: Root skill adapter
- `workflows/deep-research.json`: External intelligence workflow
- `ORCHESTRATOR.md`: Routing entry
- `scripts/validate.sh`: Integrity checklist
- Git remote: Push to GitHub repository

## Checklist
- [x] 1. Create portable `agent_reach` skill (`manifest.json`, `SKILL.md`, `skills/agent_reach.md`)
- [x] 2. Create `workflows/deep-research.json`
- [x] 3. Update `ORCHESTRATOR.md` and `scripts/validate.sh`
- [x] 4. Install skill for Antigravity adapter
- [x] 5. Run test suites and repository validation (71/71 green, 100% validate.sh clean)
- [ ] 6. Commit and push changes to GitHub repository

## Blockers & Open Decisions
- None
