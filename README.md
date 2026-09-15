# Coding Workers — Hermes + 9Router

Hermes giữ session/context, Figma MCP FULL, Unity MCP Pro FULL, routing và
final verification. Worker giữ coding loop (repo, shell, test/build/lint).

## Kiến trúc

```text
Discord → Hermes Gateway → Hermes Agent
  │
  │  task rất nhỏ → Hermes tự xử (không gọi worker)
  │
  ├─ task khó / repo lớn / long-horizon → /muse-code
  │     muse-code skill → Muse Code CLI (muse)
  │       → muse-shim generic :8787 (Responses API)
  │       → 9Router combo thtung-muse → Meta Muse Spark 1.3
  │
  ├─ feature / bug / refactor thường → /deepseek-code
  │     deepseek-code skill → mini-SWE-agent (LiteLLM nằm trong nó)
  │       → 9Router combo thtung-paid → DeepSeek V4.1 Flash
  │
  └─ GLM worker → /glm-code
        glm-code skill → opencode CLI
          → 9Router combo thtung-glm → GLM-5.3-Flash

Tất cả worker trả về → Hermes final verify (git diff, test status,
Unity MCP nếu cần) → Discord báo kết quả.
```

## Components

| Gì | Ở đâu | Ghi chú |
|---|---|---|
| skill `muse-code` / `deepseek-code` / `glm-code` | `~/.hermes/skills/<name>/SKILL.md` | trigger + cách chạy + pitfalls |
| `muse` CLI 1.2.1 | `~/.local/bin/muse` | worker native cho Muse |
| muse-shim (source) | `/root/ops/muse-shim/` | luckeyfaraday/muse-shim, generic mode |
| muse-shim (runner) | `/root/ops/muse-shim/run-shim.sh` | đọc key 9Router live từ DB, không lưu key trong file |
| muse-shim (service) | systemd `muse-shim` | `127.0.0.1:8787` → 9Router `/v1/responses`, model `thtung-muse`, auto-restart |
| `mini` 2.4.6 | `/root/.local/bin/mini` (uv tool) | worker cho DeepSeek |
| mini config | `/root/.config/mini-swe-agent/.env` (0600) | `MSWEA_CONFIGURED=true`, `OPENAI_API_BASE=http://127.0.0.1:20127/v1` |
| `opencode` 1.18.31 | `/usr/local/bin/opencode` | worker cho GLM (+ fallback cho Muse) |
| opencode config | `~/.config/opencode/opencode.json` (0600) | provider `ninerouter` → 9Router, models keyed theo combo id |

## Combos (9Router, DB có sẵn — không tạo mới)

| Combo | Entries | Trạng thái đo thật |
|---|---|---|
| `thtung-muse` | `oc/muse-spark-1.3-contributor-free` (+1.2 fallback) | OK qua shim/opencode-stream; JSON thường trả `content:''` |
| `thtung-paid` | `aibox/deepseek-v4.1-flash` | OK, JSON thường, ~1.5s |
| `thtung-glm` | `aibox/zai-org/glm-5.3-flash`, `xq/glm-5.3-flash` | entry 1 chết 503 `model_not_found`, fallback entry 2 sống (~10s) |

## Cách chạy (canonical)

```bash
# Muse — task khó (cần shim service đang active)
muse exec --provider meta --base-url http://127.0.0.1:8787 --model thtung-muse \
  --yolo --json "<task + acceptance criteria>"

# DeepSeek — task thường
MSWEA_SILENT_STARTUP=1 mini --exit-immediately -m openai/thtung-paid \
  -t "<task>. Then echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT as its own command." -y -l 0.5

# GLM
opencode run -m ninerouter/thtung-glm --format json "<task + acceptance criteria>"
```

## Ops

```bash
systemctl is-active muse-shim
curl -s http://127.0.0.1:8787/health
systemctl restart muse-shim   # sau khi sửa run-shim.sh / DB key
```

## Pitfalls (đã dính thật)

1. `muse` cần `muse auth set --provider meta` một giá trị bất kỳ cho qua local
   check — auth thật là key 9Router nằm trong shim. Không cần `muse login`.
2. `thtung-muse` qua JSON chat thường trả rỗng — luôn đi qua shim (Responses)
   hoặc opencode/stream.
3. `opencode run` chỉ đọc GLOBAL config, bỏ qua `./opencode.json` trong cwd.
4. `mini` không có `MSWEA_CONFIGURED=true` sẽ rớt vào setup interactive và treo
   headless — luôn `--exit-immediately -y`, task prompt phải dặn echo
   `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`.
5. Entry GLM `aibox` chết nhưng KHÔNG xóa — combo sống nhờ fallback sang `xq`.
6. DeepSeek reasoning effort là số 1–100, chưa map LOW/HIGH/MAX qua mini.

## Lịch sử verify & Báo cáo đo lường (2026-09-15)

- [Tài liệu Phương pháp & Công thức Benchmark (BENCHMARK.md)](./BENCHMARK.md)
- [Báo cáo Thực nghiệm Đối đầu: mini-SWE vs Hermes Direct & DeepSWE v1.1 (VERIFICATION_REPORT.md)](./VERIFICATION_REPORT.md)

### Tóm tắt thực nghiệm:
- mini → thtung-paid: `HELLO_SWE_OK`, `DONE_MINI_HEADLESS` — OK.
- opencode → thtung-glm (fallback xq): `HI_GLM_OK` — OK.
- muse → shim → thtung-muse: `HI_MUSE_NATIVE`, `HI_SHIM_SVC` — OK.
- **Đối đầu trực tiếp**: `mini-SWE` nhanh gấp 2.5 lần ở single-file (34s vs 85s) và hoàn thành multi-file trong 28s trong khi Hermes Direct bị timeout >180s.
- DB backup: `/tmp/9r-backup.sqlite` (bản ngày triển khai).
