---
name: graphify
description: >-
  Use for deep dependency analysis, structural graphs, god-node detection,
  and logical module clustering across a codebase.
---

# /graphify (Structural Mapping & Knowledge Graph)

> Codebase structural mapping, dependency graphs, and architecture comprehension.

## Overview
- **Trigger**: New repository onboarding, large refactor planning, identifying circular dependencies, analyzing module coupling.
- **Pipeline Stage**: `Discovery & Architectural Analysis`
- **Output**: Navigable knowledge graph (`graphify-out/`), god-node identification, and `GRAPH_REPORT.md`.

## Core Capabilities
1. **God Node Detection**: Pinpoints overloaded modules and high-fan-in/high-fan-out classes.
2. **Community Detection**: Identifies logical subsystem clusters and natural module boundaries.
3. **GraphRAG Ready**: Generates structured graph JSON for retrieval-augmented generation.

## Execution
```bash
# Full graph generation on current repository
/graphify
```
