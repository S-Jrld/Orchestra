# 🎻 Orchestra

> **Intelligent single-agent orchestration for high-discipline software engineering and maximum token density.**

[![Validation](https://img.shields.io/badge/Orchestra-100%25%20Validated-brightgreen.svg)](#-validation--integrity-check)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tokens: 40-60% Saved](https://img.shields.io/badge/Token%20Savings-40--60%25-blueviolet.svg)](#-ambient-session-voice-caveman-engine)
[![Architecture: Single--Agent](https://img.shields.io/badge/Architecture-Single--Agent-orange.svg)](#-single-agent-architecture)

Orchestra is a lightweight, portable orchestration framework for AI-assisted and autonomous software development. It eliminates the chaos of sprawling multi-agent menus by presenting **one single primary agent (`@orchestra`)** that automatically coordinates specialized subagents, enforces rigorous engineering standards (TDD, verification proofs, server-side security, ADRs), and minimizes token usage using an ambient **Caveman token-saving engine**.

---

## 🎯 Single-Agent Architecture

Most agent setups overwhelm developers with a crowded menu of separate agents (`advisor`, `researcher`, `reviewer`, `tester`, `worker`). 

Orchestra solves this with a **Unified Single-Agent Model**:
- **You talk to only ONE primary agent (`@orchestra`, `mode: primary`)**.
- All specialist agents (`researcher`, `advisor`, `tester`, `reviewer`) are configured as internal subagents (**`mode: subagent`**)—hidden from your picker menu and orchestrated seamlessly behind the scenes.

```mermaid
flowchart TD
    User["Developer / You"] -->|"Single Conversation"| Orch["@orchestra (Primary Orchestrator)<br/>L0 Constitution + Caveman + L1 Router"]

    subgraph Subagents ["Internal Subagents (Hidden from Menu)"]
        direction TB
        Res["@researcher<br/>Code Exploration (Read-Only)"]
        Adv["@advisor<br/>Architecture & Contracts (Text-Only)"]
        Test["@tester<br/>TDD Test Runner (Tests Only)"]
        Rev["@reviewer<br/>Security & Quality Audit (Read-Only)"]
    end

    Orch -->|"1. Explore Context"| Res
    Orch -->|"2. Design Contract"| Adv
    Orch -->|"3. Write Failing Test"| Test
    Orch -->|"4. Audit Diff"| Rev

    Res -.->|"Findings"| Orch
    Adv -.->|"Schema / Spec"| Orch
    Test -.->|"Test Results"| Orch
    Rev -.->|"Audit Verdict"| Orch

    Orch -->|"Verified Minimal Diff"| User
```

---

## ⚡ Core Philosophy & Token Density

### The Token Density Equation
$$\text{Token Density} = \frac{\text{Verified Engineering Quality} \times \text{Decision Correctness}}{\text{Input Context} + \text{Reasoning Overhead} + \text{Conversational Fluff}}$$

Rather than dumping 30,000+ tokens of rules, documentation, and skill instructions into every prompt, Orchestra organizes context into **3 strictly bounded tiers**:

| Layer | Component | Context Cost | Lifecycle |
|---|---|---|---|
| **L0 Kernel** | [`AGENTS.md`](AGENTS.md) | ~500 tokens | Permanent system prompt (Includes Caveman rules) |
| **L1 Router** | [`ORCHESTRATOR.md`](ORCHESTRATOR.md) | ~400 tokens | Transient classification on task intake |
| **L2 Leaf** | [`skills/`](skills/) & [`protocols/`](protocols/) | ~600–900 tokens | Single leaf loaded strictly on demand |

### Ambient Session Voice: Caveman Engine
- **40–60% output token reduction** across all turns by stripping greetings, hedging, recaps, and pleasantries.
- Answers first, active voice, imperative grammar.
- Code blocks, terminal commands, file paths, numbers, and error traces remain **100% exact and verbatim**.
- Automatic clarity fallback for security warnings, irreversible actions, and user questions.

---

## 🚀 Quickstart (60 Seconds)

### 1. Clone & Validate
```bash
git clone https://github.com/S-Jrld/Orchestra.git
cd Orchestra
bash scripts/validate.sh
```

### 2. Install to Your Preferred Environment

#### Option A: Global OpenCode Installation (Zero-Config)
Deploys Orchestra as your default constitutional guide in OpenCode, installs `@orchestra` as your single primary agent, and sets all specialist subagents to `mode: subagent`:
```bash
./scripts/install.sh opencode
```

#### Option B: Standalone Project Installation
Deploys the kernel, router, agents, protocols, and templates directly into any project repository:
```bash
./scripts/install.sh project /path/to/my-project
```

#### Option C: Antigravity CLI / IDE Installation
Deploys Orchestra rules into the Antigravity CLI rules directory:
```bash
./scripts/install.sh antigravity
```

---

## 📖 Full Usage Guide

Once installed, Orchestra is completely hands-off. You do not need to memorize complex commands or select different subagents—**simply talk to `@orchestra` in plain English**.

### 1. Everyday Development Workflows

#### Scenario A: Adding a Feature or Fixing a Bug (TDD Loop)
Just describe what you want built:
> *"Add JWT token refresh endpoint in `auth/router.py`"*

What Orchestra does:
1. Classifies task as **`Normal`** tier.
2. Triggers [`skills/superpowers.md`](skills/superpowers.md).
3. Dispatches `@tester` to write an automated failing test (**RED**).
4. Implements the minimal code required to satisfy the contract (**GREEN**).
5. Dispatches `@reviewer` to verify no credentials, regressions, or scope creep exist.
6. Runs the automated test suite and reports verified proof.

#### Scenario B: UI & Frontend Craft
Describe your interface task:
> *"Build a responsive navigation header for mobile viewports"*

What Orchestra does:
1. Routes to [`skills/impeccable.md`](skills/impeccable.md).
2. Adheres to the 4 mandatory UI states: `Loading`, `Success`, `Error` (with retry action), and `Empty`.
3. Verifies semantic HTML, WCAG AA color contrast, and keyboard navigation.

#### Scenario C: Exploring an Unfamiliar Codebase
When joining a new project:
> *"Where do I start in this repo? What are the core models?"*

What Orchestra does:
1. Dispatches `@researcher` with read-only tools to map call trees and locate entry points.
2. Triggers [`skills/understand_anything.md`](skills/understand_anything.md) or [`skills/graphify.md`](skills/graphify.md) to generate dependency graphs and identify god-nodes.

---

### 2. Controlling the Token Economy (Caveman Commands)

Orchestra speaks in terse, high-density Caveman voice by default. You can adjust the compression level at any time using slash commands:

| Command | Mode | Description | Savings |
|---|---|---|---|
| `/caveman` | Default Terse | Active voice, fluff stripped, code verbatim. | ~40–50% |
| `/ultracave` | Extreme Density | Fragment style; each technical fact stated once. | ~60–70% |
| `/megacave` | Classical Chinese | Classical Chinese (文言文) mode for ultra-compact payloads. | ~75% |
| `stop caveman` | Full Prose | Disables Caveman voice; resumes standard conversational sentences. | Baseline |

---

### 3. Task Execution Tiers & Stop Conditions

Orchestra bounds every task with clear execution tiers and hard stop conditions:

| Tier | Scope | Required Gates | Stop Condition |
|---|---|---|---|
| **Tiny** | Typo, naming, comment, formatting | Diff re-read, scope check, clean lint | Diff clean, zero scope creep |
| **Normal** | Feature, bugfix, schema, endpoint | Red-Green TDD, regression suite pass | Suite green, behavior verified |
| **Complex** | Cross-module, auth, breaking API | Threat pass, rollback plan, scoped subagent brief | Confirmed plan, ADR logged, green tests |
| **Architectural** | Subsystem, new database, framework | Trade-off matrix, ADR approved before code | Approved ADR in `DECISIONS.md` |

---

### 4. Updating an Existing Installation

If you already cloned Orchestra and installed it to OpenCode, update to the latest release in two commands:

```bash
cd Orchestra
git pull origin main
./scripts/install.sh opencode
```

This automatically:
- Pulls latest agent updates, protocols, and skills.
- Backs up your existing configuration.
- Keeps `@orchestra` primary while ensuring all specialist agents remain set to `mode: subagent`.

---

## ⚡ Skill Routing Directory

Orchestra routes tasks between ambient session voices and domain-specialized skills on demand:

| Skill | Type | Trigger Intent | Documentation |
|---|---|---|---|
| **Caveman** | Ambient (Session) | Token saving, terse voice, zero fluff | [`skills/caveman.md`](skills/caveman.md) |
| **Superpowers** | Task-Level | Feature, bugfix, plan execution, TDD | [`skills/superpowers.md`](skills/superpowers.md) |
| **Impeccable** | Task-Level | UI components, design polish, a11y, responsive styling | [`skills/impeccable.md`](skills/impeccable.md) |
| **UI/UX Pro Max** | Task-Level | Design systems, palettes, style & font pairing, chart choice | [`skills/ui_ux_pro_max.md`](skills/ui_ux_pro_max.md) |
| **Graphify** | Task-Level | Structural graphs, dependency clusters, god nodes | [`skills/graphify.md`](skills/graphify.md) |
| **Understand Anything** | Task-Level | Codebase onboarding, visual interactive tours | [`skills/understand_anything.md`](skills/understand_anything.md) |
| **Archify** | Task-Level | Architecture diagrams, C4 models, Mermaid specs | [`skills/archify.md`](skills/archify.md) |
| **Addy Osmani** | Task-Level | Web performance, bundle optimization, Core Web Vitals | [`skills/addy_osmani.md`](skills/addy_osmani.md) |

---

## 📂 Repository Structure

```text
Orchestra/
├── bin/
│   └── orch                           # Orchestra CLI executable launcher
├── orchestra/                         # Core Python 3 Runtime (zero external dependencies)
│   ├── registry/                      # Skill discovery, deterministic scoring, conflict resolution
│   ├── context/                       # Progressive L0/L1/L2 context builder & SHA-256 cache
│   ├── workflow/                      # Declarative DAG execution engine & step scheduler
│   ├── budget/                        # Hard quota enforcement & tier profile manager
│   ├── security/                      # Path sandbox allowlist & secret redactor
│   ├── adapters/                      # Client adapters (Mock, OpenCode, Antigravity)
│   ├── models.py                      # Strongly typed dataclasses
│   └── validator.py                   # Draft 2020-12 pure-Python JSON schema validator
├── schemas/                           # Canonical Draft 2020-12 JSON schemas
│   ├── skill-manifest.json
│   ├── agent-profile.json
│   ├── workflow-definition.json
│   ├── task-contract.json
│   ├── structured-result.json
│   └── run-record.json
├── spec/                              # Formal vendor-neutral specifications
├── docs/                              # Full technical architecture & guides
├── workflows/                         # Declarative DAG workflow definitions
├── tests/                             # Automated test suite (unit, integration, adapters, benchmarks)
├── AGENTS.md                          # L0 Constitutional Kernel + Caveman (Tokens: ~500)
├── ORCHESTRATOR.md                    # L1 Task & Skill Router (Tokens: ~400)
├── README.md                          # Full guide and architecture overview
├── LICENSE                            # MIT License
├── agents/                            # Agent profiles (orchestra, researcher, advisor, tester, reviewer)
├── protocols/                         # Engineering, Token Economy & Dispatch Protocols
├── skills/                            # Portable skills (SKILL.md + manifest.json)
├── templates/                         # State tracking, ADR & Verification templates
└── scripts/
    ├── install.sh                     # Reversible deployment script with --dry-run
    └── validate.sh                    # Integrity, agent modes & token benchmark checker
```

---

## 🛠️ Orchestra CLI (`orch`)

Orchestra includes an executable CLI (`bin/orch`) for deterministic routing, workflow execution, adapter diagnostics, and benchmarking:

```bash
# Check system and adapter health
orch doctor

# Inspect and search discovered skills
orch skills list
orch skills inspect superpowers

# Explain deterministic routing for a task
orch route --task "Add JWT refresh endpoint in auth/router.py" --explain

# Validate and run declarative DAG workflows
orch workflow validate workflows/feature-tdd.json
orch workflow run workflows/feature-tdd.json

# Run token-efficiency benchmarks
orch benchmark
```

---

## 📚 Complete Documentation

- [Architecture Overview](docs/architecture.md)
- [Implementation Baseline & Audit](docs/implementation-baseline.md)
- [Canonical Specification & Schemas](docs/specification.md)
- [Skill Registry & Discovery](docs/skill-registry.md)
- [Deterministic Routing Pipeline](docs/routing.md)
- [Declarative Workflows](docs/workflows.md)
- [Context Economy & Token Density](docs/context-economy.md)
- [Budget & Cost Controls](docs/budget-management.md)
- [Security & Trust Boundaries](docs/security-model.md)
- [Client Adapters Architecture](docs/adapters.md)
- [OpenCode Integration Guide](docs/opencode.md)
- [Antigravity CLI Integration Guide](docs/antigravity-cli.md)
- [Installation & Rollback](docs/installation.md)
- [Troubleshooting & Error Codes](docs/troubleshooting.md)
- [Benchmarking Results](docs/benchmarking.md)
- [Development Roadmap](docs/roadmap.md)

---

## 🧪 Validation & Integrity Check

Orchestra includes an automated validation script that checks:
1. All required constitutional files, protocols, skills, templates, and agents exist.
2. Agent permissions (`orchestra.md` is `mode: primary`; all specialists are `mode: subagent`).
3. 100% of internal Markdown links resolve cleanly.
4. L0 and L1 token budgets remain strictly bounded.

```bash
bash scripts/validate.sh
```

---

## 📄 License

MIT © [S-Jrld](https://github.com/S-Jrld)
