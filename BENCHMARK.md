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
