# Orchestra Deterministic Routing Engine

The Orchestra Router replaces non-deterministic LLM-based skill guessing with an auditable, deterministic scoring and ranking pipeline.

## 10-Step Resolution Pipeline

1. **Task Normalization**: Whitespace stripped, lowercased, and tokenized.
2. **Tier Inference**: Categorized into `Tiny`, `Normal`, `Complex`, or `Architectural`.
3. **Explicit Skill Extraction**: Direct references like `@superpowers` or `/caveman` are awarded 100 points.
4. **Trigger Scoring**:
   - Command triggers (`/tdd`, `/impeccable`): +50 points.
   - Exact keyword matches: +10 points per keyword.
   - Intent matches: +20 points per intent.
   - Target file pattern matches: +15 points.
5. **Deterministic Ranking**: Sorted by descending score; stable tie-breaking by alphabetical Skill ID.
6. **Single-Leaf Selection**: Only the top-ranked task skill leaf is selected per pipeline stage to avoid context bloat.
7. **Dependency Expansion**: Required dependencies are recursively expanded.
8. **Cycle Detection**: Python standard library `graphlib.TopologicalSorter` rejects circular dependencies.
9. **Conflict Resolution**: Mutually exclusive skills are pruned according to pipeline precedence.
10. **Budget Fitting**: Selections are checked against available token limits.

## Explainable Routing

Every routing decision can be inspected without running an LLM:

```bash
orch route --task "Add JWT refresh endpoint in auth/router.py" --explain
```

Output:
```text
=== Orchestra Routing Explanation ===
Task: "Add JWT refresh endpoint in auth/router.py"
Inferred Tier: Complex
Estimated Context: ~1550 tokens

Ambient Session Skills (Active across session):
  • caveman (Caveman Token Economy Engine)

Selected Task Skills:
  ✓ superpowers (Superpowers Execution Engine)
      - Matched keyword: 'add'
      - Matched keyword: 'endpoint'
```
