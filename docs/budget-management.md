# Orchestra Budget & Cost Management

Orchestra enforces hard runtime quotas on model calls, token consumption, wall-clock execution time, and parallelism.

## Task Tier Profiles

| Tier | Max Calls | Max Input Tokens | Max Output Tokens | Max Total Tokens | Timeout | Workers |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Tiny** | 3 | 2,500 | 1,000 | 3,500 | 60s | 1 |
| **Normal** | 8 | 15,000 | 4,000 | 19,000 | 300s | 2 |
| **Complex** | 20 | 50,000 | 15,000 | 65,000 | 900s | 4 |
| **Architectural** | 35 | 100,000 | 30,000 | 130,000 | 1800s | 4 |

## Enforcement Behavior
1. **Pre-Step Check**: Before dispatching a subagent step, the budget manager verifies that remaining tokens and call counts can accommodate the step.
2. **Hard Stop**: If any quota is breached, the engine halts immediately and raises `ERR_BUDGET_EXCEEDED` rather than silently continuing or consuming unapproved compute.
3. **Reconciliation**: Actual token counts reported by client adapters are recorded after each step turn.
