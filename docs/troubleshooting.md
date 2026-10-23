# Orchestra Troubleshooting & Diagnostics

Common issues, actionable error codes, and diagnostic commands.

## System Health Diagnostics

Run the doctor command to inspect prerequisites and adapter status:

```bash
orch doctor
orch adapters doctor
```

## Common Error Codes

### `ERR_SCHEMA_VALIDATION`
- **Cause**: Input JSON or manifest failed Draft 2020-12 schema validation.
- **Fix**: Run `orch skills validate` or `orch workflow validate <file>` to view exact property paths that failed.

### `ERR_SKILL_NOT_FOUND`
- **Cause**: Workflow or routing requested a skill ID not discovered on disk.
- **Fix**: Check available skills via `orch skills list`. Ensure the skill folder contains a valid `manifest.json`.

### `ERR_CYCLE_DETECTED`
- **Cause**: Circular dependency in workflow steps or skill manifests.
- **Fix**: Run `orch workflow validate <file>` to identify the cycle loop and reorder dependencies.

### `ERR_BUDGET_EXCEEDED`
- **Cause**: Active step or workflow exceeded token count, model call quota, or timeout limit.
- **Fix**: Increase budget profile in workflow definition (`budget_profile: "Complex"`) or run with larger context quota:
  ```bash
  orch route --task "..." --budget 8000
  ```

### `ERR_PERMISSION_DENIED`
- **Cause**: Step attempted to write outside authorized workspace roots or access protected files (`.git/`, `.env`, private keys).
- **Fix**: Ensure target paths are relative and inside the project root.
