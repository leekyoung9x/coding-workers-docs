# Coding Workers — Hermes + 9Router / OpenRouter

## Đánh giá công cụ theo vai trò

- [Đánh giá 30 Skills / MCP / CLI cho Lead & Workers](plans/SKILLS_MCP_CLI_ROLE_EVALUATION.md) — đánh giá từng mục, phân quyền, kế hoạch pilot và bản gốc người dùng cung cấp. Đây là đề xuất, không phải danh sách đã cài đặt.

Hermes đóng vai trò **Orchestrator**: quản lý session/context, giữ kết nối Discord, tích hợp Figma MCP (FULL), Unity MCP Pro (FULL), phân luồng công việc (routing), trích xuất design spec và kiểm định chất lượng cuối cùng (final verification). 

Các **Dedicated Worker CLI** sở hữu coding loop độc lập (quản lý repository, tương tác shell, build/test/lint, tự sửa lỗi biên dịch).

---

## 1. Kiến trúc Tổng thể (8 Workers)

```text
                        ┌──────────────→ Muse Code CLI (muse)
                        │                  ↓ (Responses API qua muse-shim :8787 / Meta OAuth)
                        │                thtung-muse → Meta Muse Spark 1.3-contributor
                        │                (Tích hợp Unity MCP Mini: 13 tools cốt lõi)
                        │
                        ├──────────────→ DeepSeek Harness CLI (dsh)
                        │                  ↓ (Anthropic Messages API streaming)
                        │                9Router: thtung-paid → DeepSeek V4.1 Flash
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
                        ├──────────────→ Claude Code CLI (claude)
                        │                  ↓ (Messages API qua XQ API wrapper)
                        │                XQ API: Claude Sonnet 4.6 / Opus 4.6 / Haiku 5.5
                        │
                        └──────────────→ Antigravity CLI (agy)
                                           ↓ (Google Sign-In OAuth / thtung-agy)
                                         Google Gemini 3.8 / Claude Opus 4.6


Hermes đảm nhiệm (LEAD ORCHESTRATOR ONLY - KHÔNG làm việc của Dev):
- Discord Gateway & multi-turn session
- Figma MCP (FULL - 45 tools) & Unity MCP Pro (FULL - 275 tools)
- Thu thập context & phân tích nguyên nhân gốc rễ (Root Cause Recon)
- Soạn Implementation Plan & Numbered Brief chi tiết
- Giám sát tiến trình (Watchdog: Chống treo, kẹt loop, xử lý lỗi hạn mức quota/429)
- Tiếp nhận phản biện kỹ thuật từ Worker & thống nhất phương án (Final Consensus)
- Nghiệm thu độc lập kết quả đầu ra (đo lại số thật, đối chứng baseline)

Workers đảm nhiệm (100% THI CÔNG & TEST OWNERSHIP):
- Review & phản biện lại kế hoạch với Lead trước khi sửa code
- Đọc, tìm kiếm, chỉnh sửa code trong repo (100% việc dev)
- Tự viết testcase (cả regression spec đo số thật, cấm chỉ đo biến cờ)
- Tự chạy testcase (chu trình RED ➔ GREEN ➔ REFACTOR: Đỏ trước khi sửa)
- Tự build, lint, sửa lỗi biên dịch trong workspace
- Cô lập ngữ cảnh (<10k token ban đầu), tránh phình context
```

---

## 1.1. Ma Trận Thế Mạnh & Tiêu Chí Lựa Chọn Từng Worker (Strength & Routing Matrix)

Mỗi worker được tối ưu hóa cho các nhóm tác vụ và ngữ cảnh chuyên biệt:

| Worker | Model / Combo | Thế mạnh vượt trội (Mạnh về cái gì) | Điểm yếu / Lưu ý | Khi nào Lead nên chọn |
|---|---|---|---|---|
| **Muse Code** (`muse`) | `muse-spark-1.3-contributor` (Meta OAuth) | **Bố cục công thái học (HUD UX) khoa học, mượt mà (59.9 FPS) & Tự phát hiện lỗi logic sâu**. Action Bar 6 ô trực quan đếm cooldown; tạo hình Tu Sĩ nón lá truyền thống Việt Nam; tự bắt lỗi ticker game loop ghi đè BGM khi vào Endless Mode; frame rate cao nhất (59.9 FPS headless); bundle JS gọn (366.3 kB); suy luận sâu (`reasoning-effort medium/xhigh`), Unity MCP. | Phụ thuộc hạn mức tài khoản Meta, bắt buộc khóa cứng model `muse-spark-1.3-contributor` và cờ `--yolo` để không bị kẹt hàng đợi duyệt lệnh headless. | Xây dựng game/app cần vòng lặp frame mượt mà (60 FPS), thiết kế HUD/Action Bar công thái học, C# Clean Architecture hoặc xử lý lỗi tương tác logic phức tạp. |
| **DeepSeek Harness** (`dsh`) | DeepSeek V4.1 Flash (`thtung-paid`) | **Khả năng tự gỡ lỗi (Self-healing) & Kỷ luật test cực cao**. Tự viết script `.dbg.mjs` chẩn đoán lỗi sâu trong core/DOM/audio; test suite Vitest mock sạch chạy siêu tốc (1.02s / 146 tests); UI Master-Detail và vector silhouette hoàn thiện không lỗi layout; đóng gói CI/CD 1 lệnh (`npm run verify`). | Tốn nhiều bước suy luận (thích lặp lại kiểm tra, 826 steps / 5 phase), bundle JS lớn hơn (~500 kB), cần stopping bounds rõ ràng trong brief. | Xây dựng engine lõi, logic phức tạp, UI thương mại không tì vết, cần test suite đồ sộ chạy CI siêu tốc. |
| **mini-SWE-agent** (`mini`) | DeepSeek V4.1 Flash (`thtung-paid`) | **Tốc độ thực thi chớp nhoáng & Siêu tiết kiệm token/bước**. Hoàn thành task ít hơn 30–40% số bước (564 steps / 5 phase); bundle production cực kỳ gọn nhẹ (~434 kB); mỹ thuật chữ Hán thư pháp sáng tạo; văn phong bản địa hóa tu chân kèm chú thích công thái học (`(Restart)`, `(Về Menu)`). | Tự chủ môi trường yếu hơn (dễ lạc workspace sang `/tmp` nếu không khóa `cd "$WS"`), chạy test Vitest chậm (19s do mock/warnings), dễ sót lỗi layout CSS nhỏ. | Triển khai tính năng nhanh, bugfix gọn (20–34s), task song song số lượng lớn (bulk/parallel), tối ưu bundle nhẹ cho web/mobile. |
| **OpenCode** (`opencode`) | GLM-5.3-Flash (`thtung-glm`) | **Vô địch tối ưu Bundle JS (344.6 kB), Tốc độ mô phỏng cực hạn (0.0139 ms/step) & Test E2E đồ sộ**. Dùng cơ chế zero-allocation in-place compaction (`compactInPlace`); bộ test Playwright sâu nhất (23 tests bao quát đa dạng kịch bản); token rẻ nhất qua 9Router. | Cần cấu hình cờ `--variant minimal` để tránh bẫy suy nghĩ quá sâu làm cạn trần 32.000 output tokens của GLM 5.3. | Frontend / Web Game khắt khe về bundle (<350 kB), thuật toán toán học/mô phỏng tải nặng cần Zero-GC, hoặc viết test E2E chuyên sâu. |
| **Antigravity** (`agy`) | Gemini 3.8 Flash (`thtung-agy`) | **Thẩm mỹ UI/UX hiện đại đẳng cấp commercial indie & Đồ họa chiến đấu bóng bẩy**. Container translucent glass bo góc mượt mà; vòng radar/trận pháp Bát Quái phân tầng hiển thị tầm đánh tự động; đạn đạo neon phát sáng; context 1M+ tokens; tự động xoay tua 3 tài khoản Google OAuth chống 429. | CLI yêu cầu xác thực Google OAuth native; số lượng unit test ở mức cô đọng theo brief (51 tests) thay vì viết dày đặc. | Giao diện thương mại hiện đại, đồ họa chiến đấu trực quan, rà soát/refactor codebase đồ sộ hoặc tác vụ đa phương thức (ảnh/video). |
| **Claude Code** (`claude`) | DeepSeek V4.1 Flash (`thtung-paid` qua 9Router Anthropic API) | **Vô địch tuyệt đối về độ phủ kiểm thử (284 unit tests, 60 E2E tests) & Tự chẩn đoán sâu**. Tự phát hiện và sửa lệch sprite hitbox formula, tự thêm texture quái triệu hồi chống crash ticker, tạo cơ chế "boss arena" dọn quái thường để đòn đánh không bị loãng; thời gian step 0.266 ms; pass trọn vẹn 18/18 gates. | Cần cờ `IS_SANDBOX=1` để bypass root check; thời gian chạy bộ test đồ sộ kéo dài hơn các worker khác. | Dự án quy mô lớn đòi hỏi kiểm thử bao quát tối đa (Regression Safety), tự tìm và sửa các lỗi boundary conditions sâu. |
| **Kimi Code** (`kimi`) | Kimi K3 (`thtung-kimi` qua 9Router OpenAI API) | **Kỷ luật quản lý tác vụ (TodoList) xuất sắc & Thuật toán mô phỏng siêu tốc (0.038 ms/step)**. Tự quản lý danh mục tác vụ qua TodoList tool; 180 unit tests + 20 E2E tests pass 100%; giao diện Flat Card thanh thoát; hiển thị lượng máu trực tiếp và thanh máu phụ trên đầu nhân vật. | Nhạy cảm với timeout khi hệ thống chịu tải cao; cần cấu hình chuẩn `config.toml` trỏ về loopback 9Router. | Chia nhỏ task nhiều bước theo quy trình TodoList chặt chẽ, tối ưu thuật toán game/mô phỏng tải nặng, giao diện thẻ tinh tế. |
| **OpenAI Codex** (`codex`) | DeepSeek V4.1 Flash (`thtung-paid` qua 9Router Responses API) | **Tự chủ shell cao độ & Tính toán cân bằng toán học chính xác (Endless Scaling)**. Tự tính toán và debug công thức scale quái vật lũy tiến trong Endless Mode; 128 unit tests + 22 Playwright tests pass 100%; bundle JS rất gọn (381.5 kB); tốc độ step 0.138 ms. | Dễ tràn ngữ cảnh nếu nạp ảnh chụp màn hình thô (cần prompt chỉ thị cấm nạp base64 image vào context). | Tự chủ dòng lệnh shell, triển khai các thuật toán cân bằng chỉ số toán học lũy tiến (Endless scaling) và giữ kích thước bundle tối giản. |


---

## 2. Danh mục Components & Workers

| Thành phần | Binary Linux VPS | Binary macOS (Apple Silicon) | Phiên bản | Mô tả & Cách đấu nối |
| :--- | :--- | :--- | :---: | :--- |
| **muse-code** skill | `~/.hermes/skills/muse-code/` | `~/.hermes/skills/autonomous-ai-agents/muse-code/` | 1.0.0 | Điều phối task khó/long-horizon cho Muse Code CLI (Reasoning: `xhigh`) |
| **codex** skill | `~/.hermes/skills/autonomous-ai-agents/codex/` | `~/.hermes/skills/autonomous-ai-agents/codex/` | 1.0.1 | Điều phối coding/review cho OpenAI Codex CLI |
| **opencode** skill | `~/.hermes/skills/glm-code/` | `~/.hermes/skills/autonomous-ai-agents/opencode/` | 1.2.0 | Điều phối tác vụ qua OpenCode CLI |
| **claude-code** skill | `~/.hermes/skills/autonomous-ai-agents/claude-code/` | `~/.hermes/skills/autonomous-ai-agents/claude-code/` | 2.2.1 | Điều phối coding/PR review cho Claude Code CLI (Anthropic) |
| **antigravity** skill | `~/.hermes/skills/autonomous-ai-agents/antigravity/` | `~/.hermes/skills/autonomous-ai-agents/antigravity/` | 1.0.0 | Điều phối coding cho Google Antigravity CLI (`agy`) |
| **Muse Code CLI** | `/root/.local/bin/muse` | `~/.local/bin/muse` | 1.4.2 | CLI native của Meta (kèm `unity-mini.js` 13 tools) |
| **muse-shim** | `/root/ops/muse-shim/` | `~/.local/share/muse-shim/`<br>`~/.local/bin/muse-shim` | 0.4.0 | Shim proxy loopback `:8787` ➔ Responses API |
| **mini-SWE-agent** | `/root/.local/bin/mini` | `~/.local/bin/mini` | 2.4.6 | Agent ~100 dòng Python, bash-only (DeepSeek via 9Router) |
| **DeepSeek Harness** (`dsh`) | `/usr/local/bin/dsh` | `dsh` (npm `@deepseek-ai/dsh`) | 0.2.1-rc.2 | Agent của DeepSeek, chạy headless qua Anthropic streaming SSE (`thtung-paid`) |
| **OpenCode CLI** | `/usr/local/bin/opencode` | `/opt/homebrew/bin/opencode` | 1.18.31 | Agent mã nguồn mở, hỗ trợ đa provider qua `@ai-sdk` (GLM via 9Router) |
| **Codex CLI** | `/usr/local/bin/codex` | `~/.local/bin/codex` | 0.147.0 | OpenAI Codex CLI, cấu hình `~/.codex/config.toml` |
| **Claude Code CLI** | `/usr/local/bin/claude` | `/usr/local/bin/claude` | 2.1.295 | Anthropic Claude Code CLI (gọi qua wrapper XQ, không dùng key Anthropic) |
| **claude-xq-wrapper** | `/poki/coding-workers-docs/claude-xq-wrapper.py` | N/A | 1.0.1 | Python wrapper gọi XQ API (key từ env/file, limit ~80K tokens) |
| **Antigravity CLI** | `/root/.local/bin/agy` | `~/.local/bin/agy` | 1.2.3 | Google Antigravity CLI, hỗ trợ Gemini 3.8 / Claude Opus |
| **Kimi Code CLI** | `/root/.kimi-code/` (global npm) | `kimi` (npm `@moonshot-ai/kimi-code`) | 2.3.0 | CLI tự chủ của Moonshot AI, hỗ trợ Kimi K3 qua OpenAI provider |

---

## 3. Cấu hình Combos (9Router)

Tất cả các worker (trừ Muse Code dùng upstream OpenRouter) đều trỏ về 9Router:
- **Từ Linux VPS**: `http://127.0.0.1:20127/v1` (host) hoặc `http://172.17.0.1:20127/v1` (docker).
- **Từ macOS Workstation**: `https://router.cutes1tg.online/v1`.

| Tên Combo | Model List trong Combo | Trạng thái thực tế |
|---|---|---|
| `thtung-paid` | `xq/deepseek-v4.1-flash`, `aibox/ds/deepseek-flash` | Trả lời nhanh (~1.5s), phục vụ DeepSeek (`mini-SWE` & `dsh`) |
| `thtung-glm` | `xq/glm-5.3-flash` | Phục vụ GLM-5.3-Flash qua OpenCode (~2s) |
| `thtung-muse` | `oc/muse-spark-1.3-contributor-free` (+1.2 fallback) | Chạy chuẩn qua Responses API (muse-shim) & stream |
| `thtung-agy` | `ag/gemini-3.8-flash-high`, `ag/gemini-3.8-flash-medium`, `ag/gemini-3.8-flash-low` | Active qua 3 account Google OAuth (`leekyoung55124`, `sanggia5512`, `huytung551237`), tự xoay tua khi hết quota |
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

# 6. DeepSeek Harness CLI (dsh)
DEEPSEEK_BASE_URL="https://router.cutes1tg.online/v1" \
DEEPSEEK_API_KEY="$HERMES_CUSTOM_ROUTER_CUTES1TG_ONLINE_API_KEY" \
DSH_PERMISSION_MODE="danger-full-access" \
dsh --profile headless "<yêu cầu task>"
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

# 6. DeepSeek Harness CLI (dsh)
DEEPSEEK_BASE_URL="http://127.0.0.1:20127/v1" \
DEEPSEEK_API_KEY="$HERMES_CUSTOM_ROUTER_CUTES1TG_ONLINE_API_KEY" \
DSH_PERMISSION_MODE="danger-full-access" \
dsh --profile headless "<yêu cầu task>"

# Hoặc qua runner script:
bash /poki/scripts/run_dsh_worker.sh <workspace_dir> <brief.md>
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
OPENAI_API_KEY="sk-fa5<ROTATED - lay tu $HERMES_CUSTOM_ROUTER_CUTES1TG_ONLINE_API_KEY>"
OPENAI_API_BASE="https://router.cutes1tg.online/v1"
LITELLM_API_KEY="sk-fa5<ROTATED - lay tu $HERMES_CUSTOM_ROUTER_CUTES1TG_ONLINE_API_KEY>"
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
        "apiKey": "sk-fa5<ROTATED - lay tu $HERMES_CUSTOM_ROUTER_CUTES1TG_ONLINE_API_KEY>"
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

### E. Claude Code CLI (`claude`) — XQ API Worker
- **Binary**: `/usr/local/bin/claude` (v2.1.295) — CLI gốc của Anthropic (không dùng trực tiếp).
- **Wrapper**: `/poki/coding-workers-docs/claude-xq-wrapper.py` (v1.0.1) — Python script giả lập `-p` mode, gọi XQ API thay vì Anthropic.
- **Skill**: `claude-code` (v2.2.1) — điều phối coding, PR review, refactor qua Hermes.
- **Models qua XQ API**: `claude-haiku-5-5` (default), `claude-sonnet-4-6`, `claude-opus-4-6`.
- **API Key**: Đọc từ env `XQ_API_KEY` hoặc file `~/.config/xqapi/key` (chmod 600). **KHÔNG hardcode key trong repo**.
- **Endpoint**: `https://xqapi.com/v1/messages` (ghi đè bằng env `XQ_ENDPOINT`).
- **Giới hạn context thực đo (2026-10)**: XQ API chỉ nhận tối đa **~80K input tokens**/request, KHÔNG đạt 1M như quảng cáo. Payload lớn hơn bị **truncate âm thầm** (không báo lỗi): 150K chars → 31K tokens, 271K chars → 75K tokens. ⇒ Task cần context >80K phải chuyển sang Muse Code (200K) hoặc DeepSeek V4.1 (1M qua mini-SWE).
- **Chế độ hoạt động**: One-shot print mode only — nhận brief, gọi XQ API, trả JSON tương thích Claude Code format.
- **Flags hỗ trợ**:
  ```bash
  python3 /poki/coding-workers-docs/claude-xq-wrapper.py \
    -p "task description" \
    --model haiku|sonnet|opus \
    --output-format json|text \
    --dangerously-skip-permissions
  ```
- **Runner chuẩn**: `/poki/coding-workers-docs/run_claude_brief.sh`
  ```bash
  bash run_claude_brief.sh /path/to/brief.md [haiku|sonnet|opus]
  ```
  Script tự động:
  - Đọc brief từ file markdown
  - `cd` vào project dir (dirname của brief)
  - Gọi wrapper với model được chọn
  - In JSON output ra stdout

### F. Antigravity CLI (`agy`) & AGY-Code Worker
- **Binary**: `/root/.local/bin/agy` (v1.2.3) trên Linux, `~/.local/bin/agy` trên macOS.
- **Auto-Rotation Runner**: `/root/.local/bin/agy-runner` tự động trượt qua 3 tài khoản khi gặp 429/RESOURCE_EXHAUSTED.
- **Skill**: `agy-code` (hoặc `antigravity`) với Gemini 3.8 Flash và tùy biến mức suy luận (`low` / `medium` / `high`).
- **Cơ chế 3 Tài khoản Độc lập**:
  - `acc1`: `leekyoung55124@gmail.com` (`~/.config/agy-profiles/acc1`)
  - `acc2`: `sanggia5512@gmail.com` (`~/.config/agy-profiles/acc2`)
  - `acc3`: `huytung551237@gmail.com` (`~/.config/agy-profiles/acc3`)
  - Mỗi tài khoản có `installation_uuid` riêng biệt trong `jetski_state.pbtxt`, chống bị Google gắn cờ dùng chung thiết bị.
  - Tự động đồng bộ token từ 9Router qua script: `python3 /root/ops/agy_profile_sync.py`.
- **Lệnh chạy chuẩn**:
  ```bash
  agy-runner -p "<yêu cầu task + tiêu chí nghiệm thu>" --effort <low|medium|high>
  ```

### G. DeepSeek Harness CLI (`dsh`) & `~/.dsh/profiles/headless/cordis.patch.yml`
- **Binary**: `/usr/local/bin/dsh` (npm package `@deepseek-ai/dsh` v0.2.1-rc.2).
- **Mô hình**: DeepSeek V4.1 Flash (`thtung-paid`) qua 9Router (`/v1/messages` Anthropic streaming SSE).
- **Cấu hình Profile Headless (`~/.dsh/profiles/headless/cordis.patch.yml`)**:
  ```yaml
  llm:
    provider: deepseek-official
  deepseek:
    model: thtung-paid
    messagesApiRoot: /v1
  ```
- **Quy tắc vận hành sống còn**:
  - `dsh` **CẤM** đặt `DEEPSEEK_BASE_URL` trong file `.env` (gây lỗi `sets DEEPSEEK_BASE_URL, which only the launching environment may set`). Bắt buộc export trực tiếp từ môi trường shell hoặc wrapper launcher script.
  - Phải có `DSH_PERMISSION_MODE="danger-full-access"` khi chạy tự động / headless để bỏ qua các câu hỏi xin quyền ghi file và chạy lệnh shell.
  - Phải đặt stopping bounds rõ ràng trong brief: "Khi tất cả test gates của phase đã pass, lập tức kết luận nộp bài, không tự ý tối ưu hóa vi mô hoặc bot simulation ngoài brief" để tránh tình trạng agent kiểm tra lặp đi lặp lại quá nhiều steps.
  - Runner script chuẩn: `/poki/scripts/run_dsh_worker.sh <workspace> <brief.md>`.

---

## 6. Tài liệu Chuyên sâu & Benchmark

- 🎮 **[Benchmark Đối đầu Toàn diện: 5 Workers — Vạn Kiếp Tu Tiên P1–P5 (BENCHMARK.md)](./BENCHMARK.md)**: Đối đầu 5 giai đoạn, 18 gates kỹ thuật (T01–T18) giữa cả 5 workers (`dsh`, `mini-swe-agent`, `opencode` GLM-5.3, `agy` Gemini 3.8, `muse` Meta Muse Code). So sánh chi tiết về số bước, tốc độ Vitest (146 vs 102 vs 142 vs 51 vs 107 tests), kích thước bundle (500k vs 434k vs 344k vs 463k vs 366k), hiệu năng mô phỏng (0.0139 ms/step vs 0.053 ms/step), RAM heap, FPS Chromium (lên tới 59.9 FPS) và ma trận định tuyến thực tế.
- 📜 **[Quy chuẩn Phối hợp Lead–Worker & Tranh luận Kỹ thuật (LEAD_WORKER_PROTOCOLS.md)](./LEAD_WORKER_PROTOCOLS.md)**: Quy định tách biệt vai trò Lead (Hermes) vs 100% Thi công & Test Ownership (Worker), cơ chế phản biện 2 chiều, Watchdog chống treo/chết, và Ma trận lựa chọn worker (Mục 7).

- 📘 **[Hướng dẫn Chi tiết Vận hành 6 Workers trên macOS & Điều phối qua Hermes (MACOS_WORKERS_GUIDE.md)](./MACOS_WORKERS_GUIDE.md)**: Ma trận phân công task, bảng lệnh headless chuẩn, feedback loop Unity MCP Mini và xử lý sự cố.
- 📊 **[Tài liệu Phương pháp & Công thức Benchmark (BENCHMARK.md)](./BENCHMARK.md)**: Hướng dẫn đo lường theo chuẩn DeepSWE (Pier runner) và Terminal-Bench (Harbor runner).
- 📈 **[Báo cáo Thực nghiệm Đối đầu: mini-SWE vs Hermes Direct & DeepSWE v1.1 (VERIFICATION_REPORT.md)](./VERIFICATION_REPORT.md)**:
  - **Single-File Bugfix**: mini-SWE hoàn thành trong **34s** (6 bước) vs Hermes mất **85s** (mini-SWE nhanh hơn 2.5 lần).
  - **Multi-File Feature**: mini-SWE hoàn thành trong **28s** (5 bước, 100% test pass) vs Hermes bị **TIMEOUT >180s** do phình context (>318k token/turn).
  - **DeepSWE v1.1**: Pass 40% (2/5 bài khó tuyệt đối), P2P 80% (không gây regression), 92.3% cache-hit rate.
- ✅ **[Quy chuẩn QA tự động Pokiwar (QA_AUTO_TEST_STANDARD.md)](./QA_AUTO_TEST_STANDARD.md)**: Stack Playwright + CDP WebGL, 5 quy tắc cốt lõi (đo số thật, RED-GREEN, bảo vệ prod), suite 8 nhóm, checklist thi công, quy tắc seed M94, luật no-fake-green. Chỉ tài liệu — bộ test nằm ở `/poki`.
