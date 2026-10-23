# Installation, Updates, and Rollback Guide

Orchestra provides zero-config, reversible installation methods for global developer environments and project repositories.

## 1. Quickstart Installation

### Option A: Global OpenCode Installation
```bash
./bin/orch install opencode
# or
bash scripts/install.sh opencode
```

### Option B: Google Antigravity CLI Installation
```bash
./bin/orch install antigravity
# or
bash scripts/install.sh antigravity
```

### Option C: Standalone Project Installation
```bash
./bin/orch install project /path/to/my-project
# or
bash scripts/install.sh project /path/to/my-project
```

## 2. Dry-Run Verification

Test installation changes before modifying files:

```bash
./bin/orch install opencode --dry-run
# or
bash scripts/install.sh opencode --dry-run
```

## 3. Atomic Backups and Rollback

Whenever `install.sh` modifies an existing `AGENTS.md` in OpenCode, an automated timestamped backup is created:
`~/.config/opencode/AGENTS.md.bak.<TIMESTAMP>`

To uninstall and restore your previous configuration:

```bash
bash scripts/install.sh uninstall opencode
```
This safely removes Orchestra router files and restores the latest available backup of your constitution.
