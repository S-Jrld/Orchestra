#!/usr/bin/env bash
# ==============================================================================
# Orchestra Installer
# Deploys Orchestra configuration to OpenCode, Antigravity, or project roots.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
    cat <<EOF
Usage: $(basename "$0") [target] [options]

Targets:
  opencode      Install Orchestra as the global OpenCode constitution and single primary agent
  antigravity   Install Orchestra rules to ~/.gemini/antigravity-cli/ and skills to .agents/skills/
  project <dir> Install Orchestra into a specific project repository
  uninstall <opencode|antigravity>  Safely remove Orchestra configurations
  help          Show this message

Options:
  --dry-run     Simulate changes without modifying filesystem

Examples:
  ./scripts/install.sh opencode
  ./scripts/install.sh opencode --dry-run
  ./scripts/install.sh project /path/to/my-project
  ./scripts/install.sh uninstall opencode
EOF
    exit 0
}

TARGET="${1:-help}"
DRY_RUN=false
ARG2="${2:-}"
ARG3="${3:-}"

if [ "$ARG2" == "--dry-run" ] || [ "$ARG3" == "--dry-run" ] || [ "${1:-}" == "--dry-run" ]; then
    DRY_RUN=true
fi

safe_copy() {
    local src="$1"
    local dst="$2"
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] copy $src -> $dst"
    else
        cp "$src" "$dst"
    fi
}

safe_mkdir() {
    local dir="$1"
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] mkdir -p $dir"
    else
        mkdir -p "$dir"
    fi
}

case "$TARGET" in
    opencode)
        DEST_DIR="$HOME/.config/opencode"
        AGENTS_DIR="$DEST_DIR/agents"
        safe_mkdir "$DEST_DIR"
        safe_mkdir "$AGENTS_DIR"

        # 1. Back up and install constitution & router
        if [ -f "$DEST_DIR/AGENTS.md" ]; then
            BACKUP="$DEST_DIR/AGENTS.md.bak.$(date +%Y%m%d%H%M%S)"
            if [ "$DRY_RUN" = false ]; then
                cp "$DEST_DIR/AGENTS.md" "$BACKUP"
                echo "Backed up existing AGENTS.md to $BACKUP"
            else
                echo "[DRY-RUN] would backup $DEST_DIR/AGENTS.md -> $BACKUP"
            fi
        fi
        safe_copy "$SCRIPT_DIR/AGENTS.md" "$DEST_DIR/AGENTS.md"
        safe_copy "$SCRIPT_DIR/ORCHESTRATOR.md" "$DEST_DIR/ORCHESTRATOR.md"
        echo "✓ Installed AGENTS.md and ORCHESTRATOR.md to $DEST_DIR"

        # 2. Install Orchestra agent suite
        for a_file in "$SCRIPT_DIR"/agents/*.md; do
            safe_copy "$a_file" "$AGENTS_DIR/"
        done
        echo "✓ Installed Orchestra agent suite to $AGENTS_DIR"

        # 3. Demote legacy agents to mode: subagent to ensure clean UI
        if [ "$DRY_RUN" = false ]; then
            for legacy_agent in "$AGENTS_DIR"/worker.md "$AGENTS_DIR"/superpowers-orchestrator.md; do
                if [ -f "$legacy_agent" ]; then
                    sed -i 's/^mode: all/mode: subagent/' "$legacy_agent" || true
                fi
            done
        fi
        echo "✓ Ensured only @orchestra is primary; specialists set to mode: subagent."

        echo ""
        if [ "$DRY_RUN" = true ]; then
            echo "✅ Dry-run completed. No files modified."
        else
            echo "✅ Orchestra installed successfully! OpenCode now uses @orchestra as its single primary orchestrator."
        fi
        ;;

    antigravity)
        DEST_DIR="$HOME/.gemini/antigravity-cli/rules"
        safe_mkdir "$DEST_DIR"
        safe_copy "$SCRIPT_DIR/AGENTS.md" "$DEST_DIR/ORCHESTRA_AGENTS.md"
        echo "✓ Orchestra constitution copied to $DEST_DIR/ORCHESTRA_AGENTS.md."

        # Also stage workspace skills if in an active git workspace
        if [ -d "$SCRIPT_DIR/.agents/skills" ] || [ -d "$SCRIPT_DIR/.git" ]; then
            AGENTS_SKILLS="$SCRIPT_DIR/.agents/skills"
            safe_mkdir "$AGENTS_SKILLS"
            for s_dir in "$SCRIPT_DIR"/skills/*; do
                if [ -d "$s_dir" ] && [ -f "$s_dir/SKILL.md" ]; then
                    s_name=$(basename "$s_dir")
                    if [ "$DRY_RUN" = false ]; then
                        rm -rf "$AGENTS_SKILLS/$s_name"
                        cp -r "$s_dir" "$AGENTS_SKILLS/"
                    else
                        echo "[DRY-RUN] stage skill $s_name into $AGENTS_SKILLS/"
                    fi
                fi
            done
            echo "✓ Staged portable skills into $AGENTS_SKILLS."
        fi

        echo ""
        if [ "$DRY_RUN" = true ]; then
            echo "✅ Dry-run completed. No files modified."
        else
            echo "✅ Antigravity rules and skills deployed successfully."
        fi
        ;;

    project)
        PROJ_DIR="$ARG2"
        if [ -z "$PROJ_DIR" ] || [ ! -d "$PROJ_DIR" ]; then
            echo "Error: Please specify a valid project directory."
            exit 1
        fi
        safe_copy "$SCRIPT_DIR/AGENTS.md" "$PROJ_DIR/AGENTS.md"
        safe_copy "$SCRIPT_DIR/ORCHESTRATOR.md" "$PROJ_DIR/ORCHESTRATOR.md"
        safe_mkdir "$PROJ_DIR/protocols"
        safe_mkdir "$PROJ_DIR/templates"
        safe_mkdir "$PROJ_DIR/agents"
        safe_mkdir "$PROJ_DIR/.agents/skills"

        for p in "$SCRIPT_DIR"/protocols/*.md; do safe_copy "$p" "$PROJ_DIR/protocols/"; done
        for t in "$SCRIPT_DIR"/templates/*.md; do safe_copy "$t" "$PROJ_DIR/templates/"; done
        for a in "$SCRIPT_DIR"/agents/*.md; do safe_copy "$a" "$PROJ_DIR/agents/"; done

        echo ""
        if [ "$DRY_RUN" = true ]; then
            echo "✅ Dry-run completed. No files modified."
        else
            echo "✓ Orchestra deployed to project $PROJ_DIR successfully."
        fi
        ;;

    uninstall)
        SUBTARGET="$ARG2"
        if [ "$SUBTARGET" == "opencode" ]; then
            DEST_DIR="$HOME/.config/opencode"
            rm -f "$DEST_DIR/ORCHESTRATOR.md"
            echo "✓ Removed ORCHESTRATOR.md from $DEST_DIR"
            echo "✓ Note: AGENTS.md backup retained. Restoring latest backup if present..."
            LATEST_BAK=$(find "$DEST_DIR" -name "AGENTS.md.bak.*" | sort | tail -n 1 || true)
            if [ -n "$LATEST_BAK" ] && [ -f "$LATEST_BAK" ]; then
                cp "$LATEST_BAK" "$DEST_DIR/AGENTS.md"
                echo "✓ Restored original AGENTS.md from $LATEST_BAK"
            fi
            echo "✅ Uninstalled Orchestra from OpenCode."
        elif [ "$SUBTARGET" == "antigravity" ]; then
            rm -f "$HOME/.gemini/antigravity-cli/rules/ORCHESTRA_AGENTS.md"
            echo "✓ Removed $HOME/.gemini/antigravity-cli/rules/ORCHESTRA_AGENTS.md"
            echo "✅ Uninstalled Orchestra from Antigravity."
        else
            echo "Usage: $0 uninstall <opencode|antigravity>"
            exit 1
        fi
        ;;

    help|*)
        usage
        ;;
esac
