# Orchestra Security & Trust Boundary Specification

Orchestra enforces security at runtime through least privilege, path restrictions, and approval gates.

## Trust Assumptions
- **Untrusted Content**: Model responses, external skill repositories, tool outputs, and user prompts are treated as untrusted inputs.
- **Prompt vs Runtime Security**: Prompts and Markdown instructions alone are not security boundaries. Actual path checks, permission masks, and process controls must be enforced by the runtime.

## Core Security Controls

1. **Path Traversal Protection**:
   - The runtime blocks path traversal attempts (e.g. `../`, `/etc/`, `~/.ssh/`).
   - Workspaces have an explicit allowlist of approved roots (`allowed_workspace_roots`).

2. **Secret Redaction**:
   - Outbound agent briefs, execution logs, and run records are scanned for API keys, private keys, bearer tokens, and credentials.
   - Matches are replaced with `[REDACTED_SECRET]`.

3. **Approval Gates**:
   - Destructive file operations (deleting directories, modifying git roots, running `rm -rf`) require an interactive or explicit approval gate.
   - Network calls to unknown endpoints require authorization.

4. **Skill Provenance Verification**:
   - Skill imports must record upstream repo, immutable git commit hash, and verified open-source license.
   - Skill scripts must be inspected before execution.
