# Quy chuẩn Phối hợp Lead–Worker (Lead–Worker Operating Protocols)

Tài liệu này xác định nguyên tắc vận hành, ranh giới trách nhiệm và cơ chế tương tác 2 chiều giữa **Hermes (Lead Orchestrator)** và các **Dedicated Coding Workers** (`muse-code`, `deepseek-code`, `glm-code`, `agy-code`, `codex`).

---

## 1. Nguyên Tắc Cốt Lõi: Tách Biệt Tuyệt Đối Vai Trò

```text
┌──────────────────────────────────────────────────────────────────┐
│                   HERMES (LEAD ORCHESTRATOR)                     │
│                                                                  │
│  1. Khảo sát bối cảnh & Phân tích nguyên nhân gốc (Recon & Root) │
│  2. Lập Kế hoạch Thi công (Implementation Plan & Numbered Brief)  │
│  3. Giám sát lộ trình (Watchdog: Chống treo, kẹt loop, đứt quota) │
│  4. Nghiệm thu độc lập đầu ra (Independent Verification)         │
│  ❌ CẤM TỰ GÕ CODE, RSYNC, DOCKER BUILD, LÀM THAY VIỆC CỦA DEV   │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                   1. Giao Plan   │   2. Review & Phản biện
                   thi công       │      (Technical Debate)
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                   DEDICATED CODING WORKER                        │
│                                                                  │
│  1. Review phản biện kế hoạch với Lead trước khi đụng code      │
│  2. 100% Thi công: Sửa code, refactor, tái cấu trúc              │
│  3. 100% Test Ownership: Tự viết testcase, tự chạy test         │
│  4. Chu trình RED ➔ GREEN ➔ REFACTOR (Đỏ trước khi sửa)          │
│  5. Tự build, lint, sửa lỗi biên dịch trong workspace            │
└──────────────────────────────────────────────────────────────────┘
```

- **Hermes là LEAD, không phải Dev thứ hai**: Người dùng thuê năng lực điều phối, quản trị và kiểm định chất lượng. Việc Hermes tự sửa file, tự patch tay là hành vi vi phạm vai trò, dễ sinh lỗi hồi quy (regression) và biến buổi làm việc thành bãi thử nghiệm chắp vá.
- **Worker chịu trách nhiệm 100% thi công**: Bất kỳ sửa đổi nào trong codebase, từ viết logic đến viết testcase và chạy test đều thuộc quyền và nghĩa vụ của Worker.

---

## 2. Ma Trận Trách Nhiệm Chi Tiết (RACI Matrix)

| Hạng mục công việc | Hermes (Lead) | Worker (Dev) | Tiêu chí & Yêu cầu bắt buộc |
| :--- | :---: | :---: | :--- |
| **Khảo sát yêu cầu & Recon bối cảnh** | **A / R** | C | Hermes đọc hiểu repo, trích xuất token/Figma specs, đo số liệu ban đầu |
| **Lập Kế hoạch thi công (Brief/Plan)** | **A / R** | C | Hermes soạn kế hoạch đánh số, working directory, whitelist file, acceptance checks |
| **Review & Phản biện Kế hoạch** | **A** | **R** | **Bắt buộc**: Worker phản biện kiến trúc, rủi ro, phương án test trước khi code |
| **Viết code tính năng / Bugfix** | I | **A / R** | 100% do Worker thực hiện trong repo workspace |
| **Viết Testcase (Unit & Regression)** | C | **A / R** | 100% do Worker viết; spec phải đo số thật (pixel, vị trí, z-index), cấm chỉ đo biến cờ |
| **Chạy Test & Vòng lặp RED ➔ GREEN** | I | **A / R** | Worker tự chạy test: phải ĐỎ trước khi sửa và XANH sau khi sửa hoàn tất |
| **Giám sát lộ trình (Watchdog)** | **A / R** | I | Hermes kiểm tra mtime file (~5 phút), bắt kẹt loop, phát hiện 429 quota để xoay acc |
| **Nghiệm thu độc lập đầu ra** | **A / R** | I | Hermes tự chạy bộ test độc lập, đo lại số thật, đối chiếu baseline, cấm tin self-report |

*(R = Responsible/Thực hiện, A = Accountable/Chịu trách nhiệm chính, C = Consulted/Trao đổi phản biện, I = Informed/Theo dõi)*

---

## 3. Quy Trình Vận Hành 5 Bước

### Bước 1: Khảo sát & Lập Kế Hoạch (Hermes Lead)
- Đo đạc chính xác nguyên nhân gốc rễ (root cause recon).
- Soạn một bản kế hoạch thi công (Numbered Implementation Plan / Brief) duy nhất chứa:
  1. **Working directory**: Đường dẫn tuyệt đối của repo làm việc.
  2. **Whitelist file**: Danh sách file được phép chỉnh sửa (nghiêm cấm sửa lan ngoài phạm vi).
  3. **Acceptance Criteria**: Bộ tiêu chí nghiệm thu định lượng bằng số đo thật.
  4. **Prohibitions**: Cấm sửa nới lỏng spec cũ, cấm đo FPS đa viewport trên host không GPU, cấm pkill bừa bãi.

### Bước 2: Review & Phản Biện 2 Chiều (Worker ↔ Lead Debate)
- **Quy tắc bất di bất dịch**: Worker sau khi nhận plan KHÔNG ĐƯỢC cắm đầu vào code ngay.
- Worker phải phân tích phản biện lại kế hoạch:
  - *"Đoạn logic này có mâu thuẫn với module X trong repo không?"*
  - *"Tiêu chí testcase Lead đưa ra có đo đúng triệu chứng người dùng thấy hay chỉ đo biến trạng thái nội bộ?"*
  - *"Có giải pháp nào tối ưu hơn về kiến trúc và tránh nợ kỹ thuật không?"*
- Nếu có điểm bất hợp lý, Worker gửi ý kiến phản biện lại cho Lead. Hai bên thống nhất giải pháp cuối cùng (**Final Consensus**) rồi mới chuyển sang thi công.

### Bước 3: Thi Công 100% & Chu Trình Testcase (Worker)
- Worker thực hiện toàn bộ việc code và refactor.
- **Quy ước Testcase bắt buộc**:
  - Với mỗi lỗi/tính năng, Worker **PHẢI tự viết testcase/spec hồi quy riêng**. Thiếu spec = Chưa xong.
  - Testcase phải đo số thật (pixel, mã màu, toạ độ tuyệt đối, số node DOM, status code, payload thực).
  - Tuân thủ chu trình **RED ➔ GREEN**: Chạy test thấy ĐỎ (chứng minh lỗi tồn tại) ➔ Sửa code ➔ Chạy test lại thấy XANH (chứng minh lỗi đã được giải quyết).

---

## 4. Quy Tắc Cổng Kiểm Thử 2 Lần Bắt Buộc (Two-Stage Testing Gate)

Tuyệt đối KHÔNG ĐƯỢC tin vào một lần test duy nhất. Mọi task code/sửa lỗi bắt buộc phải vượt qua **2 CỔNG TEST ĐỘC LẬP**:

```text
┌──────────────────────────────────────────────────────────────┐
│  CỔNG 1: PRE-DEPLOY LOCAL GATE (Tại Repo / Workspace Cục Bộ)  │
│                                                              │
│  - Worker chạy toàn bộ testcase trên bản local.              │
│  - Điều kiện: XANH 100% (Pass toàn bộ test, 0 compile error, │
│    không gây lỗi hồi quy / regression).                      │
│  - ⛔ NẾU LOCAL ĐỎ ➔ CẤM TUYỆT ĐỐI KHÔNG ĐƯỢC DEPLOY.         │
└──────────────────────────────┬───────────────────────────────┘
                               │ Local pass 100%
                               ▼
┌──────────────────────────────────────────────────────────────┐
│               TIẾN HÀNH BUILD & DEPLOY LÊN HOST              │
│  (Rsync đủ cây, build container, reload service)              │
└──────────────────────────────┬───────────────────────────────┘
                               │ Deploy thành công
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  CỔNG 2: POST-DEPLOY LIVE GATE (Trên Môi Trường Đã Deploy)   │
│                                                              │
│  - Chạy lại TOÀN BỘ bộ testcase trực tiếp trên runtime thật: │
│    live container, live URL, đúng account đối chứng.         │
│  - Đo số thật trên production/staging (pixel, layout,        │
│    status code, socket response).                            │
│  - Loại bỏ hoàn toàn rủi ro: rsync thiếu file, bundle Next.js│
│    bị cache cũ, sai lệch env giữa local và container.        │
│  - ⛔ NẾU LIVE ĐỎ ➔ BỊ COI LÀ FALSE-DONE, PHẢI SỬA LẠI NGAY.  │
└──────────────────────────────────────────────────────────────┘
```

1. **Lần 1 — Pre-Deploy Local Gate**:
   - Chạy trên workspace của worker. Phải pass 100% các spec trước khi cho phép tiến hành khâu deploy.
   - Nếu testcase local còn trượt hoặc vỡ build mà đem deploy là vi phạm quy trình nghiêm trọng.
2. **Lần 2 — Post-Deploy Live Gate**:
   - Sau khi deploy xong (ví dụ rsync đủ 4 cây thư mục, Next.js build bundle mới, docker container up), BẮT BUỘC phải kích hoạt test suite chạy lại lần thứ hai nhắm thẳng vào live URL / runtime thật.
   - Chỉ khi bản live trả về kết quả XANH và đo đúng số thật thì task mới chính thức được đóng.

---

## 5. Watchdog — Giám Sát Tiến Trình Chống Treo/Chết (Hermes Lead)
- Hermes theo dõi tiến trình nền qua PID được cấp phát:
  - **Kiểm tra mtime**: Sau ~5 phút mà các file mục tiêu không có mtime mới ➔ Worker đang lý thuyết suông (theorizing/looping), cần can thiệp kéo về thực tế.
  - **Bắt vòng lặp vô tận (Looping watchdog)**: Phát hiện hành vi chạy test liên tục 10 lần mà không sửa code, hoặc đo đạc vô nghĩa.
  - **Xử lý sự cố chết/treo & Hết Quota**: Bắt lỗi HTTP 429 / `RESOURCE_EXHAUSTED` để kích hoạt cơ chế xoay profile (ví dụ `agy-runner` tự nhảy sang `acc2`, `acc3`), không để chết tác vụ giữa chừng hoặc đốt sạch ngân sách vô ích.

### 5b. Cron watchdog đi kèm mỗi worker (BẮT BUỘC)
- Mỗi lần spawn worker (muse/mini/glm/codex/agy) **phải tạo kèm 1 cron job** theo dõi tiến độ liên tục và báo cáo về chat — user không phải hỏi "xong chưa".
- Tạo cron **kèm `--model` + `--provider` ngay lúc tạo** (không tạo trước set sau):
```bash
hermes cron create --model thtung-muse --provider custom:THTUNG \
  --name "watch-<TÊN-WORKER>" --deliver origin "every 1m" \
  "<prompt watchdog: pgrep worker/Unity, tail log brief, check artifact + curl endpoint, báo tiến độ ≤10 dòng; worker xong hoặc treo >10 phút thì báo ngay>"
```
- ⚠️ Bẫy đã gặp thật (2026-10-02): tạo cron **không** kèm model/provider rồi `edit` thêm sau → job chạy với config cũ, fail liên tiếp `No LLM provider configured`. Luôn tạo kèm từ đầu.
- Khi worker xong (REPORT tồn tại) hoặc chết: báo kết quả cuối 1 lần rồi **xóa cron** (`hermes cron remove <job_id>`) để khỏi spam.
- Tên cron theo quy ước `watch-<TÊN-BRIEF>` để dễ truy vết worker nào.

## 6. Nghiệm Thu Độc Lập Đầu Ra (Hermes Lead)
- Báo cáo tóm tắt của worker chỉ là tài liệu tự thuật (self-report), không phải sự thật đã kiểm chứng.
- Hermes độc lập đo đạc lại:
  - Soát `git diff` xem worker có làm đúng whitelist và không nới lỏng spec cũ hay không.
  - Kiểm tra cả 2 lần test: Cổng 1 (Local) đã xanh chưa, Cổng 2 (Live deploy) đã xanh chưa.
  - Đo lại số thật trên artifact đã deploy/build bằng đúng tài khoản và URL chuẩn.
- Báo cáo kết quả về Discord: Báo cáo ngắn gọn, tập trung vào số đo thực tế, nêu rõ cái gì ĐÃ XONG và cái gì CHƯA XONG. Tuyệt đối không kể lể lại hành trình.

---

## 7. Tiêu Chí Lựa Chọn Worker & So Sánh Thực Tế (Worker Routing Matrix)

Dựa trên kết quả thực tế qua 5 giai đoạn (P1–P5) xây dựng engine game 2D top-down ("Vạn Kiếp Tu Tiên") và các bài toán coding thực chiến trên hệ thống:

### 7.1. Bảng Tổng Hợp So Sánh Định Lượng Thực Tế (5 Workers)

| Hạng mục Đo đạc | Worker A: `dsh` (DeepSeek V4.1) | Worker B: `mini` (DeepSeek V4.1) | Worker C: `opencode` (GLM 5.3) | Worker D: `agy` (Gemini 3.8) | Worker E: `muse` (Muse Contributor) |
|---|---|---|---|---|---|
| **Độ phủ Unit tests (Vitest)** | **146 tests** (1.02s) | 102 tests (19.30s) | 142 tests (3.26s) | 51 tests (1.19s) | **107 tests (2.74s)** |
| **Độ phủ E2E (Playwright)** | 19 tests (58.3s) | 18 tests (34.2s) | **23 tests (45.5s)** | 3 suites (21.4s) | 9 tests (28.3s) |
| **Tỷ lệ đạt 18 Gates** | **18/18 PASS** | **18/18 PASS** | **18/18 PASS** | **18/18 PASS** | **18/18 PASS** |
| **Kích thước Bundle JS** | 500.0 kB | 434.0 kB | **344.6 kB (nhỏ nhất)** | 463.6 kB | **366.3 kB (nhỏ thứ hai)** |
| **Mô phỏng 500 quái (T12)** | 0.063 ms/step | 0.065 ms/step | **0.0139 ms/step (nhanh nhất)** | 0.1345 ms/step | 0.0530 ms/step (p99 0.311) |
| **Đỉnh RAM JS Heap** | 95.70 MB | 88.40 MB | **9.54 MB** | **9.54 MB** | 42.63 MB |
| **FPS Headless Chromium** | 18.0 FPS | 7.5 FPS | 23.4 FPS | 20.0 FPS | **59.9 FPS (mượt nhất)** |

---

### 7.2. Chi Tiết Từng Worker: Mạnh Về Cái Gì & Khi Nào Nên Chọn Code

#### 1. Worker A: `@deepseek-ai/dsh` (DeepSeek V4.1 Flash via 9Router)
* **Mạnh về cái gì:**
  - **Khả năng tự chủ và tự sửa lỗi (Self-healing) đỉnh cao:** Khi gặp lỗi khó (i-frame kẹt test, popup đè lớp), `dsh` tự viết file chẩn đoán `.dbg.mjs`, lần ra tận gốc nguyên nhân trong core game và tự bổ sung API gỡ lỗi mà không cần Lead can thiệp.
  - **Kỷ luật test mock sạch sẽ & tốc độ cao:** Viết tới 146 unit test mà chạy chỉ trong **1.02 giây**.
  - **UI/UX chuẩn mực thương mại:** Giao diện Master-Detail, vector silhouette vẽ tay chuẩn xác, không bao giờ lỗi tràn hay lệch layout.
  - **Quy trình nghiệm thu 1 lệnh:** Tự động hóa pipeline kiểm thử và xuất báo cáo (`npm run verify`).
* **Khi nào Lead nên chọn code:**
  - **Xây dựng module lõi (Core Engine / State Machine / Battle Logic phức tạp).**
  - **Dự án đòi hỏi bộ test coverage khắt khe** (Unit tests mock sạch + E2E Playwright) chạy CI/CD tốc độ cao.
  - **Khi cần UI hoàn thiện thương mại**, bố cục chuẩn mực không có lỗi vặt.

#### 2. Worker B: `mini-swe-agent` (DeepSeek V4.1 Flash via 9Router)
* **Mạnh về cái gì:**
  - **Tiết kiệm số bước (steps) và chi phí token số một:** Hoàn thành toàn bộ bài toán với chỉ 564 steps (tiết kiệm hơn Worker A gần 32%).
  - **Tốc độ thực thi chớp nhoáng:** Các task bugfix đơn file hoàn thành chỉ trong 20–34 giây.
  - **Sáng tạo văn phong & mỹ thuật bản địa hóa:** Hệ thống 12 icon chữ Hán thư pháp (劍, 萬, 雷...) đổi màu theo nguyên tố; câu từ tu chân bản địa hóa kèm chú thích công thái học `(Restart)`, `(Về Menu)`.
* **Khi nào Lead nên chọn code:**
  - **Bugfix nhanh (Single-file bugfix, sửa regression):** Giải quyết lỗi trong vài chục giây mà không tiêu tốn tài nguyên.
  - **Tác vụ bulk / chạy song song số lượng lớn:** Khi cần chạy nhiều worker đồng thời để xử lý hàng loạt task nhỏ nhằm tiết kiệm chi phí token.
  - **Tác vụ vận hành DevOps, deploy container, bảo trì script VPS.**

#### 3. Worker C: `opencode` (GLM-5.3-Flash qua 9Router)
* **Mạnh về cái gì:**
  - **Vô địch về tối ưu hóa Bundle JS & Bộ nhớ:** Bundle JS sinh ra chỉ **344.6 kB** (gọn nhất trong tất cả các worker, nhỏ hơn Worker A tới 31%).
  - **Thuật toán mô phỏng lõi đạt hiệu năng cực hạn:** Tốc độ step đạt **0.0139 ms/step** (nhanh gấp 4.5 lần Worker A) nhờ cơ chế zero-allocation in-place compaction (`compactInPlace`).
  - **Bộ test E2E Playwright sâu và phong phú nhất:** Viết 23 kịch bản E2E bao quát sâu, tự nhận diện và giải quyết triệt để lỗi bất đồng bộ của engine.
  - Chi phí token GLM rẻ nhất qua 9Router.
* **Khi nào Lead nên chọn code:**
  - **Ứng dụng frontend / Web Game nhạy cảm về kích thước bundle** (Bundle size budget < 350 kB).
  - **Xử lý thuật toán toán học, mô phỏng số lượng lớn thực thể** (High Performance / Zero Garbage Collection).
  - **Khi cần bao phủ kịch bản kiểm thử E2E Playwright chuyên sâu.**

#### 4. Worker D: `agy` (Google Antigravity CLI — Gemini 3.8 Flash)
* **Mạnh về cái gì:**
  - **Thẩm mỹ UI/UX hiện đại và đồ họa chiến đấu bóng bẩy nhất:** Thiết kế translucent glass container, bo góc hiện đại đẳng cấp commercial indie; vòng radar/trận pháp Bát Quái phân tầng hiển thị tầm đánh tự động; đạn đạo neon phát sáng rõ nét.
  - **Context cửa sổ siêu lớn (1M+ tokens):** Đọc hiểu trọn vẹn toàn bộ codebase đồ sộ trong một lượt.
  - **Hệ thống an toàn đa tầng & tự động xoay tài khoản:** Tự động xoay tua 3 tài khoản Google OAuth (`acc1`, `acc2`, `acc3`) chống lỗi 429 / Quota Exceeded.
* **Khi nào Lead nên chọn code:**
  - **Giao diện người dùng hiện đại, bóng bẩy (Commercial Indie Game, Landing Page, Dashboard cao cấp).**
  - **Refactor hoặc rà soát codebase cực lớn** cần nhồi toàn bộ repository vào context cùng lúc.
  - **Tác vụ kết hợp đa phương thức (Multimodal):** Đọc hiểu mockup hình ảnh, video gameplay, screenshot đối chiếu.

#### 5. Worker E: `muse` (Meta Muse Code — `muse-spark-1.3-contributor`)
* **Mạnh về cái gì:**
  - **Bố cục công thái học (HUD UX) khoa học nhất:** Dải thanh trạng thái ngang tinh tế ở đỉnh màn hình, Action Bar 6 ô chiêu thức trực quan ở đáy kèm thời gian hồi chiêu; tạo hình nhân vật mang bản sắc văn hóa Việt Nam (nón lá truyền thống, áo đạo bào xanh ngọc).
  - **Khả năng tự phát hiện lỗi logic sâu trong vòng lặp game (Deep Loop Logic Debugging):** Tự bắt lỗi ticker game ghi đè BGM mỗi frame khi vào Endless Mode và tự fix trước khi nộp bài.
  - **Tốc độ khung hình (FPS) mượt nhất toàn đoàn:** Đạt **59.9 FPS** trong môi trường headless Chromium, thời gian step 0.053 ms.
* **Khi nào Lead nên chọn code:**
  - **Xây dựng game hoặc ứng dụng cần vòng lặp xử lý frame tốc độ cao, mượt mà (60 FPS).**
  - **Thiết kế giao diện đòi hỏi tư duy công thái học cao cho người dùng/người chơi** (HUD, Action Bar, Hotkeys).
  - **Giải quyết các lỗi tương tác logic phức tạp** giữa các hệ thống (âm thanh, trạng thái, vòng lặp game loop).

#### 6. Worker F: `codex` (OpenAI Codex CLI — GPT-5.6-Luna qua `thtung-gpt`)
* **Mạnh về cái gì:**
  - **Tư duy kiến trúc hệ thống chuẩn mực:** Tuân thủ triệt để design pattern, clean architecture, SOLID.
  - **Typing TypeScript strict & API contract:** Không bao giờ lạm dụng `any`, định nghĩa interface và contract chặt chẽ.
* **Khi nào Lead nên chọn code:**
  - **Thiết kế khung kiến trúc ban đầu (Scaffolding / Architecture setup).**
  - **Viết Backend API, xử lý migration cơ sở dữ liệu hoặc thiết kế domain models.**

#### 7. Worker G: `claude` (Claude Code CLI — Anthropic Claude 3.7 / Sonnet 4.6)
* **Mạnh về cái gì:**
  - **Suy luận ngữ cảnh sâu và giải quyết thuật toán hóc búa:** Đọc hiểu code phức tạp, tìm các edge cases tiềm ẩn.
  - **Code review & Security audit:** Soát lỗi bảo mật, rà soát lỗ hổng logic trước khi release.
* **Khi nào Lead nên chọn code:**
  - **Code review trước khi commit/merge lên branch chính.**
  - **Điều tra các lỗi logic khó hiểu hoặc tái cấu trúc các thuật toán toán học phức tạp.**

---

### 7.3. Bảng Ma Trận Quyết Định Nhanh Cho Lead (Quick Decision Matrix)

| Loại Tác Vụ Cần Làm | Worker Ưu Tiên 1 (Khuyên dùng) | Worker Ưu Tiên 2 (Dự phòng) | Lý do chính |
|---|---|---|---|
| **Core Engine / Logic Game Phức Tạp** | **`dsh`** (DeepSeek V4.1) | **`muse`** (Muse Contributor) | `dsh` self-healing tự chẩn đoán sâu; `muse` logic vòng lặp chuẩn |
| **Bugfix Nhanh / DevOps / Script Nhỏ** | **`mini`** (mini-swe-agent) | **`opencode`** (GLM 5.3) | `mini` chớp nhoáng (20s-30s), tiết kiệm 32% token |
| **Tối Ưu Bundle / Hiệu Năng / Zero-GC** | **`opencode`** (GLM 5.3) | **`muse`** (Muse Contributor) | `opencode` bundle siêu nhẹ (344 kB), step 0.0139 ms |
| **Đồ Họa Bóng Bẩy / UI Hiện Đại / Multimodal**| **`agy`** (Gemini 3.8) | **`muse`** (Muse Contributor) | `agy` visual glass/neon đỉnh cao; `muse` HUD công thái học |
| **Game Cần 60 FPS Mượt / HUD Khoa Học** | **`muse`** (Muse Contributor) | **`opencode`** (GLM 5.3) | `muse` đạt 59.9 FPS headless, Action Bar trực quan |
| **Kiến Trúc Backend / Scaffolding / API** | **`codex`** (GPT-5.6 Luna) | **`dsh`** (DeepSeek V4.1) | `codex` kiến trúc clean, typing strict |
| **Code Review / Security / Thuật Toán Khó** | **`claude`** (Claude 3.7/Sonnet) | **`dsh`** (DeepSeek V4.1) | `claude` suy luận sâu, soát lỗi tinh tế |


