# ORCHESTRATOR

> L1 Router. Classify task type, route to the single appropriate skill/protocol leaf, execute the tier, stop. Zero domain bloat lives here.

## Session vs Task Skills

- **Session-Level (Ambient)**: [skills/caveman.md](skills/caveman.md) — Voice & token saving engine. Active across whole session.
- **Task-Level (On-Demand)**: Domain skills below. Ingested one at a time, strictly on trigger match.

---

## Task Routing Table

| Task Intent | Primary Skill / Protocol | Tier | Stop Condition |
|---|---|---|---|
| **Terse mode / less tokens** | [skills/caveman.md](skills/caveman.md) | Ambient | Caveman active, zero fluff, verbatim code |
| **Typo, comment, formatting** | [protocols/ENGINEERING_STANDARDS.md](protocols/ENGINEERING_STANDARDS.md) | Tiny | Diff re-read clean, no scope creep |
| **Feature, bugfix, logic change** | [skills/superpowers.md](skills/superpowers.md) | Normal | Red-Green TDD cycle complete, suite green |
| **UI component, layout, styling** | [skills/impeccable.md](skills/impeccable.md) | Normal | Visual hierarchy verified, a11y baseline met |
| **Design system, palette, style or font selection** | [skills/ui_ux_pro_max.md](skills/ui_ux_pro_max.md) | Normal | Verified search result: style + palette + font pairing reported |
| **Codebase discovery, onboarding** | [skills/understand_anything.md](skills/understand_anything.md) | Normal | Key modules mapped, guided tour delivered |
| **Deep dependency & structure graph**| [skills/graphify.md](skills/graphify.md) | Normal | Knowledge graph built, god-nodes reported |
| **System diagrams & C4 models** | [skills/archify.md](skills/archify.md) | Normal | Mermaid / SVG diagram validated & rendered |
| **Performance, bundle, latency fix**| [skills/addy_osmani.md](skills/addy_osmani.md) | Normal–Complex | Metrics measured before AND after; no speculative cache |
| **Cross-module refactor, auth, data**| [protocols/SUBAGENT_DISPATCH.md](protocols/SUBAGENT_DISPATCH.md) | Complex | Scoped subagent plan confirmed, threat reviewed |
| **Subsystem, framework, store change**| [protocols/ENGINEERING_STANDARDS.md](protocols/ENGINEERING_STANDARDS.md) | Architectural | ADR approved in `DECISIONS.md` before coding |

---

## Multi-Skill Conflict Resolution

When a task matches multiple domains (e.g. Fullstack Feature = Superpowers + Impeccable + Archify):
1. **Pipeline Order**:
   `Discovery (Understand Anything / Graphify) → Design / ADR → Logic TDD (Superpowers) → Design System (UI/UX Pro Max) → UI Polish (Impeccable) → Diagram (Archify) → Delivery`
2. **Never Parallel-Load Skills**: Load exactly one task skill leaf at a time corresponding to active pipeline stage. Unload / return before advancing.
3. **Ambient Caveman Floor**: [skills/caveman.md](skills/caveman.md) remains permanently active to minimize token overhead throughout every stage.

---

## Tier Escalation Triggers

Escalate tier immediately when:
- Single-file change touches public contracts or schema migrations (`Normal → Complex`).
- Reversible change becomes irreversible (data destruction, security bypass, production deploy) (`Normal → Complex`).
- Ambiguity impacts architectural boundaries or technology choices (`Complex → Architectural`).

## Router Stop Rule

No task requires loading more than `AGENTS.md` + `ORCHESTRATOR.md` + one active skill or protocol. If you need a third file simultaneously, re-classify and narrow your scope.
