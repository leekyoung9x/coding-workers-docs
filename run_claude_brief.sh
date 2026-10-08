#!/usr/bin/env bash
# Claude Code worker via XQ API wrapper
# Usage: bash run_claude_brief.sh /path/to/brief.md [model]
# Models: haiku (default), sonnet, opus

set -euo pipefail

BRIEF_PATH="${1:?Missing brief path}"
MODEL="${2:-haiku}"  # haiku | sonnet | opus
WRAPPER="/poki/coding-workers-docs/claude-xq-wrapper.py"

if [[ ! -f "$BRIEF_PATH" ]]; then
  echo "❌ Brief not found: $BRIEF_PATH" >&2
  exit 1
fi

if [[ ! -f "$WRAPPER" ]]; then
  echo "❌ Wrapper not found: $WRAPPER" >&2
  exit 1
fi

BRIEF_CONTENT=$(<"$BRIEF_PATH")
PROJECT_DIR=$(dirname "$BRIEF_PATH")

echo "🚀 Claude Code worker via XQ API"
echo "   Brief: $BRIEF_PATH"
echo "   Model: $MODEL"
echo "   Project: $PROJECT_DIR"
echo ""

cd "$PROJECT_DIR"

python3 "$WRAPPER" \
  -p "$BRIEF_CONTENT" \
  --model "$MODEL" \
  --output-format json \
  --dangerously-skip-permissions

echo ""
echo "✅ Claude worker completed"
