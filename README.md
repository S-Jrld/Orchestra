# Orchestra

> Intelligent agent orchestration for high-discipline software engineering and maximum token density.

[![Validation](https://img.shields.io/badge/Orchestra-Validated-brightgreen.svg)](#validation)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Orchestra is a lightweight, portable orchestration framework for autonomous and assisted AI engineering. It couples **strict software engineering practices** (TDD, verification proofs, server-side security, ADRs) with an **aggressive token economy** powered by [Caveman](skills/caveman.md) that maximizes useful intelligence while strictly bounding prompt overhead.

---

## 🎯 Single-Agent Architecture

Unlike bloated multi-agent systems that clutter your menu with dozens of choices, Orchestra provides **ONE single primary entry agent (`@orchestra`)**. 

All specialists are configured as internal subagents (`mode: subagent`)—hidden from your menu and orchestrated behind the scenes:

```mermaid
flowchart TD
    User["Developer / You"] -->|One Conversation| Orch["@orchestra (mode: primary)\nL0 Constitution + Caveman + L1 Router"]
    
    subgraph InternalSubagents["Internal Subagents (mode: subagent — Hidden from Menu)"]
        Orch -->|Investigate (Read-Only)| Res["@researcher"]
        Orch -->|Contract & Schemas| Adv["@advisor"]
        Orch -->|TDD Red / Green| Test["@tester"]
        Orch -->|Security & Regression| Rev["@reviewer"]
    end
    
    InternalSubagents --> Orch
    Orch -->|Terse Verified Diff| User
```

---

## ⚡ Core Philosophy

### 1. The Token Density Equation
$$\text{Token Density} = \frac{\text{Verified Engineering Quality} \times \text{Decision Correctness}}{\text{Input Context} + \text{Reasoning Overhead} + \text{Conversational Fluff}}$$

Rather than stuffing 30,000 tokens of rules, documentation, and skill instructions into every prompt, Orchestra organizes context into **3 strictly bounded tiers**:

| Layer | Component | Context Cost | Lifecycle |
|---|---|---|---|
| **L0 Kernel** | [`AGENTS.md`](AGENTS.md) | ~500 tokens | Permanent system prompt (Includes Caveman) |
| **L1 Router** | [`ORCHESTRATOR.md`](ORCHESTRATOR.md) | ~400 tokens | Transient classification |
| **L2 Leaf** | [`skills/`](skills/) & [`protocols/`](protocols/) | ~600–900 tokens | Single leaf loaded on demand |

### 2. Ambient Session Voice: Caveman Engine
- **40–60% output token reduction** across all turns by stripping conversational filler, greetings, and recaps.
- Answers first, active voice, imperative grammar.
- Code blocks, terminal commands, file paths, numbers, and error traces remain 100% exact and verbatim.
- Auto-clarity fallback for security warnings, irreversible actions, and user questions.

### 3. Engineering Rigor
- **Test-Driven Development (TDD)**: Write failing test (RED), minimal implementation (GREEN), refactor.
- **Zero Unrun Claims**: Never assert that a bug is fixed or code is working without executing the test suite and recording exit codes.
- **Contract-First Truth**: Database schemas, API endpoints, and interfaces originate from verified project documents, never hallucinated.

---

## ⚡ Skill Routing Directory

Orchestra routes tasks between ambient session voices and domain-specialized skills on demand:

| Skill | Type | Trigger Intent | Documentation |
|---|---|---|---|
| **Caveman** | Ambient (Session) | Token saving, terse voice, zero fluff | [`skills/caveman.md`](skills/caveman.md) |
| **Superpowers** | Task-Level | Feature, bugfix, plan execution, TDD | [`skills/superpowers.md`](skills/superpowers.md) |
| **Impeccable** | Task-Level | UI components, design polish, a11y, responsive styling | [`skills/impeccable.md`](skills/impeccable.md) |
| **Graphify** | Task-Level | Structural graphs, dependency clusters, god nodes | [`skills/graphify.md`](skills/graphify.md) |
| **Understand Anything** | Task-Level | Codebase onboarding, visual interactive tours | [`skills/understand_anything.md`](skills/understand_anything.md) |
| **Archify** | Task-Level | Architecture diagrams, C4 models, Mermaid specs | [`skills/archify.md`](skills/archify.md) |
| **Addy Osmani** | Task-Level | Web performance, bundle optimization, Core Web Vitals | [`skills/addy_osmani.md`](skills/addy_osmani.md) |

---

## 📂 Repository Structure

```text
Orchestra/
├── AGENTS.md                          # L0 Constitutional Kernel + Caveman (Tokens: ~500)
├── ORCHESTRATOR.md                    # L1 Task & Skill Router (Tokens: ~400)
├── README.md                          # This documentation
├── LICENSE                            # MIT License
├── agents/
│   ├── orchestra.md                   # Single primary agent (mode: primary)
│   ├── researcher.md                  # Codebase discovery subagent (mode: subagent)
│   ├── advisor.md                     # Architecture & contracts subagent (mode: subagent)
│   ├── tester.md                      # TDD test-runner subagent (mode: subagent)
│   └── reviewer.md                    # Threat & quality audit subagent (mode: subagent)
├── protocols/
│   ├── TOKEN_ECONOMY.md               # Context tiering & Caveman integration
│   ├── ENGINEERING_STANDARDS.md       # TDD cycles & verification gates
│   └── SUBAGENT_DISPATCH.md           # Scoped subagent dispatch schema
├── skills/
│   ├── caveman.md                     # Token saving ambient voice engine
│   ├── superpowers.md                 # TDD & structured execution adapter
│   ├── impeccable.md                   # Frontend craft & UX adapter
│   ├── graphify.md                    # Knowledge graph adapter
│   ├── understand_anything.md         # Visual onboarding adapter
│   ├── archify.md                     # System diagramming adapter
│   └── addy_osmani.md                 # Performance optimization adapter
├── templates/
│   ├── ACTIVE_TASK.md                 # Compact active state tracker
│   ├── ADR_TEMPLATE.md                # Lightweight architectural decision record
│   ├── EXECUTION_BRIEF.md             # Subagent task handoff contract
│   └── VERIFICATION_REPORT.md         # Empirical test evidence format
└── scripts/
    ├── install.sh                     # Zero-config deployment script
    └── validate.sh                    # Link integrity, agent modes & token benchmark checker
```

---

## 🚀 Installation & Setup

### Option 1: Global OpenCode Installation (Zero-Config)
Deploys Orchestra as your default constitutional guide in OpenCode, installs `@orchestra` as your single primary agent, and sets all specialist subagents to `mode: subagent`:
```bash
./scripts/install.sh opencode
```

### Option 2: Project-Level Installation
Deploys the kernel, router, agents, protocols, and templates directly into your project repository:
```bash
./scripts/install.sh project /path/to/my-project
```

### Option 3: Antigravity CLI / IDE Installation
Deploys Orchestra rules into the Antigravity CLI environment:
```bash
./scripts/install.sh antigravity
```

---

## 🧪 Validation

Run the internal integrity validator to ensure all cross-references, agent modes, templates, and token budgets pass:
```bash
bash scripts/validate.sh
```

---

## 📄 License

MIT © [S-Jrld](https://github.com/S-Jrld)
