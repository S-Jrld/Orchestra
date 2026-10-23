# Orchestra Security & Trust Model

Orchestra enforces security at runtime through least privilege, path restrictions, and approval gates.

## Security Controls

1. **Path Traversal Protection (`PathSandbox`)**:
   - Blocks path escape attempts (e.g. `../../etc/passwd`, `~/.ssh/`).
   - Ensures all file accesses stay within authorized workspace roots.

2. **Protected File Blocklist**:
   - Access to sensitive files is automatically denied:
     - `**/.git/**` (Git internals)
     - `**/.env*` (Environment files and secrets)
     - `**/id_rsa*`, `**/id_ed25519*` (SSH private keys)
     - `**/credentials*` (Cloud / API credentials)
     - `/etc/**`, `/root/**` (System files)

3. **Secret Redaction (`SecretRedactor`)**:
   - All agent briefs, execution logs, and run records are scanned with regular expressions.
   - Credentials (API keys, GitHub tokens, AWS IDs, private keys) are automatically sanitized into `[REDACTED_SECRET]`.

4. **Approval Gates**:
   - Irreversible actions (destructive deletes, external network publication) require explicit user authorization.

5. **Agent Permission Scopes**:
   - Specialist agents operate with restricted tool access:
     - `@researcher`: Read-only. Write, edit, and shell access are denied.
     - `@advisor`: Text-only design and contracts. File modifications and tools are denied.
     - `@tester`: Writes test files and runs test suites. Production code edits are denied.
     - `@reviewer`: Read-only audit. File modifications are denied.
