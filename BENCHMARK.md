# Đo hiệu quả worker: công thức + phương pháp

Mục đích: trả lời một câu duy nhất — **luồng worker mới có hơn baseline không,
và hơn bao nhiêu**. Không đo cảm tính, không hỏi model "mày là ai" (cả hàng
chính hãng cũng trả lời lung tung câu đó).

## Nguyên tắc vàng

Cùng tasks, cùng số attempts, chỉ đổi **một biến duy nhất** (harness hoặc
model). Mọi thứ khác giữ nguyên: provider endpoint, reasoning effort, timeout.

```text
RUN A   Hermes → DeepSeek
RUN B   mini-SWE → DeepSeek        (đổi harness, giữ model)
RUN C   Hermes → mini-SWE → DeepSeek
```

## Metrics (giữ đúng 4 số + 2 số verifier)

- **Pass@1** = `số attempt pass / tổng số attempt`. Mỗi attempt chạy độc lập.
- **Pass@k** = `số task có ≥1 attempt pass / tổng số task`. Đo độ ổn định.
- **F2P** (fail-to-pass): test hỏng trước, phải pass sau fix — càng cao càng tốt.
- **P2P** (pass-to-pass): test đã pass, phải giữ pass (không regression).
- **Avg cost / task**: tiền model chia cho số task.
- **Avg output tokens / task** và **avg wall time / task**: rẻ + nhanh mới thắng.

Ví dụ bảng quyết định:

```text
DeepSWE 10-task smoke × 3

                     PASS@1    COST/TASK   TIME/TASK
Hermes + DeepSeek    63.3%     $0.018      88s
mini-SWE + DeepSeek  76.7%     $0.021      72s
Hermes→mini-SWE      73.3%     $0.024      78s
```

Con nào không thắng baseline thì **loại ngay**, khỏi build thêm.

## Thứ tự đo (rẻ trước, đắt sau)

1. **DeepSWE smoke**: 10 task × 3 attempts = 30 runs (~1–1.5h, 4 luồng).
   Đúng nhất cho feature/bug/refactor.
2. Config nào thắng mới chạy **full DeepSWE**: 113 × 3 = 339 runs (nhiều giờ).
3. Rồi **Terminal-Bench 4.0** (terminal/autonomous), cuối **SWE-Atlas-QnA**
   (hiểu codebase). Trung bình đều 3 điểm = kiểu Artificial Analysis Coding
   Agent Index.

## Công cụ

- **Pier** là runner official cho DeepSWE. Subset deterministic:
  `pier run -p deep-swe/tasks -l 10 --sample-seed 0 -k 3`.
- **Harbor** cho Terminal-Bench (`terminal-bench/terminal-bench@4.0.0`) và
  SWE-Atlas. Validate infra bằng agent `oracle` trước — oracle fail thì lỗi
  environment, chưa phải lỗi agent.
- Đừng tự viết benchmark runner, chỉ viết **adapter** nhét harness của mình
  vào Pier/Harbor (custom agent).

## Lệnh chuẩn (DeepSWE smoke qua 9Router)

```bash
# key 9Router trong file 0600, KHÔNG bake vào image
printf 'OPENAI_API_KEY=%s\nOPENAI_BASE_URL=https://router.cutes1tg.online/v1\nMSWEA_COST_TRACKING=ignore_errors\n' \
  "$(sqlite3 /root/ai-services/data-9router/db/data.sqlite 'SELECT key FROM apiKeys LIMIT 1')" \
  > /root/ops/bench-9r.env
chmod 600 /root/ops/bench-9r.env

pier run -p deep-swe/tasks -l 10 --sample-seed 0 \
  -a mini-swe-agent -m openai/<prefix>/<model> \
  --ak model_class=litellm -k 3 -n 4 \
  -o /root/ops/bench-jobs --env-file /root/ops/bench-9r.env -y
```

## Pitfalls đã dính thật (2026-09-15)

1. Pier mặc định `model_class=litellm_response` (Responses API) **crash khi qua
   9Router** — lỗi parse SSE `response.completed` → `NonZeroAgentExitCodeError`,
   F2P = 0. Fix: `--ak model_class=litellm` (chat completions).
2. Agent container cần gọi ra endpoint model: dùng **public URL**
   (`https://router.cutes1tg.online/v1`) qua `--env-file`, vì `127.0.0.1`
   trong container là chính nó, còn `host.docker.internal` không resolve trên
   host này.
3. Hỏi model "mày là model nào" là test vô giá trị: model chính hãng
   (deepseek-flash qua api.deepseek.com) cũng trả lời né tránh/xưng sai.
   Suy model bằng **kiến thức dài hạn + điểm benchmark**, không bằng self-claim.
4. Combo trên gateway có thể bị đổi giữa chừng (DB WAL mới) — trước mỗi run
   đọc lại `combos` và ghi leg thực tế vào kết quả, kẻo đo nhầm model.
5. `thtung-muse` qua JSON chat thường trả `content:''` — benchmark harness nào
   dùng JSON-only sẽ đo sai leg này; phải đi Responses/stream.

## 9 config smoke (bài gốc)

```text
1. Hermes → Muse            4. Hermes → DeepSeek          7. Hermes → GLM
2. Muse Code → Muse         5. mini-SWE → DeepSeek        8. DSH Headless → GLM
3. Hermes → Muse Code → Muse  6. Hermes → mini-SWE → DeepSeek  9. Hermes → DSH → GLM
```

9 × 10 × 3 = **270 runs**. Đắt thì cắt còn 5 task × 3 trước.
Top configs mới lên full 113.

---

## Benchmark Đối đầu Thực tế Toàn diện: 5 Workers (Vạn Kiếp Tu Tiên P1–P5)

*Ngày thực hiện: 2026-10-20*  
*Môi trường: Linux VPS Ubuntu (66.135.0.13), Node.js LTS 26.8.2, PixiJS v8.22.0, Vite 6, TypeScript strict, Vitest, Playwright*  
*Nhiệm vụ: Phát triển trọn vẹn game roguelite 2D top-down "Vạn Kiếp Tu Tiên" từ cùng starter repository sạch qua 5 giai đoạn (P1–P5) đạt chuẩn 18 gates kỹ thuật (T01–T18).*

### 1. Bảng số liệu đo lường định lượng chung cuộc (5 Workers)

| Hạng mục Đo đạc | Worker A: `dsh` (DeepSeek V4.1) | Worker B: `mini` (DeepSeek V4.1) | Worker C: `opencode` (GLM 5.3) | Worker D: `agy` (Gemini 3.8) | Worker E: `muse` (Muse Spark 1.3 Contributor) | Đánh giá & Ưu thế |
|---|---|---|---|---|---|---|
| **Độ phủ Unit tests (Vitest)** | 146 tests / 17 files (1.02s) | 102 tests / 12 files (19.30s) | 142 tests / 14 files (3.26s) | 51 tests / 12 files (1.19s) | **107 tests / 16 files (2.74s)** | Worker A & C dày nhất; E cân bằng test/tốc độ |
| **Độ phủ E2E (Playwright)** | 19 tests (58.3s) | 18 tests (34.2s) | **23 tests (45.5s)** | 3 suites tổng hợp (21.4s) | 9 tests (28.3s) | Worker C sâu nhất; E bao quát 22 tiêu chí |
| **Tỷ lệ 18 Gates (T01–T18)** | **18 / 18 PASS (100%)** | **18 / 18 PASS (100%)** | **18 / 18 PASS (100%)** | **18 / 18 PASS (100%)** | **18 / 18 PASS (100%)** | Cả 5 đều hoàn thành 100% chuẩn chỉ |
| **Lỗi Console (0 Error)** | **0 errors** | **0 errors** | **0 errors** | **0 errors** | **0 errors** | Tuyệt đối sạch trên cả 5 |
| **Kích thước Bundle JS chính** | 500.0 kB (152.1 kB gzip) | 434.0 kB (133.0 kB gzip) | **344.6 kB (106.4 kB gzip)** | 463.6 kB (134.0 kB gzip) | **366.3 kB (114.7 kB gzip)** | Worker C nhẹ nhất; Worker E đứng thứ hai |
| **Tổng dung lượng Assets** | 788 KiB | ~720 KiB | **~614 KiB** | ~680 KiB | **~656 KiB** | Worker C & E tối ưu dung lượng tốt nhất |
| **Procedural Audio API** | Có (3 map BGM, 9 SFX) | Có (BGM ngũ cung, SFX) | Có (3 map BGM, 8 SFX) | Có (3 map BGM, SFX) | **Có (3 map BGM, 9 SFX)** | 100% không asset ngoài tải chậm |
| **Mô phỏng 500 quái (T12)** | 0.063 ms/step | 0.065 ms/step | **0.0139 ms/step** | 0.1345 ms/step | 0.0530 ms/step (p99 0.311) | Worker C vô địch; Worker E ổn định dưới 0.1ms |
| **Đỉnh RAM JS Heap Browser** | 95.70 MB | 88.40 MB | **~10 MB (9.54 MB)** | **~10 MB (9.54 MB)** | **42.63 MB** | Worker C & D nhẹ nhất; E cân đối đồ họa/RAM |
| **FPS Headless Chromium** | ~18 FPS (1% low 13) | ~7.5 FPS (1% low 6.6) | 23.4 FPS (1% low 17.6) | 20.0 FPS (1% low 8.57) | **59.9 FPS (1% low 29.9)** | Worker E frame rate mượt mà và ổn định nhất |
| **Cổng Preview trực tiếp VPS** | `:39101` | `:39102` | `:39103` | `:39104` | **`:39105`** | Sẵn sàng trải nghiệm cả 5 bản |

### 2. So sánh Đặc tính Kỹ thuật 5 Bên

#### Worker A: `@deepseek-ai/dsh` (DeepSeek V4.1 Flash)
* **Thế mạnh:** Tự chủ và tự gỡ lỗi (Self-healing) xuất sắc; tự viết script `.dbg.mjs` chẩn đoán lỗi sâu trong core/DOM/audio; test suite Vitest mock sạch chạy siêu tốc (1.02s); UI Master-Detail và vector silhouette hoàn thiện không lỗi layout; đóng gói CI/CD 1 lệnh (`npm run verify`).
* **Hạn chế:** Tốn nhiều bước suy luận (826 steps / 5 phase do tính cầu toàn lặp lại); bundle lớn hơn (~500 kB JS).

#### Worker B: `mini-swe-agent` (DeepSeek V4.1 Flash)
* **Thế mạnh:** Tốc độ thực thi chớp nhoáng, tiết kiệm token/bước vượt trội (564 steps / 5 phase, ít hơn ~32%); bundle gọn nhẹ (434 kB); mỹ thuật chữ Hán thư pháp độc đáo; văn phong bản địa hóa tu chân kèm chú thích công thái học (`(Restart)`, `(Về Menu)`).
* **Hạn chế:** Tự chủ môi trường kém hơn (từng lạc workspace sang `/tmp`); chạy unit test chậm (19s do cảnh báo localStorage); sót lỗi tràn thanh cuộn che quái ở Bestiary.

#### Worker C: `opencode` (GLM-5.3-Flash)
* **Thế mạnh:** **Tối ưu hóa bundle và hiệu năng mô phỏng vô địch**: bundle JS chính chỉ **344.6 kB** (gọn nhất trong cả 5 bên); thời gian mô phỏng mỗi step chỉ **0.0139 ms** (nhanh gấp 4.5 lần Worker A); bộ test E2E phong phú nhất (23 Playwright tests); tự động nhận diện và sửa lỗi bất đồng bộ của engine PixiJS.
* **Hạn chế:** Cần chặn cờ `--variant minimal` ngay từ đầu để tránh việc mô hình suy nghĩ quá sâu vượt trần 32.000 reasoning tokens của BigModel.

#### Worker D: `agy` (Google Antigravity Native — Gemini 3.8 Flash)
* **Thế mạnh:** **Đồ họa chiến đấu và giao diện UI đẹp mắt, hiện đại nhất**: hệ thống vòng tròn radar/trận pháp Bát Quái phân tầng biểu thị tầm đánh tự động; đạn đạo kiếm khí phát sáng neon; tự động bổ sung culling tối ưu khung hình; hoàn thành bài toán nhanh gọn và kỷ luật.
* **Hạn chế:** Phụ thuộc vào cơ chế xác thực Google OAuth (keyring/interactive auth); bộ test unit bao quát vừa đủ theo brief (51 tests) chứ không tự viết dày đặc như A hay C.

#### Worker E: `muse` (Meta Muse Code — `muse-spark-1.3-contributor`)
* **Thế mạnh:** **Bố cục công thái học (HUD UX), bản sắc Việt Nam và tốc độ khung hình (FPS) mượt nhất**:
  - Tự động phát hiện lỗi ngầm: ticker game ghi đè BGM mỗi frame làm rớt nhạc Ma Vực khi vào Endless Mode $\rightarrow$ tự debug và sửa triệt để trước khi nghiệm thu.
  - Bố cục HUD gọn gàng khoa học nhất: dải thanh trạng thái ngang tinh tế ở đỉnh, Action Bar 6 ô kỹ năng rõ ràng kèm đếm thời gian hồi chiêu ở đáy.
  - Tạo hình nhân vật Tu Sĩ mang đậm bản sắc văn hóa Việt Nam (đội nón lá truyền thống, áo đạo bào xanh ngọc thắt lưng vàng).
  - Tốc độ render Chromium headless đạt **59.9 FPS** (1% low 29.9 FPS), thời gian step **0.053 ms**, dung lượng bundle JS đứng thứ 2 (**366.3 kB**).
* **Hạn chế:** Bắt buộc phải khóa cứng model `muse-spark-1.3-contributor` và cờ `--yolo` để tránh kẹt hàng đợi phê duyệt lệnh headless.

### 3. Tiêu chuẩn Định tuyến Lead (Routing Decision)
* **Chọn Worker A (`dsh`):** Khi cần xây dựng logic phức tạp, hệ thống engine lõi đòi hỏi test suite đồ sộ, chạy CI/CD tốc độ cao và cần UI hoàn chỉnh thương mại.
* **Chọn Worker B (`mini`):** Khi cần triển khai tính năng nhanh gọn, tiết kiệm chi phí gọi mô hình LLM, và tối ưu dung lượng cho web/mobile nhẹ nhàng.
* **Chọn Worker C (`opencode` + GLM 5.3):** Khi cần tối ưu dung lượng bundle ở mức tối đa, logic toán học/mô phỏng hiệu năng cực cao và viết test suite bao quát sâu.
* **Chọn Worker D (`agy` + Gemini 3.8):** Khi cần thẩm mỹ giao diện cao cấp, đồ họa chiến đấu trực quan, xử lý context lớn và hệ thống an toàn đa tầng của Google.
* **Chọn Worker E (`muse` + Muse Spark 1.3 Contributor):** Khi cần thiết kế UI công thái học đỉnh cao, bố cục game khoa học, frame rate mượt mà và khả năng tự phát hiện lỗi logic sâu trong vòng lặp game.

