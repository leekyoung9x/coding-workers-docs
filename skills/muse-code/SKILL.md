---
name: muse-code
description: "Use when delegating coding tasks to Meta Muse Code CLI."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Coding-Agent, Muse, Meta, Worker, Orchestration, CLI]
    related_skills: [lead-worker-orchestration, codex, claude-code]
---

# Meta Muse Code CLI Worker

Operating skill for orchestrating Meta's native terminal coding agent **Muse Code CLI** (`muse`) as a dedicated worker.

## Overview & Architecture

Muse Code is Meta's native coding agent for terminal and CI:
- **Binary:** `~/.local/bin/muse` (hoặc `/usr/local/bin/muse`).
- **Cài đặt:** `curl -fsSL https://dev.meta.ai/install.sh | sh`.
- **Xác thực:** Trực tiếp qua Meta OAuth device code (không dùng shim/proxy):
  - Chạy `muse login` ➔ truy cập `https://auth.meta.com/oauth/device/?code=...` ➔ xác nhận mã device.
  - File thông tin xác thực lưu tại: `~/.config/muse/auth.json`.
  - Hoặc qua biến môi trường: `export META_API_KEY="..."` / `muse auth set`.
- **Model:** Meta Muse Spark 1.3 / 1.2 với engine suy luận nhiều cấp độ.

## Phương Thức Phối Hợp (Lead–Worker Orchestration)

Tuân thủ nghiêm ngặt ranh giới trong `lead-worker-orchestration` (`hermes.md` / `agent.md`):
- **Hermes (Lead)**: Lập Numbered Brief, file whitelist, acceptance criteria định lượng, giám sát watchdog, nghiệm thu độc lập. Lead KHÔNG tự tay sửa code.
- **Muse (Worker)**: Chịu trách nhiệm 100% thi công, tìm root cause, tự viết regression spec, thực hiện chu trình RED ➔ GREEN, tự build và fix compile.

### 0. Bắt buộc kiểm tra trước khi spawn (môi trường VPS)

Hai bẫy dưới đây đã thật sự làm worker chết giữa phiên — kiểm trước khi giao việc:

- **Bẫy `413 Maximum request body size 1048576 exceeded`**: **HAI nguồn khác nhau, kiểm cả hai** trước khi kết luận:
  1. **Proxy `/tmp/meta_proxy.py` (nguồn phổ biến nhất)**: `aiohttp.web.Application()` mặc định `client_max_size = 1 MiB`. Khi context của Muse vượt 1MB, **proxy** trả 413 — trông y như lỗi Meta API. Fix: `web.Application(client_max_size=64 * 1024 * 1024)`. Kiểm chứng bằng cách POST body 2MB vào proxy: nhận 401 (từ Meta) = OK, nhận 413 = vẫn còn giới hạn.
  2. **Context thật sự quá lớn**: worker mở **file ảnh evidence PNG/JPG** (1.9MB) hoặc `cat` nguyên file lớn (`nodes.json` 400KB, spec 100KB+, log dài), hoặc `console.log` object lớn.
  → Trong MỌI brief phải ghi rõ: *KHÔNG đọc/mở file ảnh hay file >100KB; chỉ dùng `sed -n`/`offset+limit`/`grep -n` đọc từng phần; không dump object lớn ra stdout.* Và **giữ ảnh evidence ngoài workspace** của worker. Khi đổi cấu hình proxy/mức reasoning cho worker đang chạy: **đừng sửa launcher đang dùng chung** — dựng cổng mới (ví dụ 9990) và **kill rồi respawn** worker, để không cắt ngang tiến trình khác.
- **Bẫy auth/base-url**: `muse exec --model muse-spark-1.3-contributor` gọi thẳng `api.meta.ai` trả **exit 1**. Chạy proxy `python3 /tmp/meta_proxy.py <PORT>` (aiohttp, forward sang `https://api.meta.ai`, **nhớ `client_max_size=64MiB`**) rồi thêm `--base-url http://127.0.0.1:<PORT>/v1`. Kiểm proxy sống: `curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:<PORT>/v1/models` (401 = OK).

- **Bẫy model contributor (đã gặp thật, nghiêm trọng)**: proxy `/tmp/meta_proxy.py` từng chứa đoạn rewrite `muse-spark-1.3-contributor` → `muse-spark-1.3`, khiến MỌI worker **âm thầm chạy model yếu hơn** dù launcher ghi đúng. **KHÔNG bao giờ rewrite model trong proxy.**

### Khóa cứng model (đã cài, không được gỡ)
Ba tầng cùng bảo vệ, đã kiểm chứng bằng proxy spy ghi lại `model` client thực gửi:
1. **Launcher `~/.local/bin/muse`** (ngay trước `exec "$binary"`): ép mọi lời gọi về `muse-spark-1.3-contributor`.
   - `--model muse-spark-1.3` → ghi đè; `--model=muse-spark-1.3` → chuẩn hoá về 2 token rời + ghi đè (CLI **không** nhận form `--model=value`); model rác khác → ghi đè; **không truyền `--model`** → tiêm ngay **sau subcommand** (`exec`), không tiêm trước nó.
   - Tắt tạm khi debug: `MUSE_MODEL_LOCK=off muse ...`. Backup bản gốc: `/root/.local/bin/muse.bak-pre-lock`.
2. **`~/.config/muse/settings.json`**: `{"schema_version": 1, "model": "muse-spark-1.3-contributor"}` — **bắt buộc có `schema_version`**, thiếu nó CLI báo `malformed settings file` và exit 1.
3. **Skill + memory**: nghiêm cấm `muse-spark-1.3`.

Cách kiểm chứng model thực tế Meta phục vụ (làm sau mỗi lần đổi proxy/config):
  ```bash
  TOK=$(python3 -c "import json;print(json.load(open('/root/.config/muse/auth.json'))['providers']['meta']['api_key'])")
  curl -s -X POST http://127.0.0.1:9990/v1/chat/completions -H "Authorization: Bearer $TOK" \
    -H "Content-Type: application/json" \
    -d '{"model":"muse-spark-1.3-contributor","messages":[{"role":"user","content":"ok"}],"max_tokens":8}' \
    | python3 -c "import sys,json;print('model thuc te =>', json.load(sys.stdin).get('model'))"
  ```
  Phải in `muse-spark-1.3-contributor`. Để kiểm **client gửi model gì** (bắt được cả khi CLI tự đổi), dùng spy proxy `/tmp/spy_proxy.py <port>` (ghi mọi `"model"` vào `/tmp/spy_models.log`) rồi truyền `--base-url http://127.0.0.1:<port>/v1`.

- `muse-spark-1.3-contributor` gọi **trực tiếp** `api.meta.ai` chạy được (verify 3/3 lần exit 0) ⇒ chạy qua proxy là để tiện log/kiểm soát, KHÔNG phải vì contributor bị lỗi.

### 1. Thực Thi Tự Động Headless (`muse exec` — Khuyến nghị)

Dùng launcher có sẵn để log tách theo tên brief (khuyến nghị hơn gọi trực tiếp):

```bash
bash /poki/run_muse_brief.sh BRIEF_MUSE_<TÊN>     # → BRIEF_MUSE_<TÊN>.log
```

Hoặc gọi trực tiếp:

```bash
~/.local/bin/muse exec \
  --base-url http://127.0.0.1:9988/v1 \
  --workspace /path/to/project \
  --model muse-spark-1.3-contributor \
  --prompt-file /path/to/BRIEF.md \
  --reasoning-effort medium \
  --yolo
```

Các tham số quan trọng:
- `--workspace <PATH>`: Khoanh vùng thư mục làm việc của agent.
- `--prompt-file <PATH>`: Đọc brief/kế hoạch thi công chi tiết từ file markdown.
- `--model muse-spark-1.3-contributor`: **BẮT BUỘC**. Nghiêm cấm `muse-spark-1.3`.
- `--reasoning-effort <none|minimal|low|medium|high|xhigh|max|ultra>`: Độ sâu suy luận. **Mức mặc định của user hiện tại là `medium`**; chỉ nâng lên `max`/`xhigh` khi user yêu cầu rõ cho task phức tạp.
- `--base-url <URL>`: Bắt buộc trỏ proxy `http://127.0.0.1:<PORT>/v1` (xem mục 0) — thiếu tham số này worker exit 1. Cổng hiện dùng: **9990** (9988 là bản cũ còn giới hạn 1MB).
- `--yolo`: Bỏ qua sandbox và câu hỏi xin phép để chạy tự động hoàn toàn.
- `--json`: Xuất stream sự kiện dạng JSONL khi cần parse tiến trình.

### 3. Chạy nhiều worker song song trên cùng workspace

Chia brief theo **lát cắt phạm vi** (mỗi worker một nhóm bảng/chủ đề) và ghi rõ whitelist file output riêng
(`review-X-A.md` vs `review-X-B.md`) — hai worker cùng ghi một file sẽ đè nhau. Một brief gộp chung cho
"review toàn bộ" dễ bị bỏ sót; 2–3 brief hẹp chạy song song cho độ phủ tốt hơn và nhanh hơn.

### 4. Vòng nghiệm thu bắt buộc (không tin self-report)

Worker tự báo "đã xong, mọi số đã kiểm" **vẫn sai số**. Quy trình đã chứng minh hiệu quả: Lead chạy lại
SQL độc lập trên vài con số mẫu → thấy lệch → giao **một worker thứ ba** brief "fix + verify toàn bộ số"
(kèm bảng số Lead đã tự đo làm mốc). Vòng đó bắt được 6 số sai trong 2 report, gồm 1 số do Lead phát hiện.
Luôn yêu cầu worker xuất thêm file `VERIFY.md` dạng bảng `số | vị trí | report ghi | đo thật | pass-fail`.

### 5. Kiểm chứng phi-tác-động khi brief là read-only

Với brief audit: chốt trước baseline đếm bảng (`SELECT COUNT(*)` vài bảng), chạy lại sau khi worker xong để
chứng minh không có lệnh ghi DB, và `find <source-dir> -newermt <giờ spawn>` để chứng minh không sửa source.
Với brief ghi DB: chốt trước `md5(group_concat(...))` trên bảng sẽ đổi **và** trên các cột/bảng phải giữ
nguyên (ví dụ `reward_json` các tier không sửa) — cách này bắt được worker sửa quá phạm vi.

### 5b. Worker tự nhận "test đỏ sẵn, không do tôi" — LUÔN tự kiểm chứng

Đây là dạng self-report sai phổ biến nhất. Worker gọi test suite chung, thấy đỏ, rồi suy ra "lỗi sẵn" để khỏi
phải sửa. Cách bác bỏ trong ≤3 lệnh:
1. Chạy **riêng spec của task** → nếu xanh, chứng minh diff không gây hồi quy.
2. Kiểm **biến môi trường của spec**: spec tự mint session/JWT bằng `process.env.X || "fallback"` mà suite không
   export `X` → test đỏ vì cookie sai, không vì code. Export biến thật rồi chạy lại để phân biệt.
3. Kiểm **danh tính fixture**: spec hardcode user id (ví dụ `4`), nhưng DB test đặt quyền cho id khác (id 46).
   Thử trực tiếp cả hai id bằng `curl` + cookie mint từ script của repo → biết ngay ai mới có quyền.
Ghi kết luận khác với self-report của worker vào báo cáo, kèm lệnh tái lập.

### 5c. Bẫy khi worker rebuild container giữa lúc chạy test

Worker chạy `docker compose build && up -d` trong khi suite Playwright đang chạy → container restart →
`ERR_CONNECTION_REFUSED` + cascade "element not found" (hàng chục test đỏ giả). Khi thấy cụm lỗi kiểu này,
kiểm `docker inspect <ct> --format '{{.State.StartedAt}}'` và số `ERR_CONNECTION_REFUSED` trong log trước khi
kết luận hồi quy. Trong brief: yêu cầu build xong + healthy **rồi mới** chạy suite.

### 5d. Kiểm chứng claim "đã push" — repo backend thường ở branch khác `master`

`git rev-parse origin/master` trả về chuỗi literal `origin/master` (không resolve) khi repo đang ở branch
feature ⇒ dễ kết luận sai là "chưa push". Luôn kiểm đúng branch đang đứng:
`git branch --show-current` → `git ls-remote origin <branch>` và so với `git rev-parse HEAD`.
Cũng đừng kết luận "worker không gate" chỉ vì `strings`/`grep` trên file trong container không khớp —
image runtime có thể thiếu `binutils` (không có `strings`); dùng `docker exec <c> grep -ac '<symbol>' <dll>`
hoặc kiểm ngay bằng một request thật rồi đo DB trước/sau.

### 5e. Kiểm chứng gate/no-write bằng probe thật (mạnh hơn đọc test của worker)

Khi worker thêm "gate" (chỉ ghi khi cờ bật), nghiệm thu đúng cách là tự gọi đường ghi thật rồi đo DB:
1. Đọc cờ ra, chốt số đo TRƯỚC (`SELECT SUM(...)`).
2. Tìm endpoint S2S tương ứng. API S2S thường bind trong docker network chứ không publish ra host
   (`docker ps` không có port) → gọi qua container cùng network:
   `docker exec <web-ct> wget -qO- --post-data='{...}' --header='Content-Type: application/json' --header='X-Server-Secret: <secret>' http://poki-internal-api:5000/api/<route>`.
   Secret đọc từ `docker inspect <ct> --format '{{range .Config.Env}}{{println .}}{{end}}'`.
3. Đo lại: đường event phải KHÔNG tăng, nhưng đường không-event (match/damage) phải CÓ dòng — nếu cả hai
   đều không tăng thì request chưa hề chạy và phép thử vô nghĩa.
4. Test integration của worker có thể `Skipped`/`Inconclusive` nếu thiếu `ConnectionStrings__DBConnection`;
   tự set env trỏ DB test rồi chạy lại trước khi tin "passed".

### 6. Thực Thi Tương Tác Qua TUI

Dành cho các phiên tương tác đa bước cần nhập phản hồi thủ công:
```python
terminal(command="~/.local/bin/muse", workdir="/path/to/project", background=true, pty=true)
```

## Lệnh Quản Trị Hệ Thống

```bash
# Kiểm tra phiên bản
muse --version

# Đăng nhập xác thực tài khoản Meta
muse login

# Đăng xuất / thu hồi credential
muse logout
```

## Quy Chuẩn Kiểm Thử Bắt Buộc

Worker bắt buộc phải hoàn thành Two-Stage Testing Gate:
1. **Cổng 1 (Local Gate)**: Tự viết testcase kiểm thử, chạy RED trước khi sửa, GREEN sau khi sửa, đảm bảo không có compile error hay regression.
2. **Cổng 2 (Live Gate)**: Kiểm tra trực tiếp trên container/URL thật của dịch vụ sau deploy, đo bằng số liệu thực tế (HTTP status, payload).
