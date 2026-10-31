# Orchestra Skill Registry & Discovery

The Skill Registry indexes and discovers modular skills across workspace roots and global configuration directories without loading complete instructions into model context.

## Portable Skill Layout

Skills are structured in isolated directories:

```text
skills/<skill-id>/
├── SKILL.md          # Portable instructions with YAML frontmatter
├── manifest.json     # Canonical metadata conforming to schema
├── references/       # (Optional) On-demand deep documentation
└── scripts/          # (Optional) Executable automation tools
```

## Discovered Skills Inventory

| ID | Name | Version | Kind | Summary |
|---|---|---|---|---|
| `caveman` | Caveman Token Economy Engine | 3.1.0 | `session-ambient` | Strips conversational ceremony; preserves code verbatim. |
| `superpowers` | Superpowers Execution Engine | 7.0.0 | `task-leaf` | Structured development, brainstorming, and TDD cycles. |
| `impeccable` | Impeccable UI Craft | 1.0.0 | `task-leaf` | Frontend polish, 4 UI states, and WCAG AA contrast. |
| `ui_ux_pro_max`| UI/UX Pro Max Design Intelligence | 2.15.0 | `task-leaf` | Searchable design systems, palettes, and typography. |
| `graphify` | Graphify Knowledge Graph | 1.0.0 | `task-leaf` | Structural mapping, god-node detection, community clusters. |
| `understand_anything`| Understand Anything | 1.0.0 | `task-leaf` | Codebase onboarding and visual interactive tours. |
| `archify` | Archify System Diagrams | 1.0.0 | `task-leaf` | Validated Mermaid models, sequence and C4 diagrams. |
| `addy_osmani` | Addy Osmani Performance Patterns | 0.6.13 | `task-leaf` | Bundle hygiene, DOM virtualization, and latency fixes. |
| `ponytail` | Ponytail Lazy Senior Dev Engine | 5.3.2 | `task-leaf` | Smallest complete change, YAGNI, pattern reuse, and debt tracking. |

## CLI Commands

```bash
# List all discovered skills
orch skills list

# Inspect detailed metadata for a skill
orch skills inspect superpowers

# Search skills by keyword or capability
orch skills search "responsive layout"
```
