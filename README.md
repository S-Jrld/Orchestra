# Orchestra

Skill routing table for agent orchestration. Maps task types to specialized skills.

## Usage

1. Read `AGENTS.md` → `## Skill Routing` section.
2. Match task to trigger condition.
3. Load matching skill, execute, return.

## Skills

| Skill | Trigger |
|-------|---------|
| Superpowers | Feature/bugfix/plan execution |
| Caveman | Voice/format (session-level) |
| Graphify | Codebase structure/architecture |
| Understand Anything | Documentation/knowledge graph |
| Impeccable | Test fixtures |
| Archify | Diagrams/visualizations |
| Addy Osmani | Performance patterns |

## Install

```bash
git clone <repo> Orchestra
cp Orchestra/AGENTS.md ~/.config/opencode/AGENTS.md
```

## License

MIT
