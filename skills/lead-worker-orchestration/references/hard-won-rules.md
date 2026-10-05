# Hard-Won Rules

Check these before writing any brief. Each rule cost a real incident.

## 1. Never leave content design open in a brief

A brief that says "add a weekly quest to source STONE_ASCEND" without exact names, targets,
and rewards licenses the worker to invent game content — which lands in production unreviewed
and reaches real players before anyone notices. Same for prices, drop rates, and any rule that
is really game design.

- Scope briefs to **fixing existing behaviour**.
- **Propose** new content to the user and get approval before any brief is written.
- Do not "fix" a self-inflicted content change by asking the user whether to keep it. Undo it,
  then report that it is undone.

## 2. A worker's number is a proposal, not a verdict

When a worker pushes back on a figure in the brief ("300/day is what the data supports"), check
what **goal** that figure served before accepting or rejecting it. Two failure shapes:

- Worker computes from a local plan while ignoring the design target → number is wrong, reject it.
- Worker refuses an instruction because it double-counted the existing state → accept the refusal.

Either way: confirm with the user before changing a user-facing number, and say plainly which
one you are doing.

## 3. Count your own processes correctly

`ps -eo args | grep <pattern>` and `pgrep -f <pattern>` both match the checking command's own
command line — they report phantom workers and phantom "still running" builds.

```bash
pgrep -af '[r]un_worker.sh BRIEF'   # bracket trick: the pattern no longer matches itself
```

Print the matched command line, not a bare count, so the reader can judge it.

## 4. Parallel workers on one repo: nobody deploys

N workers each running `docker compose build` overwrite each other's images and race on the
same checkout. Dispatch all N with an explicit **"do NOT deploy"**, then write **one**
consolidated deploy brief whose job is: verify the build is clean, take a backup + image tag,
sync the artifact, redeploy, and prove it with a fresh start timestamp and a changed asset hash.

## 5. Shared files in parallel runs

Workers sharing a file (`App.tsx`, `api.ts`, route tables) must touch only their own lines and
**append** at the end rather than reformatting. Commits will interleave — that is expected and
harmless. Instead of forbidding it, verify at consolidation time that every expected change
survived.

## 6. Any production data write needs four things

1. **Backup + sha256** taken before the write.
2. An **id-scoped rollback script** written to disk (delete/restore by primary key — never a
   table-wide revert).
3. **Idempotency proof**: re-running the same job changes nothing.
4. **Self-funding test data**: the worker pays for its own test objects and dumps every changed
   number before → after.

## 7. Refunds and regrants

- Return **exactly what the player spent** (spent A to get B → refund A, not B).
- Count **everyone affected**, not just the two names the user supplied.
- Let the cap **clip** the excess and say so, instead of inflating a total.
- **Refuse to blind-refund** cases that left no trace to verify — say why in the report.
- Exclude test/admin accounts, and state the exclusion in the report so the number is auditable.

## 8. Report proactively; keep the raw logs out of chat

A job-completion notification is for the orchestrator, not for the user. On receipt: verify the
result independently, then post the acceptance report — never let a raw notification line be the
user's first news that something finished, and never wait to be asked "how is it going".

## 9. Verify user-facing numbers against the live artifact

Before telling the user something is published/documented/fixed, grep the live artifact (article
body, container bundle, served HTML), not the source file or the plan. A guide can be "written"
and still be unreachable (no link from the page players actually use) or stale (quotes a number
changed by a later fix).

## 10. Do the literal simple thing first

When the user asks for a concrete end-to-end action ("export then import"), execute exactly
that before designing anything around it — no loader framework, no multi-phase plan, no
refactor brief, no pipeline abstraction. Elaborating a simple request reads as not listening,
and every extra layer is another round of wrong output to unwind. Frameworks follow a working
round-trip; they never precede it.

## 11. A vendor roadmap post is not a product

Before letting an announced format or tool into the architecture, verify it exists: a package
on the registry, code in dated releases, a repo with commits. A blog-only announcement gets a
watch note ("recheck on the next release"), never a dependency — an announcement can sit
unshipped across several releases while the team keeps investing in the existing APIs.
Runtime work should target the stable APIs the vendor actually ships; the custom bridge stays
small and replaceable until the standard lands.

## 12. Set the commit identity from the repo's own history before committing

## 13. Cron watchdog đi kèm mỗi worker (BẮT BUỘC — theo coding-workers-docs §5b)

Mỗi lần spawn worker (muse/mini/glm/codex/agy) phải tạo kèm 1 cron job theo dõi
tiến độ liên tục và báo cáo về chat — user không phải hỏi "xong chưa".
Tạo cron kèm --model + --provider NGAY lúc tạo (không tạo trước set sau):
`hermes cron create --model thtung-muse --provider custom:THTUNG --name
"watch-<TÊN-BRIEF>" --deliver origin "every 1m" "<prompt watchdog: pgrep
worker, tail log brief, check artifact + curl endpoint, báo tiến độ ≤10 dòng;
worker xong hoặc treo >10 phút thì báo ngay>"`.
Bẫy đã gặp thật (2026-10-02): tạo cron không kèm model/provider rồi edit thêm
sau → job chạy với config cũ, fail liên tiếp "No LLM provider configured".
Luôn tạo kèm từ đầu. Khi worker xong hoặc chết: báo kết quả cuối 1 lần rồi xóa
cron (`hermes cron remove <job_id>`) để khỏi spam. Tên cron theo quy ước
`watch-<TÊN-BRIEF>` để dễ truy vết worker nào.

## 14. RULE THÉP: worker exit là xóa cron TRƯỚC, nghiệm thu SAU (2026-10-05)

M169 xong từ 00:34 nhưng cron `watch-M169` chạy vô ích tới sáng (mỗi phút 1 lần)
Vì Lead kiểm log thấy xong mà quên xóa cron. Từ giờ checklist "xong việc" bắt buộc
theo đúng thứ tự này:
1. Worker exit → **xóa cron NGAY** (`hermes cron remove watch-<TÊN>`), chưa cần biết kết quả.
2. Rồi mới đọc log, nghiệm thu độc lập.
3. Rồi mới báo user + update bảng theo dõi.
Xóa cron trước vì cron thừa tốn tài nguyên mỗi phút; nghiệm thu sau vì nó không
chạy đi đâu được. Không bao giờ làm ngược lại.

## 15. Worker chết liên tục lúc spawn = kiểm tra /tmp đầy TRƯỚC (2026-10-05)

M172/M173 chết 5+ lần liên tiếp (`tcsetattr`, SIGTERM lúc khởi động), log đứng yên
ở 287 byte. Nguyên nhân KHÔNG phải RAM (trống 7.5GB) hay OOM — mà là `/tmp` đầy
76% (12GB/16GB) do rác luồng khác (`raw.zip` 3.9GB, `Assets.zip`, UnitySetup,
file `.il`). Worker spawn cần ghi tmp, hết chỗ là chết ngay lúc khởi động.
Checklist khi worker chết lúc spawn 2+ lần:
1. `df -h /tmp` trước — đầy >70% thì dọn.
2. `du -sh /tmp/* | sort -rh` tìm thủ phạm; `lsof`/`fuser` xem ai đang dùng.
3. File không ai dùng: `mv` vào `/root/tmp-backup-<ngày>/` (không xóa hẳn),
   rác build (`.il`, cache) thì xóa. File luồng khác đang dùng (MINI-57 build APK)
   thì GIỮ, hỏi chủ dự án trước khi đụng.
4. Spawn từng worker 1 (cách nhau 15s), không spawn 2 con cùng lúc khi /tmp chật.
