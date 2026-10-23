# Orchestra Error Taxonomy & Code Dictionary

All runtime errors in Orchestra are normalized into standardized, actionable codes:

| Error Code | Category | Meaning | Recovery Action |
|---|---|---|---|
| `ERR_SCHEMA_VALIDATION` | Contract | Input JSON fails schema validation | Inspect schema failure details and correct payload structure |
| `ERR_SKILL_NOT_FOUND` | Registry | Requested skill identifier is missing | Check installed skills via `orch skills list` |
| `ERR_CYCLE_DETECTED` | Dependency | Circular dependency in skills or workflow steps | Reorder step dependencies to maintain a valid DAG |
| `ERR_CONFLICT_DETECTED` | Registry | Incompatible skills or mutually exclusive rules selected | Apply conflict resolution priority or pipeline ordering |
| `ERR_BUDGET_EXCEEDED` | Cost | Quota exhausted (tokens, calls, duration) | Escalate budget profile or request explicit authorization |
| `ERR_PERMISSION_DENIED` | Security | Task attempts forbidden file path or restricted tool | Update execution policy or obtain user approval gate |
| `ERR_STEP_TIMEOUT` | Execution | Workflow step exceeded wall-clock timeout | Retry with longer timeout or decompose step into smaller subtasks |
| `ERR_VERIFICATION_FAILED`| Quality | Verification command returned non-zero exit code | Inspect test failure output and apply fixes (TDD RED state) |
| `ERR_ADAPTER_UNAVAILABLE`| Runtime | Target client CLI or environment not installed | Run `orch doctor` to diagnose client installation paths |
