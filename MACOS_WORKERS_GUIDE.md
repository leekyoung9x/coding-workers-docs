# HƯỚNG DẪN VẬN HÀNH 5 DEDICATED WORKERS TRÊN MACOS & ĐIỀU PHỐI QUA HERMES

> **Môi trường mục tiêu:** macOS Sequoia 15.2 (Apple Silicon ARM64).  
> **Orchestrator trung tâm:** Hermes Agent (quản lý Context, Discord Gateway, Full MCP Figma & Unity).  
> **Mục tiêu:** Cung cấp quy chuẩn thi công, bảng lệnh điều phối, ánh xạ nhiệm vụ và quy trình tự động hóa cho 5 Dedicated Coding Workers.

---

## 1. TỔNG QUAN VAI TRÒ & PHÂN CÔNG TÁC VỤ (TASK ROUTING MATRIX)

| STT | Dedicated Worker | CLI Binary | Backend Model | Endpoint Đấu nối | Loại Task Tối ưu Nhất | Khi nào KHÔNG nên dùng |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Muse Code** | `~/.local/bin/muse` (v1.2.1) | `meta/muse-spark-1.3-contributor` (`xhigh`) | OpenRouter qua `muse-shim :8787` | **Tính năng Unity Client C#**, UI uGUI Prefab, sửa lỗi logic Combat, bài toán dài hơi (>20 turns). | Task script nhỏ 1 file, sửa backend Python/Nodejs. |
| **2** | **mini-SWE-agent** | `~/.local/bin/mini` (v2.4.6) | `thtung-paid` (`deepseek-v4.1-flash`) | 9Router VPS (`router.cutes1tg.online`) | **Tính năng Backend** (.NET CleanArch, Colyseus TS, Go), bugfix nhanh, refactor repo vừa (<50 files). Tốc độ 28s/task. | Code Unity cần verify editor compiler; task cần TUI tương tác. |
| **3** | **OpenCode CLI** | `/opt/homebrew/bin/opencode` (v1.18.31) | `thtung-glm` (`glm-5.3-flash`) | 9Router VPS (`router.cutes1tg.online`) | **Review PR chéo**, đọc hiểu repo rộng (200k context), rà soát dependencies, refactor đa file. | Task chạy bash độc lập không cần context rộng. |
| **4** | **Codex CLI** | `~/.local/bin/codex` (v0.147.0) | `gpt-5.6-sol` / GPT models | OpenAI Native OAuth (`~/.codex/auth.json`) | **Thiết kế kiến trúc hệ thống**, viết core engine, review bảo mật và chất lượng code pre-commit. | Task cần tiết kiệm chi phí tối đa (dùng DeepSeek/GLM thay thế). |
| **5** | **Antigravity CLI** | `~/.local/bin/agy` (v1.2.3) | `thtung-agy` (Gemini 3.8 / Opus 4.6) | Google Antigravity Native / 9Router | **Phân tích đa phương thức**, xử lý context khổng lồ (1M-2M tokens), second opinion từ hệ sinh thái Google. | Task terminal thao tác nhanh cần zero latency. |

---

## 2. BẢNG THÔNG SỐ CẤU HÌNH CỦA 5 WORKERS TRÊN MACOS

| Worker | Tệp cấu hình trên Mac | Quyền file | Biến môi trường / Headers chính | Công cụ phụ trợ tích hợp |
| :--- | :--- | :---: | :--- | :--- |
| **Muse Code** | `~/.config/muse/env`<br>`~/.config/muse/settings.json` | `600` | `MUSE_SHIM_PROVIDER=generic`<br>`MUSE_SHIM_MODEL=meta/muse-spark-1.3-contributor`<br>`META_API_KEY=local-shim-placeholder` | **Unity MCP Mini (13 tools)**: compile loop, test runner, play scene. |
| **mini-SWE** | `~/Library/Application Support/mini-swe-agent/.env`<br>*(symlink: `~/.config/mini-swe-agent/.env`)* | `600` | `OPENAI_API_KEY=sk-fa5efb...`<br>`OPENAI_API_BASE=https://router.cutes1tg.online/v1`<br>`MSWEA_MODEL_NAME=openai/thtung-paid` | Bash subshell runner, auto-submit detector, cost guardrails (`-l 0.5`). |
| **OpenCode** | `~/.config/opencode/opencode.json`<br>`~/.local/share/opencode/auth.json` | `600` | Provider: `ninerouter` (`@ai-sdk/openai-compatible`)<br>BaseURL: `https://router.cutes1tg.online/v1`<br>Model: `thtung-glm` | Format JSON stream, Git PR inspector, session resume. |
| **Codex CLI** | `~/.codex/config.toml`<br>`~/.codex/auth.json` | `600` | `wire_api = "responses"`<br>`supports_websockets = false`<br>`requires_openai_auth = true` | Git worktree parallel isolation, sandbox workspace-write. |
| **Antigravity**| `~/.config/antigravity/`<br>`~/.gemini/antigravity-cli/` | `600` | Managed by Google OAuth (`agy`) | Multi-agent coordination, Google Search integration. |

---

## 3. HƯỚNG DẪN SỬ DỤNG VÀ LỆNH THỰC THI (CANONICAL COMMANDS)

### 3.1. Worker 1: Muse Code (Chuyên gia Unity Client & C#)

#### A. Lệnh chạy headless chuẩn qua Hermes:
```bash
META_API_KEY=local-shim-placeholder muse exec \
  --provider meta \
  --base-url http://127.0.0.1:8787 \
  --model meta/muse-spark-1.3-contributor \
  --reasoning-effort xhigh \
  --yolo \
  --workspace "/Users/leekyoung9x/Downloads/pokiwar/pokiguard_client" \
  "<Yêu cầu code C# kèm spec>"
```

#### B. Vòng lặp tự động sửa lỗi của Muse (Feedback Loop):
1. Muse sửa file `.cs`.
2. Muse tự gọi MCP `refresh_asset_db` để Unity compile lại.
3. Muse tự gọi MCP `get_compilation_errors`:
   - Nếu có lỗi biên dịch: Đọc mã CSxxxx, dòng lỗi và tự patch lại code.
   - Nếu sạch lỗi (0 errors): Tiếp tục bước 4.
4. Muse tự gọi MCP `play_scene` / `run_tests` để verify runtime.

#### C. Quản lý dịch vụ Proxy ngầm (`muse-shim`):
```bash
muse-shim-service status    # Kiểm tra trạng thái shim
muse-shim-service start     # Bật shim nền
muse-shim-service restart   # Khởi động lại khi đổi model
muse-smoke-test             # Chạy test kiểm tra toàn bộ pipeline
```

---

### 3.2. Worker 2: mini-SWE-agent (Chuyên gia Backend & Bugfix nhanh)

#### A. Lệnh chạy headless chuẩn qua Hermes:
```bash
MSWEA_SILENT_STARTUP=1 mini --exit-immediately -y -l 0.5 \
  -t "<Mô tả bug/feature>. Viết test kiểm tra. Then echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT as its own command."
```

#### B. Các cờ bắt buộc:
- `--exit-immediately`: Tự động thoát ngay khi agent hoàn thành, không treo terminal.
- `-y` (`--yolo`): Tự động duyệt lệnh bash, không dừng chờ người dùng gõ `yes`.
- `-l 0.5`: Trần chi phí tối đa $0.5/task (chống vòng lặp vô tận).
- `MSWEA_SILENT_STARTUP=1`: Ẩn banner để output trả về cho Hermes sạch sẽ nhất.

---

### 3.3. Worker 3: OpenCode CLI (Chuyên gia Đọc hiểu & Review PR)

#### A. Lệnh chạy một lượt (One-shot):
```bash
opencode run -m ninerouter/thtung-glm "<Yêu cầu review hoặc refactor>"
```

#### B. Kèm file ngữ cảnh cụ thể:
```bash
opencode run -m ninerouter/thtung-glm "Review tính năng auth" -f src/auth.ts -f tests/auth.test.ts
```

#### C. Chế độ tương tác TUI (Interactive qua tmux):
```bash
tmux new-session -d -s opencode-session "opencode"
tmux send-keys -t opencode-session "Refactor module payment" Enter
tmux capture-pane -t opencode-session -p -S -50
```

---

### 3.4. Worker 4: OpenAI Codex CLI (Chuyên gia Kiến trúc & Refactor sâu)

#### A. Lệnh chạy One-shot với quyền Workspace:
```bash
codex exec -s workspace-write "<Mô tả yêu cầu refactor kiến trúc>"
```

#### B. Chạy hoàn toàn tự động (YOLO mode trong git repo sạch):
```bash
codex exec --dangerously-bypass-approvals-and-sandbox "<Yêu cầu task>"
```

#### C. Review PR đối chiếu nhánh:
```bash
codex review --base origin/main
```

---

### 3.5. Worker 5: Google Antigravity CLI (`agy`) (Chuyên gia Đa năng)

#### A. Lệnh chạy One-shot:
```bash
agy -p "<Yêu cầu task phân tích hoặc code>" --dangerously-skip-permissions
```

#### B. Đăng nhập lần đầu (khi chuyển tài khoản):
Chạy trực tiếp `agy` trên terminal, trình duyệt sẽ tự mở trang Google OAuth để đăng nhập và cấp quyền.

---

## 4. QUY TRÌNH ĐIỀU PHỐI CỦA HERMES TỪ DISCORD (END-TO-END WORKFLOW)

```text
[Discord User nhắn tin]
  "Làm màn hình Popup_Reward theo frame Figma https://..."
         │
         ▼
[Bước 1: Hermes Tiếp nhận & Phân tích]
  • Xác định Workspace: pokiguard_client (Unity C#)
  • Quyết định Routing: Cần dùng Muse Code 1.3
         │
         ▼
[Bước 2: Hermes Khai thác MCP Full]
  • Gọi Figma MCP: Lấy kích thước (width/height), màu (#HEX), font chữ, hierarchy UI
  • Gọi Unity MCP Pro: Đọc cấu trúc script Controller hiện có
  • Tổng hợp thành bản "Design Implementation Spec" súc tích
         │
         ▼
[Bước 3: Hermes Ủy quyền cho Worker]
  • Hermes gọi skill muse-code chạy:
    muse exec --yolo --reasoning-effort xhigh --workspace <path> "<Spec từ Bước 2>"
         │
         ▼
[Bước 4: Worker Tự động Code & Tự sửa lỗi]
  • Muse Code viết code C#
  • Tự gọi refresh_asset_db & get_compilation_errors qua Unity MCP Mini
  • Tự sửa cho đến khi compile sạch 0 lỗi
         │
         ▼
[Bước 5: Hermes Nghiệm thu Vòng cuối]
  • Hermes bật play_scene kiểm tra vào được MainHome
  • Kiểm tra Git diff không bị lệch layout cũ
  • Chụp ảnh screenshot và báo cáo kết quả dạng BẢNG lên Discord
```

---

## 5. BẢNG CÚ PHÁP CHỈ ĐỊNH CHỦ ĐỘNG TỪ DISCORD (DISCORD TRIGGER MATRIX)

Bình thường Hermes sẽ tự động phân tích tech stack để chọn worker. Khi người dùng muốn **ép buộc chỉ định một worker cụ thể**, chỉ cần chèn các từ khóa nhận diện vào câu chat trong Discord theo bảng sau:

| Worker muốn chỉ định | Từ khóa nhận diện trong câu chat | Ví dụ câu lệnh chat vào Discord | Hành động Hermes sẽ thực thi |
| :--- | :--- | :--- | :--- |
| **1. Muse Code**<br>*(Chuyên Unity C#)* | `dùng muse`, `muse code`, `qua muse`, `bằng muse` | *"Dùng muse viết controller cho Popup_Reward trong client"*<br>*"Sửa bug skill pet qua muse code nhé"* | Đóng gói Design Spec, gọi `muse exec --model meta/muse-spark-1.3-contributor --reasoning-effort xhigh --yolo` kèm **Unity MCP Mini (13 tools)**. |
| **2. mini-SWE**<br>*(Chuyên Backend DeepSeek)* | `dùng mini`, `dùng deepseek`, `qua mini-swe`, `bằng mini` | *"Dùng mini sửa bug tính exp quest trong CleanArch"*<br>*"Viết test API login bằng deepseek"* | Gọi `mini --exit-immediately -y -l 0.5 -m openai/thtung-paid` chạy bash loop giải quyết trong ~28s. |
| **3. OpenCode**<br>*(Chuyên Review & GLM)* | `dùng opencode`, `dùng glm`, `qua opencode`, `bằng glm` | *"Dùng opencode review diff nhánh feature_pokiwar xem sót gì không"*<br>*"Refactor module payment bằng glm"* | Gọi `opencode run -m ninerouter/thtung-glm` đọc hiểu toàn bộ repo rộng để audit/refactor. |
| **4. Codex CLI**<br>*(Chuyên Kiến trúc GPT)* | `dùng codex`, `qua codex`, `bằng codex` | *"Dùng codex thiết kế interface cho module Matchmaking"*<br>*"Codex review bảo mật file auth"* | Gọi `codex exec -s workspace-write` hoặc `codex review --base origin/main`. |
| **5. Antigravity**<br>*(Chuyên Gemini & Đa năng)* | `dùng agy`, `dùng antigravity`, `qua agy`, `bằng agy` | *"Dùng agy phân tích log crash này xem"*<br>*"Qua agy đọc 10 file dump này"* | Gọi `agy -p "<task>" --dangerously-skip-permissions` tận dụng context window 1M+ tokens. |

> **Quy tắc phối hợp:**
> - **Chat tự nhiên (không chỉ định worker)**: Hermes tự động nhận diện: nếu file `.cs`/Unity ➔ tự gọi **Muse Code**; nếu Backend (.NET/TS/Go/Python) ➔ tự gọi **mini-SWE (DeepSeek)**.
> - **Chat có kèm từ khóa chỉ định**: Hermes tuân thủ 100% worker người dùng yêu cầu.

---

## 6. BẢNG XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

| Hiện tượng lỗi | Nguyên nhân cốt lõi | Cách khắc phục ngay lập tức |
| :--- | :--- | :--- |
| **`muse exec` báo Connection Refused :8787** | `muse-shim` chưa được bật hoặc bị crash | Chạy lệnh: `muse-shim-service restart`<br>Kiểm tra health: `curl http://127.0.0.1:8787/health` |
| **`mini` báo 401 Unauthorized** | Sai key 9Router hoặc key hết hạn | Kiểm tra file: `~/.config/mini-swe-agent/.env`<br>Đảm bảo `OPENAI_API_KEY="sk-fa5efb56e57fe4b9-drd5jf-be158103"` |
| **`opencode` báo Provider Not Found** | Thiếu cấu hình provider `ninerouter` | Kiểm tra file: `~/.config/opencode/opencode.json` đảm bảo có định nghĩa provider `ninerouter`. |
| **Unity MCP Mini không nhận lệnh** | Unity Editor chưa bật hoặc kẹt WebSocket | Mở Unity Editor dự án `pokiguard_client`. Kiểm tra port 6605/6606 không bị chiếm dụng. |
| **Codex CLI bị treo lúc khởi động (7s)** | Thử kết nối WebSocket thất bại | Đảm bảo trong `~/.codex/config.toml` đã đặt `supports_websockets = false`. |
| **`agy` báo eligibility check failed** | Chưa đăng nhập Google OAuth | Mở terminal gõ `agy` và hoàn tất đăng nhập trên trình duyệt. |
