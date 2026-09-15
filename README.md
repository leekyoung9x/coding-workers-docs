# Coding Workers — Hermes + 9Router

Hermes đóng vai trò Orchestrator: quản lý session/context, giữ kết nối Discord, tích hợp Figma MCP FULL, Unity MCP Pro FULL, phân luồng công việc (routing) và kiểm định chất lượng cuối cùng (final verification). 

Các Dedicated Worker CLI sở hữu coding loop độc lập (quản lý repository, tương tác shell, build/test/lint).

---

## 1. Kiến trúc Tổng thể (5 Workers)

```text
                        ┌──────────────→ Muse Code CLI (muse)
                        │                  ↓ (Responses API qua muse-shim :8787)
                        │                9Router: thtung-muse → Meta Muse Spark 1.3
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
                        │                9Router: thtung-paid / OpenAI models
                        │
                        └──────────────→ Antigravity CLI (agy)
                                           ↓ (Google Sign-In OAuth / thtung-agy)
                                         Google Gemini 3.8 / Claude Opus 4.6


Hermes đảm nhiệm:
- Discord Gateway & multi-turn session
- Figma MCP (FULL) & Unity MCP Pro (FULL)
- Thu thập context & phân tích yêu cầu
- Routing tác vụ & verify git diff / test suite trước khi báo cáo

Workers đảm nhiệm:
- Coding agent loop chuyên biệt (bash-centric hoặc TUI runner)
- Đọc, tìm kiếm, chỉnh sửa file trong repo
- Chạy test, build, lint, tự fix lỗi
- Cô lập ngữ cảnh (<10k token ban đầu), tránh phình context
```

---

## 2. Danh mục Components & Workers

| Thành phần | Binary / Đường dẫn | Phiên bản | Mô tả & Cách đấu nối |
|---|---|:---:|---|
| **muse-code** skill | `~/.hermes/skills/muse-code/` | 0.1.0 | Ủy quyền task khó/long-horizon cho Muse Code CLI |
| **deepseek-code** skill | `~/.hermes/skills/deepseek-code/` | 0.1.0 | Worker mặc định cho feature/bugfix thường via mini-SWE |
| **glm-code** skill | `~/.hermes/skills/glm-code/` | 0.1.0 | Worker cho các luồng GLM qua OpenCode CLI |
| **codex** skill | `~/.hermes/skills/autonomous-ai-agents/codex/` | 1.0.1 | Ủy quyền coding/review cho OpenAI Codex CLI |
| **antigravity** skill | `~/.hermes/skills/autonomous-ai-agents/antigravity/` | 1.0.0 | Ủy quyền coding cho Google Antigravity CLI (`agy`) |
| **Muse Code CLI** | `/root/.local/bin/muse` | 1.2.1 | CLI native của Meta |
| **muse-shim** | `/root/ops/muse-shim/` (systemd: `muse-shim`) | - | Shim proxy loopback `:8787` -> 9Router `/v1/responses` |
| **mini-SWE-agent** | `/root/.local/bin/mini` (uv tool) | 2.4.6 | Agent ~100 dòng Python, bash-only, LiteLLM bên trong |
| **OpenCode CLI** | `/usr/local/bin/opencode` (npm global) | 1.18.31 | Agent mã nguồn mở, hỗ trợ đa provider qua `@ai-sdk` |
| **Codex CLI** | `/usr/local/bin/codex` (npm global) | 0.154.0 | OpenAI Codex CLI, cấu hình `~/.codex/config.toml` |
| **Antigravity CLI** | `/root/.local/bin/agy` (native binary) | 1.2.3 | Google Antigravity CLI, hỗ trợ Gemini 3.8 / Claude Opus |

---

## 3. Cấu hình Combos (9Router)

Tất cả các worker đều trỏ về 9Router local (`http://127.0.0.1:20127/v1` trên host hoặc `http://172.17.0.1:20127/v1` từ Docker container):

| Tên Combo | Model List trong Combo | Trạng thái thực tế |
|---|---|---|
| `thtung-muse` | `oc/muse-spark-1.3-contributor-free` (+1.2 fallback) | Chạy chuẩn qua Responses API (muse-shim) & stream |
| `thtung-paid` | `xq/deepseek-v4.1-flash`, `aibox/ds/deepseek-flash` | Trả lời nhanh (~1.5s), phục vụ DeepSeek & Codex |
| `thtung-glm` | `xq/glm-5.3-flash` (dự phòng aibox chết 503) | Phục vụ GLM-5.3-Flash qua OpenCode (~10s) |
| `thtung-agy` | `ag/gemini-3.8-flash-high`, `omni/thtung-agy` | Active qua 2 account Google OAuth trong 9Router |
| `thtung-gpt` | `exp/gpt-5.6-luna`, `xq/gpt-5-6-luna` | Phục vụ model dòng GPT |

---

## 4. Hướng dẫn Thực thi (Canonical Commands)

```bash
# 1. Muse Code (Task khó, repo lớn, long-horizon)
muse exec --provider meta --base-url http://127.0.0.1:8787 --model thtung-muse \
  --yolo --json "<yêu cầu task>"

# 2. DeepSeek (Mặc định cho tính năng, bugfix, refactor)
MSWEA_SILENT_STARTUP=1 mini --exit-immediately -m openai/thtung-paid \
  -t "<yêu cầu task>. Then echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT as its own command." -y -l 0.5

# 3. GLM Worker (Chạy qua OpenCode)
opencode run -m ninerouter/thtung-glm --format json "<yêu cầu task>"

# 4. Codex CLI (Chạy trực tiếp qua 9Router Responses API)
codex exec -s workspace-write "<yêu cầu task>"

# 5. Antigravity CLI (Google Antigravity agy)
agy -p "<yêu cầu task>" --dangerously-skip-permissions
```

---

## 5. Cấu hình Chi tiết Từng Worker

### A. Codex CLI (`~/.codex/config.toml`)
```toml
model = "thtung-paid"
model_provider = "ninerouter"

[model_providers.ninerouter]
name = "9Router Local"
base_url = "http://127.0.0.1:20127/v1"
wire_api = "responses"
supports_websockets = false
requires_openai_auth = true
```
*Lưu ý*: Thiết lập `supports_websockets = false` giúp Codex bỏ qua 5 lần thử websocket thất bại (tiết kiệm 7 giây khởi động mỗi lệnh) và kết nối tức thì bằng HTTPS transport.

### B. mini-SWE-agent (`/root/.config/mini-swe-agent/.env`)
```bash
LITELLM_API_KEY="<9Router_Key>"
LITELLM_BASE_URL="http://127.0.0.1:20127/v1"
MSWEA_CONFIGURED="true"
MSWEA_MODEL_NAME="openai/thtung-paid"
OPENAI_API_KEY="<9Router_Key>"
OPENAI_API_BASE="http://127.0.0.1:20127/v1"
MSWEA_COST_TRACKING="ignore_errors"
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
        "baseURL": "http://127.0.0.1:20127/v1",
        "apiKey": "<9Router_Key>"
      },
      "models": {
        "thtung-glm": { "name": "GLM combo", "limit": { "context": 200000, "output": 32000 } },
        "thtung-paid": { "name": "DeepSeek combo", "limit": { "context": 200000, "output": 32000 } },
        "thtung-muse": { "name": "Muse combo", "limit": { "context": 200000, "output": 32000 } }
      }
    }
  }
}
```

### D. Muse Code Shim Service (`systemd`)
- Service: `systemctl status muse-shim`
- Runner script: `/root/ops/muse-shim/run-shim.sh` tự đọc live key từ SQLite `apiKeys`.
- Endpoint test: `curl http://127.0.0.1:8787/health` trả về `{"ok":true,"service":"muse-shim"}`.

### E. Antigravity CLI (`agy`)
- Binary: `/root/.local/bin/agy` (v1.2.3).
- Để đăng nhập lần đầu trên VPS headless: chạy với biến `SSH_CONNECTION="1.1.1.1 1234 2.2.2.2 22" agy -p "hi"`, CLI sẽ in link Google OAuth URL để mở trình duyệt cấp quyền.

---

## 6. Lịch sử Kiểm nghiệm & Benchmark

- 📊 **[Tài liệu Phương pháp & Công thức Benchmark (BENCHMARK.md)](./BENCHMARK.md)**: Hướng dẫn đo lường theo chuẩn DeepSWE (Pier runner) và Terminal-Bench (Harbor runner).
- 📈 **[Báo cáo Thực nghiệm Đối đầu: mini-SWE vs Hermes Direct & DeepSWE v1.1 (VERIFICATION_REPORT.md)](./VERIFICATION_REPORT.md)**:
  - **Single-File Bugfix**: mini-SWE hoàn thành trong **34s** (6 bước) vs Hermes mất **85s** (mini-SWE nhanh hơn 2.5 lần).
  - **Multi-File Feature**: mini-SWE hoàn thành trong **28s** (5 bước, 100% test pass) vs Hermes bị **TIMEOUT >180s** do phình context (>318k token/turn).
  - **DeepSWE v1.1**: Pass 40% (2/5 bài khó tuyệt đối), P2P 80% (không gây regression), 92.3% cache-hit rate.
