#!/usr/bin/env bash
# ==============================================================================
# Orchestra Validator
# Checks link integrity, file existence, agent modes, and token footprints.
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
    "skills/ui_ux_pro_max.md"
    "skills/graphify.md"
    "skills/understand_anything.md"
    "skills/archify.md"
    "skills/addy_osmani.md"
    "skills/ponytail.md"
    "templates/ACTIVE_TASK.md"
    "templates/ADR_TEMPLATE.md"
    "templates/EXECUTION_BRIEF.md"
    "templates/VERIFICATION_REPORT.md"
    "agents/orchestra.md"
    "agents/researcher.md"
    "agents/advisor.md"
    "agents/tester.md"
    "agents/reviewer.md"
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
echo "=== 2. Validating Agent Modes ==="
# orchestra.md must be mode: primary
if grep -q "^mode: primary" "$ROOT_DIR/agents/orchestra.md"; then
    echo "✓ agents/orchestra.md is configured as mode: primary (single entry point)"
else
    echo "❌ agents/orchestra.md must be configured as mode: primary"
    ERRORS=$((ERRORS + 1))
fi

# specialist agents must be mode: subagent
for subagent in "researcher" "advisor" "tester" "reviewer"; do
    file="$ROOT_DIR/agents/$subagent.md"
    if grep -q "^mode: subagent" "$file"; then
        echo "✓ agents/$subagent.md is configured as mode: subagent (hidden specialist)"
    else
        echo "❌ agents/$subagent.md must be configured as mode: subagent"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "=== 3. Validating Relative Links in Markdown Files ==="
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
echo "=== 4. Token Footprint & Line Counts ==="
for check_file in "AGENTS.md" "ORCHESTRATOR.md"; do
    lines=$(wc -l < "$ROOT_DIR/$check_file")
    words=$(wc -w < "$ROOT_DIR/$check_file")
    tokens=$((words * 4 / 3))
    echo "  $check_file: $lines lines, $words words (~$tokens tokens)"
    if [ "$lines" -gt 90 ]; then
        echo "  ⚠️ Warning: $check_file exceeds 90 lines target ($lines lines)"
    fi
done

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED: Orchestra structure, single-agent suite, and links are 100% valid."
    exit 0
else
    echo "❌ VALIDATION FAILED: $ERRORS errors found."
    exit 1
fi
