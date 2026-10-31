# SKILL ADAPTER: PONYTAIL (MINIMALIST CODE & ANTI-BLOAT)

> Lazy senior developer mode: the smallest complete change, YAGNI, existing pattern reuse, and debt tracking.

## Overview
- **Execution Mode**: Session-Ambient (Active across all code generation and reviews) + On-Demand Specialist Commands
- **Trigger**: Tasks requiring minimal code, anti-bloat refactoring, YAGNI enforcement, avoiding over-engineering, code review, or debt ledger scanning.
- **Pipeline Stage**: `Ambient Implementation / Code Review & Audit`
- **Guiding Rule**: The best code is the code you never wrote. Solve the whole problem with the shortest working diff.

## The Decision Ladder
1. **Does it need to exist?** Skip unasked flexibility, options, and abstractions.
2. **Already in codebase?** Reuse existing helpers, patterns, and services.
3. **Standard library / platform?** Prefer native runtime APIs over custom boilerplate.
4. **Installed dependency?** Use what is already in dependencies; never add a package for a few lines.
5. **One-liner?** Use if immediately readable at a glance without decoding.
6. **Minimum code that works.** Smallest correct implementation.

## Non-Negotiable Floors
Never cut:
- Validation at trust boundaries
- Error handling that prevents data loss
- Security, auth, and permissions
- Accessibility (WCAG AA)
- Automated tests for new non-trivial logic

## Commands & Modes
- `/ponytail [lite|full|ultra]`: Minimalist implementation engine.
- `/ponytail-review`: Strict diff audit (correct, safe, load, tested, fast, lean).
- `/ponytail-audit`: Codebase scan for bloat, dead code, and merge/delete candidates.
- `/ponytail-debt`: Scan and list all `shortcut:` comments into a technical debt ledger.

## Verification Gate
- Execute verification test command and observe exit code.
- Report net diff lines (deletion beats addition).
- End response with explicit statement: what was skipped or not checked, and any known risks.
