# Coding Workers — Hermes + 9Router / OpenRouter

Hermes đóng vai trò **Orchestrator**: quản lý session/context, giữ kết nối Discord, tích hợp Figma MCP (FULL), Unity MCP Pro (FULL), phân luồng công việc (routing), trích xuất design spec và kiểm định chất lượng cuối cùng (final verification). 

Các **Dedicated Worker CLI** sở hữu coding loop độc lập (quản lý repository, tương tác shell, build/test/lint, tự sửa lỗi biên dịch).

---

## 1. Kiến trúc Tổng thể (5 Workers)

```text
                        ┌──────────────→ Muse Code CLI (muse)
                        │                  ↓ (Responses API qua muse-shim :8787)
                        │                OpenRouter / 9Router: thtung-muse → Meta Muse Spark 1.3
                        │                (Tích hợp Unity MCP Mini: 13 tools cốt lõi)
                        │
                        ├──────────────→ mini-SWE-agent (mini)
                        │                  ↓ (OpenAI-compatible)
                        │                9Router: thtung-paid → DeepSeek V4.1 Flash
                        │
Discord → Hermes        ├──────────────→ OpenCode CLI (opencode)
 (Orchestrator) ────────┤                  ↓ (OpenAI-compatible)
                        │                9Router: thtung-glm → GLM-5.3-Flash
                        │
                        ├──────────────→ OpenAI Codex CLI (codex)
                        │                  ↓ (Responses API / HTTPS fallback)
                        │                9Router: thtung-gpt → GPT-5.6 Luna
                        │
                        └──────────────→ Antigravity CLI (agy)
                                           ↓ (Google Sign-In OAuth / thtung-agy)
                                         Google Gemini 3.8 / Claude Opus 4.6


Hermes đảm nhiệm:
- Discord Gateway & multi-turn session
- Figma MCP (FULL - 45 tools) & Unity MCP Pro (FULL - 275 tools)
- Thu thập context & phân tích yêu cầu
- Routing tác vụ & verify git diff / test suite trước khi báo cáo

Workers đảm nhiệm:
- Coding agent loop chuyên biệt (bash-centric hoặc TUI runner)
- Đọc, tìm kiếm, chỉnh sửa file trong repo
- Chạy test, build, lint, tự fix lỗi biên dịch
- Cô lập ngữ cảnh (<10k token ban đầu), tránh phình context
```

---

## 2. Danh mục Components & Workers

| Thành phần | Binary Linux VPS | Binary macOS (Apple Silicon) | Phiên bản | Mô tả & Cách đấu nối |
| :--- | :--- | :--- | :---: | :--- |
| **muse-code** skill | `~/.hermes/skills/muse-code/` | `~/.hermes/skills/autonomous-ai-agents/muse-code/` | 1.0.0 | Điều phối task khó/long-horizon cho Muse Code CLI (Reasoning: `xhigh`) |
| **codex** skill | `~/.hermes/skills/autonomous-ai-agents/codex/` | `~/.hermes/skills/autonomous-ai-agents/codex/` | 1.0.1 | Điều phối coding/review cho OpenAI Codex CLI |
| **opencode** skill | `~/.hermes/skills/glm-code/` | `~/.hermes/skills/autonomous-ai-agents/opencode/` | 1.2.0 | Điều phối tác vụ qua OpenCode CLI |
| **antigravity** skill | `~/.hermes/skills/autonomous-ai-agents/antigravity/` | `~/.hermes/skills/autonomous-ai-agents/antigravity/` | 1.0.0 | Điều phối coding cho Google Antigravity CLI (`agy`) |
| **Muse Code CLI** | `/root/.local/bin/muse` | `~/.local/bin/muse` | 1.2.1 | CLI native của Meta (kèm `unity-mini.js` 13 tools) |
| **muse-shim** | `/root/ops/muse-shim/` | `~/.local/share/muse-shim/`<br>`~/.local/bin/muse-shim` | 0.4.0 | Shim proxy loopback `:8787` ➔ Responses API |
| **mini-SWE-agent** | `/root/.local/bin/mini` | `~/.local/bin/mini` | 2.4.6 | Agent ~100 dòng Python, bash-only (DeepSeek via 9Router) |
| **OpenCode CLI** | `/usr/local/bin/opencode` | `/opt/homebrew/bin/opencode` | 1.18.31 | Agent mã nguồn mở, hỗ trợ đa provider qua `@ai-sdk` (GLM via 9Router) |
| **Codex CLI** | `/usr/local/bin/codex` | `~/.local/bin/codex` | 0.147.0 | OpenAI Codex CLI, cấu hình `~/.codex/config.toml` |
| **Antigravity CLI** | `/root/.local/bin/agy` | `~/.local/bin/agy` | 1.2.3 | Google Antigravity CLI, hỗ trợ Gemini 3.8 / Claude Opus |

---

## 3. Cấu hình Combos (9Router)

Tất cả các worker (trừ Muse Code dùng upstream OpenRouter) đều trỏ về 9Router:
- **Từ Linux VPS**: `http://127.0.0.1:20127/v1` (host) hoặc `http://172.17.0.1:20127/v1` (docker).
- **Từ macOS Workstation**: `https://router.cutes1tg.online/v1`.

| Tên Combo | Model List trong Combo | Trạng thái thực tế |
|---|---|---|
| `thtung-paid` | `xq/deepseek-v4.1-flash`, `aibox/ds/deepseek-flash` | Trả lời nhanh (~1.5s), phục vụ DeepSeek (mini-SWE) |
| `thtung-glm` | `xq/glm-5.3-flash` | Phục vụ GLM-5.3-Flash qua OpenCode (~2s) |
| `thtung-muse` | `oc/muse-spark-1.3-contributor-free` (+1.2 fallback) | Chạy chuẩn qua Responses API (muse-shim) & stream |
| `thtung-agy` | `ag/gemini-3.8-flash-high`, `omni/thtung-agy` | Active qua 2 account Google OAuth trong 9Router |
| `thtung-gpt` | `exp/gpt-5.6-luna`, `xq/gpt-5-6-luna` | Phục vụ model dòng GPT & Codex CLI (Responses API) |

---

## 4. Hướng dẫn Thực thi (Canonical Commands)

### 4.1. Trên macOS Workstation

```bash
# 1. Muse Code (Task khó, repo C# Unity, long-horizon)
META_API_KEY=local-shim-placeholder muse exec \
  --provider meta \
  --base-url http://127.0.0.1:8787 \
  --model meta/muse-spark-1.3-contributor \
  --reasoning-effort xhigh \
  --yolo \
  --workspace "/path/to/project" \
  "<yêu cầu task>"

# 2. DeepSeek (Mặc định cho tính năng nhanh, bugfix, refactor)
MSWEA_SILENT_STARTUP=1 mini --exit-immediately -m openai/thtung-paid \
  -t "<yêu cầu task>. Then echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT as its own command." -y -l 0.5

# 3. GLM Worker (Chạy qua OpenCode)
opencode run -m ninerouter/thtung-glm "<yêu cầu task>"

# 4. Codex CLI (Chạy trực tiếp qua OpenAI OAuth / 9Router)
codex exec -s workspace-write "<yêu cầu task>"

# 5. Antigravity CLI (Google Antigravity agy)
agy -p "<yêu cầu task>" --dangerously-skip-permissions
```

### 4.2. Trên Linux VPS

```bash
# 1. Muse Code
muse exec --provider meta --base-url http://127.0.0.1:8787 --model thtung-muse \
  --yolo --json "<yêu cầu task>"

# 2. mini-SWE-agent
MSWEA_SILENT_STARTUP=1 mini --exit-immediately -m openai/thtung-paid \
  -t "<yêu cầu task>. Then echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT as its own command." -y -l 0.5

# 3. OpenCode CLI
opencode run -m ninerouter/thtung-glm --format json "<yêu cầu task>"

# 4. Codex CLI
codex exec -s workspace-write "<yêu cầu task>"

# 5. Antigravity CLI
agy -p "<yêu cầu task>" --dangerously-skip-permissions
```

---

## 5. Cấu hình Chi tiết Từng Worker

### A. Codex CLI (`~/.codex/config.toml`)
```toml
model = "thtung-gpt"
model_provider = "ninerouter"

[model_providers.ninerouter]
name = "9Router"
base_url = "https://router.cutes1tg.online/v1"
wire_api = "responses"
supports_websockets = false
requires_openai_auth = true
```
*Lưu ý*: Thiết lập `supports_websockets = false` giúp Codex bỏ qua 5 lần thử websocket thất bại (tiết kiệm 7 giây khởi động mỗi lệnh) và kết nối tức thì bằng HTTPS transport.

### B. mini-SWE-agent (`~/.config/mini-swe-agent/.env`)
```bash
OPENAI_API_KEY="sk-fa5efb56e57fe4b9-drd5jf-be158103"
OPENAI_API_BASE="https://router.cutes1tg.online/v1"
LITELLM_API_KEY="sk-fa5efb56e57fe4b9-drd5jf-be158103"
LITELLM_BASE_URL="https://router.cutes1tg.online/v1"
MSWEA_CONFIGURED="true"
MSWEA_MODEL_NAME="openai/thtung-paid"
MSWEA_COST_TRACKING="ignore_errors"
MSWEA_SILENT_STARTUP="1"
```

### C. OpenCode CLI (`~/.config/opencode/opencode.json`)
```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ninerouter": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "9Router",
      "options": {
        "baseURL": "https://router.cutes1tg.online/v1",
        "apiKey": "sk-fa5efb56e57fe4b9-drd5jf-be158103"
      },
      "models": {
        "thtung-glm": { "name": "GLM-5.3-Flash", "limit": { "context": 200000, "output": 32000 } },
        "thtung-paid": { "name": "DeepSeek-V4.1-Flash", "limit": { "context": 1000000, "output": 32000 } }
      }
    }
  }
}
```

### D. Muse Code & muse-shim (macOS)
- Proxy loopback: `muse-shim generic` lắng nghe cổng `:8787`.
- Quản lý service: `muse-shim-service {start|stop|restart|status|logs}`.
- Cấu hình Unity MCP Mini (13 tools cốt lõi) tại `~/.config/muse/settings.json`.

### E. Antigravity CLI (`agy`)
- Cài đặt nhanh: `curl -fsSL https://antigravity.google/cli/install.sh | bash`.
- Binary: `~/.local/bin/agy` (v1.2.3).
- Chạy lần đầu trong terminal để hoàn tất đăng nhập Google OAuth.

---

## 6. Tài liệu Chuyên sâu & Benchmark

- 📘 **[Hướng dẫn Chi tiết Vận hành 5 Workers trên macOS & Điều phối qua Hermes (MACOS_WORKERS_GUIDE.md)](./MACOS_WORKERS_GUIDE.md)**: Ma trận phân công task, bảng lệnh headless chuẩn, feedback loop Unity MCP Mini và xử lý sự cố.
- 📊 **[Tài liệu Phương pháp & Công thức Benchmark (BENCHMARK.md)](./BENCHMARK.md)**: Hướng dẫn đo lường theo chuẩn DeepSWE (Pier runner) và Terminal-Bench (Harbor runner).
- 📈 **[Báo cáo Thực nghiệm Đối đầu: mini-SWE vs Hermes Direct & DeepSWE v1.1 (VERIFICATION_REPORT.md)](./VERIFICATION_REPORT.md)**:
  - **Single-File Bugfix**: mini-SWE hoàn thành trong **34s** (6 bước) vs Hermes mất **85s** (mini-SWE nhanh hơn 2.5 lần).
  - **Multi-File Feature**: mini-SWE hoàn thành trong **28s** (5 bước, 100% test pass) vs Hermes bị **TIMEOUT >180s** do phình context (>318k token/turn).
  - **DeepSWE v1.1**: Pass 40% (2/5 bài khó tuyệt đối), P2P 80% (không gây regression), 92.3% cache-hit rate.
