# Verifying a Worker's Report (Lead-side acceptance)

The worker's report is a hypothesis. These rules each caught a real wrong answer.

For recurring deaths, stalled leads or false PASS, use `references/worker-supervision-and-gates.md`: enforce process ownership, durable checkpoints and run-bound evidence mechanically instead of adding another prose-only rule.

> Briefing a migration/backfill that touches rows the players own — invariants that must actually fail,
one-directional deltas, proving the gate reproduces the real incident, secret and push hygiene:
> see `references/migration-data-integrity.md`.

> Worker-environment traps that produce false evidence (no MCP access / side tokens in the worker CLI — pre-fetch gated artefacts yourself; a self-regenerating visual baseline certifies a blank canvas): see `references/worker-environment-traps.md`.

## 0. Luật nghiệm thu (user chốt 06/10/2026 — bắt buộc, không ngoại lệ)

- KHÔNG ảnh + KHÔNG số đo độc lập = CHƯA XONG. Cấm báo "xong 80%", "cơ bản xong", "worker sống" thay cho kết quả.
- Worker chết giữa chừng mà chưa ra artifact = FAIL, nói thẳng fail + nguyên nhân, không báo vòng vo.
- Báo tiến triển bằng checkpoint đã kiểm: RED đúng triệu chứng, giả thuyết bị bác bỏ, compile/build có artifact hash mới, hoặc một gate đã chạy. PID còn sống, log dài thêm và git HEAD chỉ là liveness, không phải tiến triển tính năng.
- Một tick không có checkpoint: kiểm stage, child process và lý do đang chờ; chọn hành động cụ thể. Hai tick 3 phút không có checkpoint mới: đánh dấu STALLED và can thiệp, không chờ người dùng. Build đang link với deadline hợp lệ không bị kill chỉ vì log im.
- Artifact mới hoặc completion event phải kích hoạt nghiệm thu độc lập ngay; worker kết thúc chỉ chuyển IMPLEMENTED, không tự chuyển ACCEPTED. Quản lý run/checkpoint bền vững và đối chiếu build/environment trước khi báo kết quả.

## 1. An "assert the collection is empty" test that never prints the collection is unfalsifiable

A guard written as `expect(consoleErrors).toEqual([])` — with no `console.log(consoleErrors)` before it —
fails without telling you why. It looks like it passes for months, then fails once under load and leaves
nothing to diagnose. Worse, the same shape can be written so it *can never* fail (`expect(list).toBeTruthy()`
on an array is always true).

Rule: for every test that asserts "no errors collected", require the collected list be logged **before** the
assert, each entry tagged with which case/step produced it. Keep the assert strict (`toEqual([])`) — adding
observability must not loosen the gate. When you own the deliverable, check the guard actually can go red:
revert the fix and confirm the test goes red for the stated reason.

## 2. A required test that is red on every run is a test bug — never "pre-existing, out of scope"

Workers will label a red required test "pre-existing, not caused by me, out of scope" and move on. Check the
logs of several prior full runs: if it was red in all of them, it is a defect in your suite that must be fixed
before the suite means anything.

Usual cause: the spec drives the UI through a **default/ambient entity** (whatever the screen happens to open
with) and then waits for a state only reachable by an entity that satisfies the precondition. Fix the spec's
setup (select an entity that meets the precondition), never loosen the assertions.

The worker's stated *reason* may be right while its *conclusion* is wrong. "The guard correctly blocked it" can
be true (product fine) and still require you to fix the test. Separate the two verdicts.

## 3. Kill a test run mid-flight → seeded fixture rows stay in the DB

Long Playwright runs seed DB fixtures (`UPDATE t SET level = 9999, star = 100`) and restore them in a `finally`.
A kill/timeout skips `finally`, so the rows stay dirty. The next run then fails somewhere unrelated-looking
(an element never becomes selectable because the fake value changed the list ordering), and everyone calls it
"flaky".

Rules:
- After killing a suite, **verify and restore the seeded rows before drawing any conclusion**.
- Do not conclude "the worker's change caused it" until fixture rows are known-clean.
- When you brief the fix: cleanup must not depend on `finally` alone (state file / pre-run restore step), and the
  helper that scrolls to an entity must not depend on data-derived ordering.
- Prefer letting a long suite finish over killing it on a tool timeout; run it as a tracked background job.

## 4. Verify the model/endpoint the worker actually used — at the provider boundary

A launcher flag being correct proves nothing. Measure what the provider reports back (or spy the outbound
request) and compare. Launcher says X, provider says Y ⇒ there is a rewriting layer somewhere; remove it rather
than "fixing" the launcher. Re-check after every config/launcher/proxy change.

## 5. Record the constraint you had to drop

If adding a row required `ALTER TABLE ... DROP KEY <unique>`, that constraint encoded a business rule (e.g. one
source per target). The drop is a design decision — report it explicitly with before/after schema, not as an
incidental step inside a migration.

## 6. A green verdict is not evidence — read the rows, and ask the owner for the output

A harness that printed `1 passed` / exit 0 was certifying a state that violated the owner's own invariant on
dozens of accounts. Three independent defects let it do that, and each is worth an explicit check:

- **It compared two implementations over data the bad change had already rewritten.** Old-vs-new is only evidence
  when the "before" state is captured *before* the write. Golden data captured after the mutation is
  post-change characterization; label it as such and never gate a deploy on it.
- **It asserted no direction, only "differs".** A label like "difference is within scope" accepts any magnitude,
  including the subtraction that is the bug. Every changed quantity needs a business assertion with a number
  (`new >= old` **per entity**, and any increase equal to a provenance-backed delta).
- **It never proved it was collecting anything.** Identical output for two inputs known to differ, a control
group missing from the report, or a case count that can silently be zero each mean the run proved nothing.

## 8. A pushed commit is not a deployed fix — verify the running artifact

`git push` xong chưa có nghĩa prod đã chạy code mới. Kiểm tra container đang chạy: `docker inspect <ct>`
lấy `StartedAt`/image age so với giờ commit, rồi grep symbol mới ngay trong artifact đã build trên container
(`dist/*.js`, DLL) — thiếu symbol là chưa deploy, mọi kết luận "fix không ăn" đều vô nghĩa.

Hệ quả cho migration đổi nơi lưu trữ (bảng/cột/kho mới): xác minh cả phía ghi (service đang chạy) lẫn phía
đọc (client/API) đang trỏ cùng một store. Writer cũ + reader mới = dữ liệu "rơi nhầm kho", trông như mất
dữ liệu dù logic code đúng — và bảng cũ còn số dư tồn sẽ đánh lừa mọi đối chiếu số liệu.

So when a worker reports a passing suite: re-run it yourself, read its rows (not just the verdict), and require it
to print `ran / pass / fail / skip` plus a negative self-test (deliberately corrupt one expectation → non-zero
exit → revert). Then close the loop on the bad version: mark the superseded tool deprecated rather than deleting it,
so the next session cannot pick it up and re-certify a broken state.

Corollary for how the request arrives: when the owner asks whether the tests were run "and I mean the output", he
is asking for the table, not the summary. Paste the rows, including the failing ones.

## 7. Ask the user for domain decisions instead of inferring them from the data

When two sources disagree (a config table says A, a legacy column says B), do **not** pick one and proceed. The
mapping is business logic. Present the measured rows side by side, state which one the running code actually
reads, and ask. A wrong guess costs two full rounds: DB + every test that encodes the mapping.

## 9. The snapshot you compare against must come from the live target, not from a local copy

A migration gate is only as good as its "before" numbers. A local dump of the same-named schema drifted from the
live one, so the pre-check would have written **cheaper** prices onto a live economy (40/3/4/180 vs the live
60/5/12/1200). The worker's rule — *re-read the target and STOP on any mismatch* — is what caught it.

- Read the pre-check values out of the LIVE target itself (SQL over the real host), never out of a dump, a
  mirror database, or a snapshot taken days earlier.
- A mirrored source tree is the same trap for code: the local repo and the prod tree can hold different function
  sets for the same file. Diff **function names** between the two, not line counts.

## 10. A worker that produced no diff is not a worker that finished

A worker can exit `0` having done nothing: a startup warning, a truncated context, a brief whose runner resolved
no file. Three cheap checks before accepting "done":

- **Log size + content** — a few hundred bytes of warnings and no progress lines means it never started working.
- **Artifacts on disk** — mtime of the files it claimed to change, plus the markers it claimed to add
  (grep the new symbol in the artifact that actually serves traffic).
- **Child processes** — no build/test/deploy process under it means it never reached the build phase.

Record the real worker PID/PGID plus start fingerprint and child exit status; the launcher must return the child's code instead of finishing with a successful echo. Do not re-dispatch an identical brief after an unexplained death. Diagnose the failure signature, preserve partial artifacts, and allow at most two attempts with the same signature before BLOCKED and a diagnostic task.

A worker that dies **mid-verify** leaves the environment hot: check for a server it started still listening on its
port and stop it before your own run, or your run attaches to the stale instance and measures the old build. Treat
a truncated final log (`"…đang chạy GREEN"` and then nothing) as an unfinished round to re-dispatch, not a result.

## 11. Check whether the running artifact was built from the tree the worker edited

Acceptance can be red for a reason no case can express: the app exists **twice** in the repo and the framework
builds the copy nobody edited. Signs: every case red on a state condition, brand-new symbols missing from the
built bundle, and *older* features present instead.

- Grep the **served artifact** for a marker unique to each tree — one feature only the new tree has and one only
  the old tree has. The pair identifies the winning tree without reading any config.
- Compare the test box's layout to the **reference environment** (prod host). When prod has one tree and the test
  box has two, the test box is the divergence; bring it to the reference shape rather than adapting tests to it.
- A worker that stops and reports "the file I must change is outside my whitelist" is often right on the fact and
  wrong on the conclusion: the whitelist was written before you knew the repo shape. Widening it is your call, and
  the merge-then-delete plan must be spelled out (per-file decision table, marker proof, backup, structural guard
  case) — otherwise a later worker "fixes" the same class of bug in the other tree and it reappears.

## 12. Triage a screenshot bug report by SURFACE before anything else

When the owner sends a screenshot of a broken screen, establish **which environment produced it** in the first
message: read the numbers in the image against both candidates (an amount of gold or a live inventory count
identifies the live server; seeded test fixtures have round numbers and a single test account). Reproducing it on
the test box and reporting "fixed on test" answers a question nobody asked, and the owner will have to say so
again.

Once the surface is known, trace the failing value to the code path that SERVES that surface — an image that shows
raw internal codes next to localized names is telling you two data sources are being concatenated, so grep the
serving source for the append, not just the renderer.

Two reporting habits this owner expects in the same message: answer the direct question first with the measured
number, and translate insider vocabulary on the spot (he pushed back on reports that never defined "flaky" or
"fixture" — one plain clause each is enough).

## 14. Attribute repo dirtiness before blaming the worker — and spot-check its numbers

When the tree is dirty after a worker ran, do not assume the worker wrote it. Check mtime of the file
against the worker's spawn time plus `git log` on that path: a dirty file committed weeks ago and untouched
since predates the run and is pre-existing state, not a worker write. State the evidence (mtime, last commit)
when clearing the worker.

Mirror for read-only briefs: a report full of numbers is still a hypothesis. Re-measure at least one
count yourself with a cheap independent command (e.g. count the `enabled: 1` scene entries, grep for the
method the report claims is dead) before relaying the numbers. One spot-check per report catches the
confident miscounts that otherwise ship to the owner as fact.

## 13. A non-zero exit is not proof the work failed — check the artifacts, not the code

The mirror of §10: a worker can exit non-zero AFTER doing everything (a final action aborted
while every suite was already green, log full of passing gates). Judge by files changed on disk
(mtime + grep the new symbols) and the suite results recorded in the log, never by the exit code
alone — in either direction.

## 15. Verify from the user's seat before handing over

For a user-facing fix, the acceptance run must include the user's own path
end to end — open the served page yourself, log in with the provided test
account, and reach the screen the user cares about — before asking the user
to test anything. A green build log plus an HTTP 200 is not a working login
screen. Report completion with that evidence (screenshot path, scene reached,
remaining console errors listed verbatim) in the same turn the work finishes:
never hand the user a link you have not loaded, and never make the user the
first tester of your own errors.

## 16. Visual deliverables: look at the pixels yourself, and pin asset provenance in the brief

- Never relay "done, matches the reference" on a worker's word. Open the proof screenshots/video yourself before
  reporting — a log full of green checks once certified a flipped sword and a redrawn character the owner rejected
  on sight.
- Downscale before viewing: full-size PNGs time out the vision tool. Thumbnail to ≤640px (plus zoomed crops on the
  disputed area) before calling vision.
- Vision misattributes spacing (outer container padding vs inner input padding look identical in pixels) — confirm any 'dính mép / cắt viền' claim with `getBoundingClientRect` + computed-style numbers before briefing the fix, or you patch the wrong selector while the numbers already say which layer is guilty.
- When the deliverable must reuse provided art, the brief must name the exact source (file + panel/region),
  explicitly forbid redrawing, and require a provenance table (`part | crop x,y,w,h | reconstructed?`) plus closeup
  proof shots. A worker with an implicit source constraint defaults to redrawing from scratch.
- Deliver proof in a form the channel renders: native attachment/video, never a local `file://` markdown link —
  the owner sees an empty box, not your screenshot.

## 17. A janitor commit must contain only the whitelisted paths — never `git add -A`

A cleanup worker told to `git add -A` + commit will sweep thousands of pre-existing dirty files
(stale asset deletions, settings churn, untracked junk) into one commit, and undoing it costs more
than the cleanup saved. The report can still look perfect ("189 renames R100") while the commit
is unusable.

Rules:
- Briefs that end in a commit must forbid `git add -A` / `git add .` explicitly and require
  `git add` on the whitelisted paths only (or `git mv` staged entries plus the named fix files).
- Before accepting the commit, check `git show --stat HEAD` yourself: total file count must be
  in the same order as the whitelist, and `git diff HEAD~1 HEAD --name-status | grep -v '^R'`
  must show only intended modifications. Any `D`/`M` outside the whitelist = reject and redo.
- When the tree has pre-existing dirt, reset selectively (`git reset -q` + `git checkout --
  <dirty-scope-only>`) — never a blanket `git checkout -- .`, which also wipes the worker's
  legitimate fixes and forces a full redo.

## 18. A killed worker's partial work is inventory, not garbage — salvage before re-dispatching

Exit 143 identifies SIGTERM and exit 137 identifies SIGKILL; neither identifies the sender or proves OOM. Correlate process start time, supervisor stop records, kernel/cgroup memory events and tool timeout logs before attributing the cause; current free RAM does not rule out a historical or cgroup-limited OOM. Do not re-issue the original brief from zero. Salvage first:

- Read the log tail for the last GREEN checkpoint (spec names + measured numbers), not just the exit code.
- Diff EVERY repo in the workspace, including nested ones (`git -C <subdir> status` / `diff`) — root
  status hides nested-repo edits behind gitignore, and "no diff" there is a false negative (§10's mirror).
- Restore test-DB rows the dead run mutated directly. Integration tests that UPDATE seed rows with no
  `finally`-restore leave the next run measuring dirty state (§3's family, but the fix is an explicit
  restore statement, not a re-run) — verify with a GROUP BY before concluding anything.
- Then spawn a finisher brief that names the surviving artifacts (files, constants, green test names) as
  its starting base, with step 1 = verify those artifacts still exist (STOP and report if missing).
  Attribute pre-existing dirt before blaming anyone (§14): mtime + `git log` on the path decides whether
a dirty file belongs to the dead run or predates it.

## 19. Visual gates must assert on pixels, not on log lines — and freeze the working harness

A script that logs an "opened" line and screenshots later (or derives `popup_opened=True` from console text) can report PASS while the pixels show the base screen with nothing open. For any visual gate, the assertion must measure the artifact itself at the moment — pixel-region diff, DOM/canvas node presence — with the screenshot saved next to the verdict; a log-derived boolean is never visual proof, and the lead still opens the image before relaying PASS.

Beware of false positives from whole-canvas pixel diffs on animated scenes: a naive `pixdiff > threshold` on a live game board (falling gems, idle animations, floating damage numbers) passes on background motion alone even when a modal completely failed to render. For modal/popup acceptance, assert on the **modal bounding box**, modal-specific text via OCR, or overall canvas luminance dimming from the modal's overlay background.

For full-screen / fit-inside modal verification: asserting that a central panel renders is not enough. The background overlay must cover all 4 viewport edges (including the bottom edge, with no gap exposing the underlying scene/footer). If the modal scales down for fit-inside, the dark scrim must reside on the root Canvas, not inside the scaled modal container, or it scales down with the modal and leaves a bright un-darkened gap at the bottom/edges. Development console overlays (e.g. Unity Development Console, FPS bars triggered by `Debug.LogError` in isolated harnesses) must not obscure interactive controls (like "Sử dụng" or close buttons) in acceptance screenshots. Measure uniform aspect-ratio scaling (fit-inside) with margin on all sides across declared viewports.

Always distinguish between isolated visual test harnesses (e.g. direct panel hook `?pokidiagreal`, local port) and genuine authenticated E2E flows (login → hall → live match room → in-match button click → server packet). An isolated UI harness certifies only layout/geometry/pixel rendering; it can never certify match entry or E2E feature completeness. E2E acceptance test paths must never use diagnostic `SendMessage` or engine-internal hooks (e.g. `SendMessage('Btn_ChinhPhuc', 'OnClick')`) to bypass game navigation; cases must execute real Playwright mouse clicks on canvas coordinates to expose raycast blockers, missing button instances, and interaction bugs. Test suite manifests must verify that every referenced evidence file actually exists on disk (`os.path.isfile` and non-empty `getsize > 0`) before accepting a PASS verdict — a harness recording nonexistent evidence paths must fail-closed.

Always distinguish between isolated test builds (`webgl-fast/`, local port) and live promoted builds (`build/webgl/`, production URL). When a worker verifies a feature in a fast-iteration build, state clearly that it is not yet promoted to the live URL — otherwise the owner opens the live URL, sees an older build without the feature, and concludes nothing was done.

Once an e2e script produces a real passing artifact, freeze it as the standard (`e2e_<feature>.py`): later briefs must reuse and repair it, never rewrite the harness from scratch. From-zero rewrites regress steps the frozen script already passed (new OCR anchors, new timing, new failure modes) while looking like progress.

## 20. Resolve test credentials and targets yourself — never bill the owner for what the environment holds

Resolve the declared dev account and credential source without exposing secrets; never ask for a password in chat or copy one into a brief, argv or log. For browser credential entry use the vault workflow; non-browser tests use protected secret references. DB password hashes are not recoverable plaintext. Run acceptance against an explicitly isolated local/dev auth, API, WS and DB, never production. Enforce the endpoint allowlist before sending requests, verify environment/build IDs, and investigate input/transport/config evidence before claiming a password changed.

