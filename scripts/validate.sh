#!/usr/bin/env bash
# ==============================================================================
# Orchestra Validator
# Checks link integrity, file existence, and token footprints.
# ==============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== 1. Validating Required Files ==="
REQUIRED_FILES=(
    "AGENTS.md"
    "ORCHESTRATOR.md"
    "README.md"
    "LICENSE"
    "protocols/TOKEN_ECONOMY.md"
    "protocols/ENGINEERING_STANDARDS.md"
    "protocols/SUBAGENT_DISPATCH.md"
    "skills/caveman.md"
    "skills/superpowers.md"
    "skills/impeccable.md"
    "skills/graphify.md"
    "skills/understand_anything.md"
    "skills/archify.md"
    "skills/addy_osmani.md"
    "templates/ACTIVE_TASK.md"
    "templates/ADR_TEMPLATE.md"
    "templates/EXECUTION_BRIEF.md"
    "templates/VERIFICATION_REPORT.md"
    "scripts/install.sh"
)

ERRORS=0
for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$ROOT_DIR/$f" ]; then
        echo "❌ Missing required file: $f"
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ Found: $f"
    fi
done

echo ""
echo "=== 2. Validating Relative Links in Markdown Files ==="
while IFS= read -r md_file; do
    dir=$(dirname "$md_file")
    # Match markdown links: [text](path)
    links=$(grep -oP '\]\(\K[^)#]+(?=\))' "$md_file" || true)
    for link in $links; do
        # Ignore external URLs
        if [[ "$link" =~ ^https?:// ]] || [[ "$link" =~ ^mailto: ]]; then
            continue
        fi
        target="$dir/$link"
        if [ ! -e "$target" ]; then
            echo "❌ Broken link in $md_file -> $link (resolved: $target)"
            ERRORS=$((ERRORS + 1))
        fi
    done
done < <(find "$ROOT_DIR" -name "*.md" -not -path "*/.git/*")

echo ""
echo "=== 3. Token Footprint & Line Counts ==="
for check_file in "AGENTS.md" "ORCHESTRATOR.md"; do
    lines=$(wc -l < "$ROOT_DIR/$check_file")
    words=$(wc -w < "$ROOT_DIR/$check_file")
    # rough approximation: 1 token ~ 0.75 words -> tokens ~ words * 1.33
    tokens=$((words * 4 / 3))
    echo "  $check_file: $lines lines, $words words (~$tokens tokens)"
    if [ "$lines" -gt 90 ]; then
        echo "  ⚠️ Warning: $check_file exceeds 90 lines target ($lines lines)"
    fi
done

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED: Orchestra structure, Caveman integration, and links are 100% valid."
    exit 0
else
    echo "❌ VALIDATION FAILED: $ERRORS errors found."
    exit 1
fi
