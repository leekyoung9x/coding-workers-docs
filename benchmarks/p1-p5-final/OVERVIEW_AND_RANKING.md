# Báo Cáo Tổng Quan & Bảng Xếp Hạng Chung Cuộc 8 Coding Workers (P1–P5)

*Ngày hoàn thành:* 2026-10-21  
*Hạ tầng kiểm định:* Ubuntu LTS (VPS `66.135.0.13`), Node LTS v26.8.2, PixiJS v8.22.0, Vite 6, TypeScript strict, Vitest, Playwright.  
*Đề bài đối đầu:* Game roguelite 2D top-down "Vạn Kiếp Tu Tiên" từ cùng starter repository sạch qua 5 giai đoạn (P1–P5) với 18 gates kỹ thuật khắt khe (T01–T18).

---

## 1. Hệ Thống 5 Tiêu Chí Đánh Giá (Thang Điểm 100)

| Tiêu chí | Trọng số | Nội dung đánh giá |
|---|:---:|---|
| **1. Độ phủ & Kỷ luật kiểm thử** | 20 điểm | Số lượng unit test, tốc độ thực thi test suite, số kịch bản E2E Playwright thực tế, độ phủ biên logic (boundary conditions). |
| **2. Hiệu năng mô phỏng lõi** | 20 điểm | Thời gian tính toán mỗi step mô phỏng 500 quái vật (ms/step, ngân sách 16.67ms), cơ chế zero-allocation / spatial-hash, dung lượng RAM JS Heap. |
| **3. Độ mượt Render & FPS thực tế** | 20 điểm | Tốc độ khung hình (FPS median và 1% low) đo thực tế trong Chromium headless dưới tải nặng 500 quái, độ ổn định vòng lặp game loop. |
| **4. Tối ưu hóa đóng gói Bundle** | 20 điểm | Kích thước file bundle JS chính (kB), dung lượng asset tĩnh, tính procedural của Web Audio API (0 asset ngoài tải chậm). |
| **5. Mức độ tự chủ & Tự sửa lỗi sâu** | 20 điểm | Khả năng tự chẩn đoán bug ngầm (ticker, hitbox, missing textures) không cần can thiệp tay, tính công thái học và thẩm mỹ giao diện. |

---

## 2. Bảng Xếp Hạng Chung Cuộc 8 Workers

| Hạng | Worker & CLI Tool | Model LLM | Điểm Kiểm thử (20) | Điểm Hiệu năng (20) | Điểm FPS Render (20) | Điểm Bundle (20) | Điểm Tự chủ / UX (20) | **TỔNG ĐIỂM (100)** | Danh hiệu / Điểm nổi bật |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| 🥇 **1** | **Worker E: `muse`** | `muse-spark-1.3-contributor` | 16 | 18 | **20** | 19 | **20** | **93 / 100** | **Quán Quân Toàn Diện:** Kỷ lục 59.9 FPS, HUD công thái học, nón lá Việt Nam |
| 🥈 **2** | **Worker C: `opencode`** | GLM-5.3-Flash (`thtung-glm`) | 18 | **20** | 16 | **20** | 16 | **90 / 100** | **Vô Địch Hiệu Năng & Bundle:** 0.0139 ms/step, bundle 344.6 kB gọn nhất |
| 🥉 **3** | **Worker F: `claude`** | DeepSeek V4.1 (`thtung-paid`) | **20** | 16 | 14 | 17 | **20** | **87 / 100** | **Vô Địch Kiểm Thử:** Kỷ lục 284 unit tests + 60 E2E tests, tự sửa hitbox |
| 🥉 **3** | **Worker G: `kimi`** | Kimi K3 (`thtung-kimi`) | 18 | 19 | 15 | 17 | 18 | **87 / 100** | **Kỷ Luật Tác Vụ Xuất Sắc:** TodoList chặt chẽ, sim 0.038 ms/step, overhead HP |
| **5** | **Worker A: `dsh`** | DeepSeek V4.1 (`thtung-paid`) | 18 | 18 | 15 | 15 | 19 | **85 / 100** | **Self-Healing Đỉnh Cao:** Tự viết script `.dbg.mjs`, unit test siêu tốc 1.02s |
| **6** | **Worker H: `codex`** | DeepSeek V4.1 (`thtung-paid`) | 17 | 17 | 12 | 18 | 17 | **81 / 100** | **Tự Chủ Shell Cao Độ:** Tính toán cân bằng Endless lũy tiến chính xác |
| **7** | **Worker D: `agy`** | Gemini 3.8 Flash (`thtung-agy`) | 13 | 16 | 16 | 16 | 19 | **80 / 100** | **Đồ Họa Chiến Đấu Hiện Đại:** Radar Bát Quái, đạn neon, glassmorphism |
| **8** | **Worker B: `mini`** | DeepSeek V4.1 (`thtung-paid`) | 15 | 17 | 13 | 17 | 16 | **78 / 100** | **Siêu Tiết Kiệm Token:** Hoàn thành với số step ít hơn 32%, chữ Hán thư pháp |

---

## 3. Đánh Giá Chi Tiết Từng Worker

### 🥇 Hạng 1: Worker E — Meta Muse Code (`muse-spark-1.3-contributor`) [93/100]
* **Điểm mạnh:**
  - **Tốc độ khung hình cao nhất toàn đoàn:** Đạt **59.9 FPS** trong môi trường headless Chromium (1% low 29.9 FPS), thời gian step 0.053 ms.
  - **Khả năng tự phát hiện lỗi logic sâu:** Tự chẩn đoán và vá lỗi ticker game ghi đè BGM mỗi frame khiến nhạc Ma Vực bị trả về Rừng Trúc khi vào Endless Mode.
  - **Thiết kế công thái học (HUD UX):** Dải thanh trạng thái tinh tế ở đỉnh, Action Bar 6 ô chiêu thức trực quan đếm cooldown ở đáy. Nhân vật Tu Sĩ mang đậm bản sắc văn hóa Việt Nam (nón lá truyền thống).
* **Hạn chế:** Phụ thuộc vào hạn mức tài khoản Meta, bắt buộc khóa cứng model `muse-spark-1.3-contributor` và cờ `--yolo`.

### 🥈 Hạng 2: Worker C — OpenCode (`GLM-5.3-Flash`) [90/100]
* **Điểm mạnh:**
  - **Vô địch tối ưu hóa bundle và tốc độ mô phỏng:** Bundle JS chính chỉ **344.6 kB** (gọn nhất trong 8 bên); thời gian mô phỏng mỗi step chỉ **0.0139 ms** (nhanh gấp 4.5 lần mức trung bình) nhờ cơ chế zero-allocation in-place compaction.
  - **Bộ test E2E phong phú:** 23 Playwright tests bao quát đa dạng kịch bản. Chi phí token cực kỳ rẻ qua 9Router.
* **Hạn chế:** Cần chặn cờ `--variant minimal` ngay từ đầu để tránh bẫy suy nghĩ quá sâu vượt trần 32.000 reasoning tokens của BigModel.

### 🥉 Hạng 3: Worker F — Claude Code (`DeepSeek V4.1 Flash`) [87/100]
* **Điểm mạnh:**
  - **Kỷ lục tuyệt đối về độ phủ kiểm thử:** Viết tới **284 unit tests** + **60 Playwright tests** (gấp 2-3 lần các worker thông thường).
  - **Tự sửa 3 lỗi sâu nguy hiểm:** Sửa công thức anchor lệch hitbox sprite, sửa lỗi thiếu texture quái triệu hồi làm crash ticker scene, tự thiết kế cơ chế "Boss Arena" dọn quái thường để đòn đánh không bị loãng.
* **Hạn chế:** Tốc độ thực thi trung bình do test suite quá đồ sộ; cần cờ `IS_SANDBOX=1` để bỏ qua root check.

### 🥉 Hạng 3: Worker G — Kimi Code (`Kimi K3`) [87/100]
* **Điểm mạnh:**
  - **Kỷ luật quản lý tác vụ (Task Planning) xuất sắc:** Sử dụng công cụ TodoList tự phân rã và cập nhật trạng thái liên tục; mô phỏng logic cực nhanh (**0.038 ms/step**).
  - **Giao diện tinh gọn:** Quái vật có hiển thị lượng máu trực tiếp (HP 10), thanh máu phụ trên đầu nhân vật (overhead HP bar).
* **Hạn chế:** Nhạy cảm với timeout của tool khi hệ thống chịu tải cao; cần cấu hình chuẩn `config.toml` trỏ về loopback 9Router.

### 5. Worker A — DeepSeek Harness (`DeepSeek V4.1 Flash`) [85/100]
* **Điểm mạnh:** Tự chủ và tự gỡ lỗi (Self-healing) xuất sắc; tự viết script `.dbg.mjs` chẩn đoán lỗi sâu trong core/DOM/audio; test suite Vitest mock sạch chạy siêu tốc (1.02s / 146 tests); đóng gói CI/CD 1 lệnh (`npm run verify`).
* **Hạn chế:** Tốn nhiều bước suy luận (826 steps / 5 phase do tính cầu toàn lặp lại); bundle lớn hơn (~500 kB JS).

### 6. Worker H — OpenAI Codex CLI (`DeepSeek V4.1 Flash`) [81/100]
* **Điểm mạnh:** Tự chủ dòng lệnh shell rất cao; tính toán công thức scale quái vật lũy tiến trong Endless Mode cực kỳ chính xác; tốc độ step nhanh (**0.138 ms/step**); bundle rất gọn (**381.5 kB**).
* **Hạn chế:** Dễ tràn ngữ cảnh nếu nạp ảnh chụp màn hình thô (cần prompt chỉ thị cấm nạp base64 image vào context).

### 7. Worker D — Google Antigravity (`Gemini 3.8 Flash`) [80/100]
* **Điểm mạnh:** Đồ họa chiến đấu và giao diện UI đẹp mắt, hiện đại nhất: hệ thống vòng tròn radar/trận pháp Bát Quái phân tầng; đạn đạo neon phát sáng; tự động xoay tua 3 tài khoản Google OAuth chống 429.
* **Hạn chế:** Số lượng unit test ở mức cô đọng theo brief (51 tests); phụ thuộc keyring Google OAuth.

### 8. Worker B — mini-SWE-agent (`DeepSeek V4.1 Flash`) [78/100]
* **Điểm mạnh:** Tiết kiệm token/bước vượt trội (564 steps / 5 phase, ít hơn ~32%); bundle production cực kỳ gọn nhẹ (~434 kB); mỹ thuật chữ Hán thư pháp sáng tạo.
* **Hạn chế:** Tự chủ môi trường yếu hơn (từng lạc workspace sang `/tmp`); chạy test Vitest chậm (19s do mock/warnings).

---

## 4. Ma Trận Quyết Định Lựa Chọn Worker (Routing Decision Matrix)

| Nhu cầu bài toán | Worker khuyến nghị hàng đầu | Lý do lựa chọn |
|---|---|---|
| **Game / UI cần vòng lặp 60 FPS mượt mà & HUD công thái học** | **Worker E (Muse Code)** | FPS cao nhất (59.9), HUD Action Bar khoa học, tự vá lỗi ticker vòng lặp. |
| **Web Frontend / Mobile khắt khe về Bundle (<350kB) & Tốc độ thuật toán** | **Worker C (OpenCode + GLM 5.3)** | Vô địch bundle (344 kB), thuật toán zero-allocation siêu tốc (0.0139 ms/step). |
| **Dự án quy mô lớn đòi hỏi an toàn hồi quy tuyệt đối (Regression Safety)** | **Worker F (Claude Code + DeepSeek)** | Bộ test đồ sộ nhất (284 unit + 60 E2E), tự phát hiện và sửa lệch hitbox/textures ngầm. |
| **Quy trình phát triển phân rã nhiều bước chặt chẽ (Task Breakdown)** | **Worker G (Kimi Code + Kimi K3)** | Quản lý tác vụ qua TodoList nghiêm ngặt, mô phỏng logic cực nhanh (0.038 ms/step). |
| **Dự án cần tự động hóa CI/CD & Self-healing trong headless build** | **Worker A (DeepSeek Harness)** | Tự viết script debug `.dbg.mjs`, unit test chạy siêu tốc 1.02s. |
| **Tính toán cân bằng chỉ số lũy tiến (Math Balance & Endless Scaling)** | **Worker H (OpenAI Codex + DeepSeek)** | Tự chủ môi trường shell, tính toán công thức toán học chính xác, bundle gọn. |
| **Giao diện thương mại bóng bẩy, đạn đạo neon & xử lý context lớn** | **Worker D (Google Antigravity + Gemini)** | Thẩm mỹ hiện đại glassmorphism, radar Bát Quái, context 1M+ tokens. |
| **Triển khai tính năng nhanh gọn, số lượng lớn với chi phí token tối thiểu** | **Worker B (mini-SWE-agent + DeepSeek)** | Tiết kiệm 32% số bước và chi phí token, hoàn thành task gọn gàng. |
