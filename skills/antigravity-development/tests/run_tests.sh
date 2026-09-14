#!/usr/bin/env bash
# ==============================================================================
# Test Runner for Antigravity Development Skill
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================================"
echo "🧪 Running Test Suite for Antigravity Development Skill"
echo "Skill Root: $SKILL_ROOT"
echo "========================================================"

cd "$SKILL_ROOT"

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed or not in PATH."
    exit 1
fi

echo "📋 Python Version: $(python3 --version)"

# Check agy CLI version if available
if command -v agy &> /dev/null; then
    echo "⚡ Anti-Gravity CLI: $(agy --version 2>/dev/null || echo 'Installed')"
else
    echo "⚠️ Anti-Gravity CLI ('agy') is not found in PATH."
fi

echo ""
echo "🚀 Executing Unit Tests..."
echo "--------------------------------------------------------"

python3 -m unittest discover -s "$SKILL_ROOT/tests" -p "test_*.py" -v

echo "--------------------------------------------------------"
echo "✅ All tests passed successfully!"
echo "========================================================"
