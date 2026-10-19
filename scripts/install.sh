#!/usr/bin/env bash
# ==============================================================================
# Orchestra Installer
# Deploys Orchestra configuration to OpenCode, Antigravity, or project roots.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
    cat <<EOF
Usage: $(basename "$0") [target]

Targets:
  opencode      Install Orchestra as the global OpenCode constitution and single primary agent
  antigravity   Install Orchestra rules to ~/.gemini/antigravity-cli/
  project <dir> Install Orchestra into a specific project repository
  help          Show this message

Examples:
  ./scripts/install.sh opencode
  ./scripts/install.sh project /path/to/my-project
EOF
    exit 0
}

TARGET="${1:-help}"

case "$TARGET" in
    opencode)
        DEST_DIR="$HOME/.config/opencode"
        AGENTS_DIR="$DEST_DIR/agents"
        mkdir -p "$DEST_DIR" "$AGENTS_DIR"

        # 1. Back up and install constitution & router
        if [ -f "$DEST_DIR/AGENTS.md" ]; then
            BACKUP="$DEST_DIR/AGENTS.md.bak.$(date +%Y%m%d%H%M%S)"
            cp "$DEST_DIR/AGENTS.md" "$BACKUP"
            echo "Backed up existing AGENTS.md to $BACKUP"
        fi
        cp "$SCRIPT_DIR/AGENTS.md" "$DEST_DIR/AGENTS.md"
        cp "$SCRIPT_DIR/ORCHESTRATOR.md" "$DEST_DIR/ORCHESTRATOR.md"
        echo "✓ Installed AGENTS.md and ORCHESTRATOR.md to $DEST_DIR"

        # 2. Install Orchestra agent suite
        cp "$SCRIPT_DIR"/agents/*.md "$AGENTS_DIR/"
        echo "✓ Installed Orchestra agent suite to $AGENTS_DIR"

        # 3. Demote legacy agents to mode: subagent to ensure clean UI
        for legacy_agent in "$AGENTS_DIR"/worker.md "$AGENTS_DIR"/superpowers-orchestrator.md; do
            if [ -f "$legacy_agent" ]; then
                sed -i 's/^mode: all/mode: subagent/' "$legacy_agent" || true
            fi
        done
        echo "✓ Ensured only @orchestra is primary; specialists set to mode: subagent."

        echo ""
        echo "✅ Orchestra installed successfully! OpenCode now uses @orchestra as its single primary orchestrator."
        ;;
    antigravity)
        DEST_DIR="$HOME/.gemini/antigravity-cli/rules"
        mkdir -p "$DEST_DIR"
        cp "$SCRIPT_DIR/AGENTS.md" "$DEST_DIR/ORCHESTRA_AGENTS.md"
        echo "✓ Orchestra constitution copied to $DEST_DIR/ORCHESTRA_AGENTS.md."
        ;;
    project)
        PROJ_DIR="${2:-}"
        if [ -z "$PROJ_DIR" ] || [ ! -d "$PROJ_DIR" ]; then
            echo "Error: Please specify a valid project directory."
            exit 1
        fi
        cp "$SCRIPT_DIR/AGENTS.md" "$PROJ_DIR/AGENTS.md"
        cp "$SCRIPT_DIR/ORCHESTRATOR.md" "$PROJ_DIR/ORCHESTRATOR.md"
        mkdir -p "$PROJ_DIR/protocols" "$PROJ_DIR/templates" "$PROJ_DIR/agents"
        cp "$SCRIPT_DIR"/protocols/*.md "$PROJ_DIR/protocols/"
        cp "$SCRIPT_DIR"/templates/*.md "$PROJ_DIR/templates/"
        cp "$SCRIPT_DIR"/agents/*.md "$PROJ_DIR/agents/"
        echo "✓ Orchestra deployed to project $PROJ_DIR successfully."
        ;;
    help|*)
        usage
        ;;
esac
