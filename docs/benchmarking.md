# Token Economy & Efficiency Benchmarks

Orchestra is benchmarked against real-world engineering tasks to empirically measure context loading overhead and token savings.

## Benchmark Methodology

The benchmark compares two approaches:
1. **Monolithic Baseline**: All 8 domain skills, full constitution, and guidelines are dumped into one massive ~10,700-token prompt on every turn.
2. **Orchestra Progressive Context**:
   - L0 Kernel (`AGENTS.md`) permanent: ~780 tokens
   - L1 Router (`ORCHESTRATOR.md`) transient: ~580 tokens
   - L2 Targeted Leaf Skill (`SKILL.md`): ~750 tokens
   - Ambient Caveman compression saving 40-60% on conversational output.

## Empirical Benchmark Results

Measured using `./bin/orch benchmark` (Python 3.14 on Linux):

| Scenario | Inferred Tier | Baseline Tokens | Orchestra Tokens | Token Savings | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **Documentation Typo Fix** | `Tiny` | 10,728 | 2,602 | **-75.7%** | PASS |
| **Normal Feature TDD** | `Complex` | 10,728 | 2,602 | **-75.7%** | PASS |
| **Frontend Responsive UI** | `Normal` | 10,728 | 2,617 | **-75.6%** | PASS |
| **Codebase Exploration** | `Architectural` | 10,728 | 2,497 | **-76.7%** | PASS |
| **Database Query Profiling**| `Normal` | 10,728 | 2,661 | **-75.2%** | PASS |
| **Cross-Module Auth Refactor**| `Complex` | 10,728 | 2,219 | **-79.3%** | PASS |

### Summary
- **Average Token Savings**: **76.4%**
- **Decision Determinism**: 100% reproducible across all runs.
- **Verification Proof**: All scenarios met acceptance criteria and tier gates.

Run benchmarks on your own environment:
```bash
orch benchmark
# or
orch benchmark --json
```
