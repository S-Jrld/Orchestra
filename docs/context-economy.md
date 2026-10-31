# Orchestra Context Economy & Token Density

Orchestra eliminates context bloat by organizing knowledge into **strictly bounded progressive tiers**.

## The 4 Context Layers

| Layer | Component | Life Cycle | Approximate Size | Contents |
|---|---|---|---|---|
| **L0 Kernel** | [`AGENTS.md`](../AGENTS.md) | Permanent | ~850 tokens | Operating principles, security rules, Caveman voice + Ponytail code engines |
| **L1 Router** | [`ORCHESTRATOR.md`](../ORCHESTRATOR.md) | Transient (Intake) | ~580 tokens | Classification rules, tier triggers, pipeline order |
| **L2 Leaf** | `skills/<id>/SKILL.md` | Active Step Only | ~600–900 tokens | Single domain skill loaded strictly on demand |
| **L3 Evidence** | Files & Artifacts | Stored on disk | Compact refs | Plans, ADRs, test reports, and verification evidence |

## The Single-Leaf Rule
> **Never load multiple Layer 2 task leaves simultaneously.**  
When transitioning stages (e.g. from Exploration to Implementation), unload or return from the previous skill before loading the next.

## Ambient Session Voice: Caveman Engine
- Cuts conversational ceremony: eliminates greetings, hedging, polite filler, recaps, and decorative closers.
- Preserves technical payload verbatim: code blocks, terminal commands, file paths, numbers, and error traces never change.
- Automatic clarity fallback for security warnings, destructive actions, and user questions.
- Produces **40% to 60% output token savings**.

## Ambient Code Quality: Ponytail Engine
- Solves tasks with the shortest working diff while preserving correctness, security, and stability.
- Enforces the 6-step Smallest Complete Change Ladder: YAGNI → Codebase reuse → Stdlib/runtime → Installed dep → Clean one-liner → Minimum code.
- Non-negotiable floors: never cut validation at boundaries, error handling, security/auth, a11y, or tests.
- Shortcut debt ledger: intentional trade-offs commented with `shortcut: <limit>, <upgrade condition>`.
- Yields **53% code reduction, 45% tokens saved, 98% test coverage** for risky logic without speculative bloat.

## Deterministic Caching
- Intermediate parsing results, manifests, and file digests are cached in `.orchestra/` using SHA-256 fingerprints.
- Any change to source files automatically invalidates stale entries.
