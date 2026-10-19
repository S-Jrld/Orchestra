# SUBAGENT EXECUTION BRIEF

> Copy this schema when invoking subagents or delegating sub-tasks.

```markdown
### TASK EXECUTION BRIEF
- **Subagent Role**: Researcher | Advisor | Worker | Tester | Reviewer
- **Objective**: [1 sentence describing the single goal]
- **Target Files**:
  - `path/to/file1.ext` (Inspect | Modify)
- **Contract / Interface**:
  ```[language]
  // Exact interface, schema, or function signature to adhere to
  ```
- **Verification Command**: `[Exact test or verification command, e.g. pytest tests/test_feature.py]`
- **Constraints**: [What NOT to touch, maximum line changes, forbidden libraries]
- **Stop Condition**: [Exact condition to halt and return output to parent]
```
