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

## Benchmark Đối đầu Thực tế Toàn diện: 8 Workers (Vạn Kiếp Tu Tiên P1–P5)

*Ngày thực hiện: 2026-10-20*  
*Môi trường: Linux VPS Ubuntu (66.135.0.13), Node.js LTS 26.8.2, PixiJS v8.22.0, Vite 6, TypeScript strict, Vitest, Playwright*  
*Nhiệm vụ: Phát triển trọn vẹn game roguelite 2D top-down "Vạn Kiếp Tu Tiên" từ cùng starter repository sạch qua 5 giai đoạn (P1–P5) đạt chuẩn 18 gates kỹ thuật (T01–T18).*

### 1. Bảng số liệu đo lường định lượng chung cuộc (8 Workers)

| Hạng mục Đo đạc | Worker A: `dsh` (DS V4.1) | Worker B: `mini` (DS V4.1) | Worker C: `opencode` (GLM 5.3) | Worker D: `agy` (Gemini 3.8) | Worker E: `muse` (Muse Contrib) | Worker F: `claude` (DS V4.1) | Worker G: `kimi` (Kimi K3) | Worker H: `codex` (DS V4.1) |
|---|---|---|---|---|---|---|---|---|
| **Độ phủ Unit tests (Vitest)** | 146 tests (1.02s) | 102 tests (19.3s) | 142 tests (3.26s) | 51 tests (1.19s) | 107 tests (2.74s) | **284 tests (kỷ lục)** | 180 tests (1.2s) | 128 tests (3.25s) |
| **Độ phủ E2E (Playwright)** | 19 tests (58.3s) | 18 tests (34.2s) | 23 tests (45.5s) | 3 suites (21.4s) | 9 tests (28.3s) | **60 tests (đồ sộ nhất)** | 20 tests (32.7s) | 22 tests (54.6s) |
| **Tỷ lệ 18 Gates (T01–T18)** | **18/18 PASS** | **18/18 PASS** | **18/18 PASS** | **18/18 PASS** | **18/18 PASS** | **18/18 PASS** | **18/18 PASS** | **18/18 PASS** |
| **Lỗi Console (0 Error)** | **0 errors** | **0 errors** | **0 errors** | **0 errors** | **0 errors** | **0 errors** | **0 errors** | **0 errors** |
| **Bundle JS chính** | 500.0 kB | 434.0 kB | **344.6 kB (gọn nhất)** | 463.6 kB | 366.3 kB | 436.8 kB | 415.8 kB | 381.5 kB |
| **Procedural Audio API** | Có (3 BGM, 9 SFX) | Có (BGM, SFX) | Có (3 BGM, 8 SFX) | Có (3 BGM, SFX) | Có (3 BGM, 9 SFX) | Có (3 BGM, 8 SFX) | Có (3 BGM, 16 SFX) | Có (3 BGM, SFX) |
| **Mô phỏng 500 quái (T12)** | 0.063 ms/step | 0.065 ms/step | **0.0139 ms/step** | 0.1345 ms/step | 0.0530 ms/step | 0.2660 ms/step | **0.0380 ms/step** | 0.1380 ms/step |
| **Đỉnh RAM JS Heap** | 95.7 MB | 88.4 MB | **9.54 MB** | **9.54 MB** | 42.6 MB | 26.3 MB | 16.3 MB | 80.2 MB |
| **FPS Headless Chromium** | ~18 FPS | ~7.5 FPS | 23.4 FPS | 20.0 FPS | **59.9 FPS (mượt nhất)** | ~14 FPS | ~15 FPS | ~6.0 FPS |
| **Cổng Preview / Subpath** | `:39101` (`/worker-a/`) | `:39102` (`/worker-b/`) | `:39103` (`/worker-c/`) | `:39104` (`/worker-d/`) | `:39105` (`/worker-e/`) | `:39106` (`/worker-f/`) | `:39107` (`/worker-g/`) | `:39108` (`/worker-h/`) |

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


#### Worker F: `claude` CLI (DeepSeek V4.1 Flash qua 9Router Messages API)
* **Thế mạnh:** **Vô địch tuyệt đối về độ phủ kiểm thử**: **284 unit tests** + **60 Playwright tests** (gấp 2-3 lần các worker thông thường). Cơ chế tự chẩn đoán sâu: tự phát hiện và sửa lệch sprite hitbox formula, tự thêm texture cho minion triệu hồi (sapling, clone) chống crash ticker, tạo cơ chế "boss arena" dọn quái thường để tránh loãng đòn đánh.
* **Hạn chế:** Tốc độ thực thi trung bình do chạy test suite quá đồ sộ; cần cờ `IS_SANDBOX=1` để bỏ qua root check của Claude Code.

#### Worker G: `kimi` CLI (@moonshot-ai/kimi-code v2.3.0 + Kimi K3)
* **Thế mạnh:** **Tự quản lý tác vụ (Task Planning) cực kỳ kỷ luật**: dùng TodoList tool tự phân rã và cập nhật trạng thái liên tục; mô phỏng logic cực nhanh (**0.038 ms/step**); giao diện Flat Card thanh thoát, quái vật có hiển thị lượng máu trực tiếp (HP 10), thanh máu phụ trên đầu nhân vật (overhead HP bar).
* **Hạn chế:** Nhạy cảm với timeout của tool khi hệ thống chịu tải cao; cần cấu hình chuẩn `config.toml` trỏ về loopback 9Router.

#### Worker H: `codex` CLI (OpenAI Codex v0.158.0 + DeepSeek V4.1 qua Responses API)
* **Thế mạnh:** **Khả năng tự chủ trong môi trường shell và tính toán toán học chính xác**: tự tính toán công thức scale quái vật lũy tiến trong Endless Mode, tốc độ mô phỏng nhanh (**0.138 ms/step**), bundle rất gọn (**381.5 kB**), tự động cấu hình test runner độc lập với 128 unit tests và 22 Playwright tests.
* **Hạn chế:** Dễ bị tràn ngữ cảnh token nếu gọi tool `view_image` tải ảnh base64 thô (cần prompt chỉ thị cấm nạp ảnh thô vào context).

### 3. Tiêu chuẩn Định tuyến Lead (Routing Decision)
* **Chọn Worker A (`dsh`):** Khi cần xây dựng logic phức tạp, hệ thống engine lõi đòi hỏi test suite đồ sộ, chạy CI/CD tốc độ cao và cần UI hoàn chỉnh thương mại.
* **Chọn Worker B (`mini`):** Khi cần triển khai tính năng nhanh gọn, tiết kiệm chi phí gọi mô hình LLM, và tối ưu dung lượng cho web/mobile nhẹ nhàng.
* **Chọn Worker C (`opencode` + GLM 5.3):** Khi cần tối ưu dung lượng bundle ở mức tối đa, logic toán học/mô phỏng hiệu năng cực cao và viết test suite bao quát sâu.
* **Chọn Worker D (`agy` + Gemini 3.8):** Khi cần thẩm mỹ giao diện cao cấp, đồ họa chiến đấu trực quan, xử lý context lớn và hệ thống an toàn đa tầng của Google.
* **Chọn Worker E (`muse` + Muse Spark 1.3 Contributor):** Khi cần thiết kế UI công thái học đỉnh cao, bố cục game khoa học, frame rate mượt mà và khả năng tự phát hiện lỗi logic sâu trong vòng lặp game.
* **Chọn Worker F (`claude` + DeepSeek V4.1):** Khi cần xây dựng hệ thống quy mô lớn đòi hỏi kiểm thử bao quát tối đa (Regression Safety), tự tìm và sửa các lỗi lệch hitbox, boundary conditions sâu.
* **Chọn Worker G (`kimi` + Kimi K3):** Khi dự án cần lập trình theo quy trình TodoList chặt chẽ, chia nhỏ task, tối ưu tốc độ thuật toán mô phỏng (0.038 ms/step) và UI gọn gàng.
* **Chọn Worker H (`codex` + DeepSeek V4.1):** Khi cần tự chủ dòng lệnh shell, triển khai các thuật toán cân bằng chỉ số toán học lũy tiến (Endless scaling) và giữ kích thước bundle tối giản.


---

## 4. Tiêu Chuẩn Đánh Giá Mới Cho Giai Đoạn P6: Tỷ Lệ Áp Dụng PixiJS AI Skills (% Skill Utilization)

Khi nâng cấp lên Giai đoạn P6 (Engine & Visual Foundation), cả 8 worker đều được cung cấp thư mục `./skills/` chứa đầy đủ 26 AI Skills chính thức của PixiJS v8 (`https://github.com/pixijs/pixijs-skills`).

### Phương Pháp Đo Lường & Chấm Điểm Thực Tiễn:
1. **Không chấm điểm hình thức:** Không chấp nhận việc agent chỉ copy thư mục skill vào mà không dùng.
2. **Đối soát AST / Grep Codebase:** Lead Orchestrator quét mã nguồn để kiểm tra các API patterns đặc trưng của từng skill:
   - `pixijs-scene-sprite` -> Sử dụng `NineSliceSprite` dựng khung panel RPG.
   - `pixijs-filters` -> Sử dụng `Filter.from` và `pixi-filters@^6` trên `Container`/`RenderLayer` tập trung.
   - `pixijs-scene-container` -> Sử dụng `isRenderGroup`, `zIndex`, `boundsArea`, `cullable`.
   - `pixijs-performance` -> Gọi `destroy({ children: true, texture: false })`, pooling objects.
   - `pixijs-ticker` -> Sử dụng `ticker.add`, điều phối `deltaTime` và thứ tự ưu tiên render.
   - `pixijs-events` -> Sử dụng `eventMode = 'static'`, `hitArea`, cơ chế pointer drag-to-move.
3. **Chỉ số % Skill Adoption:**
   $$\text{Skill Adoption Rate} = \frac{\text{Số lượng Skill thực sự áp dụng}}{\text{Tổng số Skill liên quan (12 core skills)}} \times 100\%$$
Worker nào có tỷ lệ áp dụng cao nhất kèm chất lượng game mượt mà, không lỗi sẽ được cộng điểm trực tiếp vào bảng xếp hạng P6!
