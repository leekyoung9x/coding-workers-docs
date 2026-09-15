#!/usr/bin/env bash
# Quick smoke test for Muse Code -> muse-shim -> OpenRouter -> Muse 1.3 Contributor

set -e

PORT="${MUSE_SHIM_PORT:-8787}"
BASE_URL="http://127.0.0.1:${PORT}"

echo "=========================================="
echo "  MUSE CODE SMOKE TEST PIPELINE"
echo "=========================================="
echo "1. Checking muse-shim health at $BASE_URL/health..."
HEALTH=$(curl -s "$BASE_URL/health" || true)

if [ -z "$HEALTH" ]; then
    echo "[FAIL] muse-shim is not responding on $BASE_URL."
    echo "Please start the service first: ~/.local/bin/muse-shim-service start"
    exit 1
fi

echo "[OK] Shim is active: $HEALTH"
echo ""

echo "2. Invoking Muse Code via shim..."
echo "Model: meta/muse-spark-1.3-contributor"
echo "Prompt: 'Reply with exactly: Smoke test passed!'"
echo "------------------------------------------"

META_API_KEY=local-shim-placeholder muse exec \
  --provider meta \
  --base-url "$BASE_URL" \
  --model "meta/muse-spark-1.3-contributor" \
  --reasoning-effort xhigh \
  --yolo \
  --max-model-steps 2 \
  "Reply with exactly: Smoke test passed!"

echo ""
echo "------------------------------------------"
echo "[SUCCESS] Smoke test completed successfully!"
