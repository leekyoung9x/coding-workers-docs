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

## Benchmark Đối đầu Thực tế: `@deepseek-ai/dsh` vs `mini-swe-agent` (Vạn Kiếp Tu Tiên P1–P5)

*Ngày thực hiện: 2026-10-20*  
*Môi trường: Linux VPS Ubuntu (66.135.0.13), Node.js LTS 26.8.2, PixiJS v8.22.0, Vite 6, TypeScript strict, Vitest, Playwright*  
*Model dùng chung: DeepSeek V4.1 Flash 1017 (combo `thtung-paid` qua 9Router 127.0.0.1:20127)*  
*Nhiệm vụ: Phát triển trọn vẹn game roguelite 2D top-down "Vạn Kiếp Tu Tiên" từ starter repository sạch qua 5 giai đoạn (P1–P5) đạt chuẩn 18 gates kỹ thuật (T01–T18).*

### 1. Bảng số liệu đo lường định lượng

| Hạng mục Đo đạc | Worker A: `@deepseek-ai/dsh` | Worker B: `mini-swe-agent` | Đánh giá & Ưu thế |
|---|---|---|---|
| **Tổng số bước (Steps P1 → P5)** | 826 steps (122 + 85 + 170 + 234 + 215) | **564 steps** (64 + 86 + 99 + 132 + 183) | **Worker B tiết kiệm bước hơn 31.7%** |
| **Độ phủ Unit tests (Vitest)** | **146 tests / 17 files** (chạy trong **1.02s**) | 102 tests / 12 files (chạy trong 19.30s) | **Worker A vượt trội (chạy nhanh hơn x18.9 lần)** |
| **Độ phủ E2E Tests (Playwright)** | **19 tests** (chạy trong 58.3s) | 18 tests (chạy trong 34.2s) | **Worker A sâu hơn / Worker B chạy nhanh hơn** |
| **Tỷ lệ đạt chuẩn 18 Gates (T01–T18)** | **18 / 18 PASS (100%)** | **18 / 18 PASS (100%)** | Ngang nhau tuyệt đối |
| **Lỗi Console (0 Console/Page errors)** | **0 errors** | **0 errors** | Hoàn hảo trên cả hai |
| **Kích thước Bundle JS chính** | 500.0 kB (511.8 kB raw, 152.1 kB gzip) | **434.0 kB** (443.9 kB raw, 133.0 kB gzip) | **Worker B gọn hơn ~13%** |
| **Tổng dung lượng Assets** | 788.22 KiB (10 files) | **~720 KiB** (10 files) | **Worker B tối ưu bundle hơn** |
| **Tài nguyên âm thanh ngoài** | **0 byte / 0 request** (Web Audio API) | **0 byte / 0 request** (Web Audio API) | Chuẩn procedural tuyệt đối |
| **Stress test 500 quái (Node sim 60s)** | **0.063 ms/step** (p99: 0.518 ms) | 0.065 ms/step (p99: 0.540 ms) | **Worker A nhỉnh hơn nhẹ** |
| **Đỉnh bộ nhớ JS Heap (Browser Peak)** | 95.70 MB | **88.40 MB** | **Worker B tiết kiệm RAM hơn** |
| **Đỉnh bộ nhớ JS Heap (Node Engine)** | 41.30 MB (used: 35.12 MB) | **38.90 MB** (used: 31.20 MB) | **Worker B gọn hơn** |

### 2. So sánh Tổng quát Mạnh — Yếu 2 Bên

#### Worker A: `@deepseek-ai/dsh`
* **Điểm mạnh:**
  - **Khả năng tự chủ và tự sửa lỗi (Self-healing) xuất sắc:** Khi gặp ca khó (i-frame bất tử làm kẹt kịch bản test, đè lớp giao diện modal), `dsh` tự viết file chẩn đoán `.dbg.mjs`, lần ra tận gốc vấn đề trong core game và tự bổ sung API gỡ lỗi mà không cần can thiệp bên ngoài.
  - **Bộ test chất lượng cao, chạy siêu tốc:** 146 unit tests hoàn thành chỉ trong **1.02 giây** (nhờ kiến trúc mock sạch, độc lập), cùng 19 bài test E2E Playwright bao quát sâu cả thao tác kéo chuột và cảm ứng.
  - **Đồ họa và UI hoàn thiện không tì vết:** Bách Yêu Đồ thiết kế dạng Master-Detail chuyên nghiệp, 11 yêu thú đều có hình khối vector vẽ tay riêng biệt và đủ thông số. Màn hình Bại trận hiển thị chi tiết toàn bộ 9 kỹ năng đã build, hệ số quái và kỷ lục sống sót.
  - **Quy trình đóng gói tự động hóa mẫu mực:** Tích hợp trọn gói pipeline kiểm thử và xuất báo cáo chỉ bằng một lệnh duy nhất (`npm run verify` hoặc `npm run artifacts`).
* **Điểm yếu:**
  - **Tốn nhiều bước suy luận (steps):** Mất tổng cộng 826 steps qua 5 giai đoạn (nhiều hơn Worker B 46%), do agent có xu hướng kiểm tra đi kiểm tra lại rất kỹ.
  - **Kích thước bundle lớn hơn:** File JS chính chạm ngưỡng 500 kB (vừa khít cảnh báo của Vite, trong khi Worker B chỉ 434 kB).
  - **Mức chiếm dụng bộ nhớ nhỉnh hơn:** Đỉnh RAM trình duyệt đo được là 95.7 MB (Worker B là 88.4 MB).

#### Worker B: `mini-swe-agent`
* **Điểm mạnh:**
  - **Tiết kiệm bước và chi phí token vượt trội:** Hoàn thành toàn bộ 5 giai đoạn chỉ với **564 steps** (nhanh và tiết kiệm bước hơn Worker A gần 32%).
  - **Tối ưu hóa bundle và tài nguyên tốt:** File JS chính chỉ nặng **434 kB** (nhỏ hơn Worker A ~13%), đỉnh RAM trình duyệt thấp hơn (~88.4 MB), bundle nhẹ và tải nhanh.
  - **Mỹ thuật Tiên hiệp và Văn phong nhập vai ấn tượng:** Tàng Kinh Các sáng tạo vượt bậc với hệ thống 12 icon chữ Hán thư pháp đổi màu theo nguyên tố; câu từ tu chân bản địa hóa xuất sắc kèm chú thích công năng công thái học (`Tái Khởi (Restart)`, `Đắc Đạo Thăng Thiên (Về Menu)`).
* **Điểm yếu:**
  - **Tự chủ môi trường kém hơn:** Có giai đoạn bị mất phương hướng workspace (tự ý tạo `/tmp/p1` để clone git), lệnh kết thúc bị lỗi cú pháp exit code -1 phải nhờ Lead dọn dẹp.
  - **Tốc độ chạy test rất chậm:** 102 unit tests mất tới **19.3 giây** (chậm hơn Worker A gần 19 lần) do chưa tối ưu mock bộ nhớ và dính cảnh báo localStorage của Node.
  - **Sót lỗi giao diện (UI bugs):** Màn hình Bách Yêu Đồ bị tràn thanh cuộn che khuất 4 quái đầu tiên và thiếu chỉ số tấn công; bảng Cài đặt bị đặt thừa nút Mute bên cạnh checkbox.

### 3. Tiêu chuẩn Lựa chọn / Định tuyến cho Lead (Routing Decision)
* **Chọn Worker A (`dsh`):** Khi cần xây dựng logic phức tạp, hệ thống engine lõi đòi hỏi test suite đồ sộ, chạy CI/CD tốc độ cao và cần UI hoàn chỉnh thương mại.
* **Chọn Worker B (`mini-swe-agent`):** Khi cần triển khai tính năng nhanh gọn, tiết kiệm chi phí gọi mô hình LLM, và tối ưu dung lượng cho web/mobile nhẹ nhàng.

