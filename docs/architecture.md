# Orchestra Framework Architecture

Orchestra is an AI orchestration framework built on a **4-layer decoupled architecture**, ensuring vendor-neutrality, model-agnostic execution, and zero unnecessary context overhead.

```mermaid
flowchart TD
    User["Developer / Agent Host"] --> Orch["@orchestra (Single Primary Agent)"]
    Orch --> CLI["Orchestra CLI (`orch`)"]

    subgraph LayerB ["Layer B: Orchestra Runtime Engine"]
        Registry["Skill Registry & Discovery"]
        Router["Deterministic Scoring & Tie-Breaker"]
        Context["Context Builder & SHA-256 Cache"]
        Engine["Declarative DAG Workflow Engine"]
        Budget["Budget & Cost Quota Manager"]
        Security["Least-Privilege Policy & Sandbox"]
        State["Run State & Audit Store (.orchestra/)"]
    end

    subgraph LayerA ["Layer A: Canonical Specification"]
        Schemas["Draft 2020-12 JSON Schemas"]
        Specs["Contract Specifications (`spec/`)"]
    end

    subgraph LayerC ["Layer C: Client Adapters"]
        OpenCode["OpenCode Adapter"]
        Antigravity["Antigravity CLI Adapter"]
        Mock["Mock Test Adapter"]
    end

    subgraph LayerD ["Layer D: Portable Skill Suite"]
        Skills["`skills/<id>/SKILL.md` + `manifest.json`"]
    end

    CLI --> Registry & Engine & Budget
    Registry --> Schemas & Skills
    Engine --> OpenCode & Antigravity & Mock
    Engine --> Security & State & Budget
    Context --> Skills
```

## Layer Descriptions

### Layer A: Canonical Specification (`spec/` and `schemas/`)
- Declares versioned, machine-readable contracts using JSON Schema Draft 2020-12.
- Defines contracts for Skill Manifests, Agent Profiles, Workflow Definitions, Task Contracts, Structured Results, Verification Reports, and Run Records.
- Zero dependency on proprietary vendor formats.

### Layer B: Core Runtime (`orchestra/`)
- Lightweight, pure Python 3 implementation with zero third-party package dependencies.
- Native topological sorting and cycle detection via `graphlib.TopologicalSorter`.
- Deterministic scoring, dependency resolution, progressive L0/L1/L2 context assembly, and runtime quota enforcement.

### Layer C: Client Adapters (`orchestra/adapters/`)
- Normalizes runtime interactions across client environments:
  - **OpenCode**: Manages `~/.config/opencode` agents, sets `@orchestra` to `mode: primary`, specialist subagents to `mode: subagent`.
  - **Antigravity CLI**: Manages project `.agents/skills/` and rules in `.agents/rules/`, packages plugins.
  - **Mock**: In-memory deterministic test harness.

### Layer D: Portable Skills (`skills/`)
- Follows the standard portable skill directory layout: `skills/<skill-id>/SKILL.md` accompanied by canonical `manifest.json`.
- Maintained backward-compatibility stubs for `skills/<skill-id>.md`.
