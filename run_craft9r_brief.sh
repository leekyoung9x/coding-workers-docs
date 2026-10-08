#!/usr/bin/env bash
# Worker Craft RPG via 9Router (giống mini-SWE): LLM viết world files, validate bằng craft check.
# Dùng: bash /poki/coding-workers-docs/run_craft9r_brief.sh <TÊN_BRIEF_KHÔNG_ĐUÔI.md>
# Ví dụ: CRAFT_WS=/poki/craft-worlds bash run_craft9r_brief.sh BRIEF_CRAFT_POC01
#
# Combo mặc định: openai/thtung-paid (deepseek-flash) — combo duy nhất qua 9Router
# JSON chat còn chạy ổn lúc này (thtung-muse trả content rỗng, thtung-glm 403).
# Ghi đè: CRAFT9R_MODEL=openai/thtung-paid
set -uo pipefail

NAME="${1:?thiếu tên brief}"
WS="${CRAFT_WS:-/poki/craft-worlds}"
BRIEF_DIR="${BRIEF_DIR:-$WS}"
MODEL="${CRAFT9R_MODEL:-openai/thtung-paid}"
BRIEF="$BRIEF_DIR/${NAME}.md"
LOG="$BRIEF_DIR/${NAME}.log"

[[ -f "$BRIEF" ]] || { echo "không thấy brief: $BRIEF"; exit 1; }
command -v mini >/dev/null 2>&1 || { echo "chưa cài mini-SWE-agent (uv tool install mini-swe-agent)"; exit 1; }
command -v craft >/dev/null 2>&1 || { echo "chưa cài craft CLI (npm install -g @craftrpgs/cli)"; exit 1; }

MSWEA_SILENT_STARTUP=1 mini --exit-immediately -m "$MODEL" \
  -t "$(cat "$BRIEF"). Then echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT as its own command." \
  -y -l 0.5 > "$LOG" 2>&1

echo "exit=$? brief=$NAME log=$LOG"
