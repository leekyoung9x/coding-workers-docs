# Maintaining an Owner-Facing Tracking / Sign-off Board

Use when the owner wants a running list of issues, states, options, and their own decisions — and expects to
answer *in* the artifact rather than in chat. The board is a **shared editable surface**: treat it as the
owner's property that you are allowed to update in place, never as a file you regenerate.

## 1. Why this exists

A long project accumulates a dozen open decisions. Re-listing them in chat every turn reads as spam and buries
the two that actually block today. The board moves the list out of chat; chat then carries only what changed
and what needs a decision now.

## 2. Shape

One row per item. Columns that worked:

- `ID | Mức | Trạng thái | Vấn đề | Phương án | <owner decision column> | Người làm | Ghi chú`
- **Order the columns so every value column sits to the right of its text column** — the owner scans the short
  token to the left of each long text cell. A layout of `ID | Mức | Trạng thái | Vấn đề | …` is fine; what makes
  the board unreadable is long free text sandwiched between the two short vocabularies.

- **Mức** (severity): three values only — `GẤP` / `THƯỜNG` / `XONG`.
- **Trạng thái** (state): three values only — `CHỜ CHỐT` / `ĐANG CHẠY` / `XONG`.
- **Owner decision column**: must accept **free text**, not just a pick-list — the owner writes sentences here
  ("do both", "refund the cakes, claw back the stones"). A dropdown with suggestions plus free entry is the
  right control.

Collapse synonyms before publishing: five severity values and seven state values are unusable. Map them
(`Từ từ`+`Đang chạy`+`Đã chốt` → `THƯỜNG`; `Chờ xác minh`+`Chờ pinpoint`+`Đã điều tra` → `CHỜ CHỐT`) and show the
counts per value so the collapse is verifiable.

## 3. Two columns that must not be merged

Severity and "waiting on the owner" are different axes. When every row carries `GẤP` *and* `CHỜ CHỐT`, the board
says the owner has nine urgent decisions when in fact most are work items waiting on the agent — and the owner
reads it as "you told me nothing was pending". Keep severity in its own column, reserve the owner-decision
column for rows that genuinely need an answer, and **before ever saying "nothing pending for you", read the
owner-decision column and count the empty cells** — your own sense of what is urgent is not that evidence.

## 4. Preservation rule (the one that costs the owner real work)

Replace-the-whole-document is destructive. Uploading a regenerated file over a live spreadsheet — Drive
`files().update(media_body=...)`, re-exporting a new spreadsheet, writing the file wholesale — **erases
everything the owner built on it**: tables (`Ctrl+Alt+T`), conditional formats, manual cell colours, dropdowns,
named ranges, formulas, extra tabs, comments. Symptom from the owner: *"why does the table disappear every time
you edit it?"*

Order of preference:

1. **Write cells only.** With the Sheets API available, patch just the changed range
   (`spreadsheets().values().update(range='<Tab>!C12', valueInputOption='USER_ENTERED')`). Every user-side object
   survives. Create once, then never re-upload.
2. **No Sheets API yet? You can still write in place, cautiously.** The file could be re-uploaded and read back to
   prove what survived: on a real sheet with a `Ctrl+Alt+T` table + two dropdowns, an XLSX export → edit two
   cells → re-upload to the **same file id** came back with `tables=['Bảng_1']` and both validations intact.
   Two hard conditions: (a) **always prove it** — re-read the file after writing and report the before/after
   structure, never assert preservation; (b) **do not claim conditional formatting or manual colours survived** —
   that was not the thing measured, and it is the most likely casualty. Say which objects you verified and which
   you did not. Run this on the owner's live board only when they are waiting and the alternative is no update at
   all; the moment the API is available, switch to cells.
3. **If the API is not available and you cannot verify, stop updating** and give the owner the one-click enablement
   (`https://console.developers.google.com/apis/api/<service>/overview?project=<N>` — the 403 body carries the
   project number). Do not "keep it fresh" by re-uploading blind; each round costs their work.
4. **Offer the self-hosted board** when the owner is clearly going to iterate a lot. Asking for it explicitly
   is the signal to build it rather than keep fighting the file host.

Runner: `scripts/tracking_board.py` (`check` / `set` / `sync`, dry-run by default, prints the
BEFORE/AFTER structure report and refuses to write unless the API path is available or you pass
`--unsafe-file-replace`). The same mechanics in another shape: keep the board's content in a plain
CSV file the script re-syncs from, so a later session can rebuild its view without touching the sheet's
formatting.

### 4b. Building it inside the owner's EXISTING admin panel

When the owner says the project already has an admin panel and you built the board as a standalone app instead,
you have created a second artefact to maintain and a teardown to do. Resolve the target before designing:
lift the repo list with remotes (see the project-inventory rule in SKILL.md Step 1) and name the admin project in
the brief. Then work *inside* it:

- **Reuse the panel's own auth** — do not invent a second gate. In practice the panel already has one (a shared
  secret header check, or a session tied to an `is_admin` column on the game user row); follow the same helper
  the existing pages/APIs use so the new page inherits the protection. Confirm from the code which mechanism is
  live before writing acceptance criteria, and name the real admin account for tests.
- **Follow the panel's existing tab pattern** rather than introducing a framework: add one nav entry, one page
  block, one loader wired into the existing page-switch dispatcher, and one JSON endpoint group. The panel's own
  newest feature is the template.
- **Make the first job a recon job.** If the brief's worker cannot state how the panel authenticates, where its
  UI lives, and which port/host it runs on, it should stop and ask instead of guessing — put that instruction in
  the brief, because a worker that guesses an auth mechanism produces a page nobody can log into.
- **Verify the whole panel, not only the new tab.** The route the owner relies on today must still answer.
  Compare the old pages' responses before and after (byte-identical is the strongest form) — this is the
  acceptance evidence that adding the tab broke nothing.
- **A pre-existing app's entry point may not exist where the code is.** Before promising the owner a URL, check
  whether the service is actually running on the target host and whether the reverse proxy routes it; "the code is
  done" and "the owner can open it" are different claims, and only the second one is reportable as done.

### 4c. Switching the board's HOST mid-session

The owner may move the board from one machine to another once they understand where it would land ("same place as
the game data"). Treat that as a stop-and-rewrite: kill the in-flight deploy worker, confirm nothing was written
(`git status` in each target repo, the target host's backup dir, container start times), and re-issue the brief
against the explicit host — with the previously-used deploy script **banned by name** if it points elsewhere.

## 5. Self-hosted board recipe (when the owner asks for a real app)

Lightweight, no build step, reachable at `IP:port` (this owner prefers direct `IP:port` over domains/tunnels):

- Node + Express on a **free port** (check with `ss -ltn` first), bind `0.0.0.0`, one SQLite file. No MySQL,
  no auth gate — it is an internal decision board.
- **Seed idempotently from the CSV the board was born as** (key on the row ID) so the deployment arrives
  populated; a `npm run seed` that is safe to re-run.
- **Colour decided server-side and returned in the API payload**, so the API and the UI cannot disagree; the
  page just paints by the value it was given.
- Inline edit via combo boxes that save on change, plus a **free-text** owner-decision field.
- A JSON API (`GET/PATCH/POST/DELETE /api/items`, `/history`) so the agent can update rows with `curl` between
  turns, plus `GET /healthz`. **Call it with `curl`, not a Python HTTP client**: when the host sits behind
  Cloudflare, `urllib`/`requests` default User-Agents are answered `403` with Cloudflare error code `1010`
  (browser-integrity block) while the identical call via `curl` returns `200` — a scripted updater written against
  the Python client fails on every row and looks like an auth problem. Read the secret from the container env,
  pass it as the header, and never print it:
  `curl -s -H "X-Admin-Secret: $SECRET" https://<host>/api/items`.
- Per-row change history (who/when/old → new) — this is what settles "I already decided that".
- systemd unit with `Restart=always` + `enable`, so it survives reboots without a manual step.
- Tests must drive the **real UI** (Playwright: change a combo box, reload, assert persistence; assert the row
  colour) plus one API-write → reload → visible check proving both paths share one source. Restore the original
  values at the end so the live board is not left dirty.

## 5b. Deliver raw data first when the owner intends to style it

The owner is often the one who will decide what the board looks like. Two rounds that get wasted:

- **They say they will make the example themselves.** Hand over **raw values only** — no colours, no conditional
  formatting, no auto-painted states — and let them set the convention. Then read their sample back and mirror
  exactly what they did. Formatting you add speculatively is formatting they strip, and they may read it as you
  overriding their design. Corollary: when you later update the board, the same preservation rule from §4 applies
  with teeth — every re-upload is a chance to destroy the convention they just set.
- **They ask you to group the values.** Collapse the column's vocabulary to a small set of reusable categories and
  state the mapping, rather than leaving whatever free-text states accumulated. Show the per-value counts so the
  collapse is checkable, and collapse severity and state INDEPENDENTLY — one axis for how urgent, one for how far
  along.

Reserve the state column for what is true now and the owner-decision column for what needs an answer: an empty
owner-decision cell means "no question for you here", which is the signal the owner looks for when they ask
whether anything is pending.

### 5c. Tooling: getting a real spreadsheet out of a Drive-enabled account

When the owner says "make it a Google Sheet", a CSV uploaded to Drive is **not** what they asked for and they
will say so. If the Sheets API is not enabled for the project, do not fall back to a plain file:

- Create a real spreadsheet through the **Drive API** by uploading the CSV with
  `mimeType='application/vnd.google-apps.spreadsheet'` — the file conversion happens server-side and needs no
  Sheets API scope. Verify the result's `mimeType` is `application/vnd.google-apps.spreadsheet`, not `text/csv`.
- If the owner wants dropdowns and coloured states and you cannot write cells yet, a workaround that survived
  verification is to build the file as an **XLSX with openpyxl** (data validation lists + conditional-formatting
  rules), upload it converted to a Sheet, and then **download it back and read it** to prove the validations,
  rules, freeze panes and filter all survived the round trip. Do this for the first version only; afterwards the
  preservation rule in §4 governs and you write cells, not files.
- Python deps are usually missing from the interpreter you reach for first: create a venv and install
  `openpyxl` + `google-api-python-client` + `google-auth-oauthlib` there rather than assuming a system-wheel.
- When the owner wants to touch the board's formatting themselves, they will say so (§5b) — hand over raw values
  and stop publishing formats.

## 7. Row hygiene: "updated" is not "accurate"

The owner reads one column at a time and does not re-audit rows, so a single stale row discredits the whole
board ("is the board actually done? why is row X still running?"). Re-audit every row against evidence before
reporting the board as done, and enforce these in the brief that touches it:

- **One row = one item with one state.** A row that merges two items of different state hides the unfinished one.
  The recurring shape: an owner-decided change ("swap reward A for reward B") bundled into a row about a finished
  piece of UI work — the row goes `XONG` and the undelivered decision silently disappears. Split it: one row for
  the finished half (with its evidence), one new row for the undelivered half.
- **The mirror case is two rows for one continuous workstream.** A deliverable split into a data half and a deploy
  half (the DB rows landed, the code that reads them did not) must not leave both rows in `ĐANG CHẠY` — mark the
  finished half `XONG` with its evidence (backup path + checksum + re-read values) and point the live one at the
  worker that is actually running. "Data done, code not shipped" is the state to show, because that is the state the
  owner is waiting on.
- **`ĐANG CHẠY` rows outnumbering running workers is normal — a row pointing at a worker that was never launched is
  not.** One worker can own two rows (a task and its follow-up) and one fan-out of several workers can cover many
  rows, so never "fix" the count by inventing workers or by marking rows `chưa giao` while work is genuinely in
  flight. Before reporting the board, `ps` the worker processes and map each `ĐANG CHẠY` row to one of them.
- **The worker column names only a worker that is really running.** `Người làm: <worker> đang làm` on a row whose
  worker finished (or was never dispatched) reads as a live process and misleads the owner into thinking the
  system is busy. Work that has no worker yet says `chưa giao`; work the Lead is holding says nothing.
- **Every `XONG` row carries evidence** — commit hash, spec path, or a measured number. A row marked done without
  evidence gets challenged on the next read.
- **Severity reflects what it blocks, not how hard it is.** A row waiting on the owner because it blocks sign-off
  or players is `GẤP`; a row of optional, not-yet-shipped preferences is `THƯỜNG`. If all owner-decisions end up
  `THƯỜNG` and all `GẤP` rows are the agent's own work, the board answers the owner's "nothing is pending for me?"
  with a misleading picture even though every cell is technically correct — re-classify before reporting.
- **A finished worker whose brief's last step was blocked leaves its rows stranded in `ĐANG CHẠY` — reconcile from its report, not from your own memory of what you dispatched.** When a board write is left out of a brief (because the credential lives elsewhere) or fails at the end of a run, the worker still delivers everything else: its report file exists, its plan-checked changes are on disk, and only the row never moved. Four workers in one session ended exactly this way while their rows read "đang chạy", and the owner eventually audited the board himself. At every heartbeat, and before answering any "is X done?" question: list the running worker processes, take the rows whose named worker is NOT in that list, and for each one read its report / log tail — if it finished, close the row now with its evidence and note that the agent performed the write on the worker's behalf. Rows are closed by evidence, not by a worker's exit notification.
- **Read the board back through the API after every update** (not from your own patch list) and check: total row
  count, the per-value counts of severity and state, duplicate ids, and that the owner-decision cells of existing
  rows are byte-identical to before. Paste those numbers in the report — that is the accuracy evidence.
- Two defects this catches every time in practice: a filter combination (severity + state) that legitimately
  returns zero rows while the board looks like it lost data, and rows whose state was set by a previous round and
  never revisited.
- **Verify YOUR OWN write landed, exactly as you would verify a worker's.** A bulk `curl` update whose body was
  passed in the wrong position silently drops every field, and the API still answers `200`/`success` while creating
  blank rows with server-assigned ids — one six-row batch produced six empty rows and made a whole earlier batch
  look like it had been deleted by someone else. Two habits prevent it: send the payload with `PATCH`/`POST`
  `--data-binary` in a script (a heredoc/py file beats a long hand-typed `curl`), and **re-read the board through
  the API after writing** — assert the exact ids you intended (created/updated), the total row count, and that the
  ids you did NOT intend to create do not exist. Delete any stray row your own malformed write produced, and say so
  plainly if the owner noticed the artifacts.
- **When YOU choose the row ids, assert the response echoes the id you sent.** Boards whose ids are human codes
  (`T1`, `E11`, `M86`, a ticket prefix) hand you a free proof of parsing: a response carrying a server-assigned
  surrogate id instead of yours means the body never reached the handler and a default row was inserted. So after a
  batch, re-GET and check the ids you intended exist *and* that the id you sent equals the id returned — a
  `success: true` plus a `200` is not evidence, and the orphan rows it leaves look to the owner like the board lost
  data. Include every write call in one scripted batch (a Python file calling `curl`/`requests` with an argv list)
  rather than a chain of hand-typed commands, and print one line per row so a failure is attributable.

## 5d. The board's own UX: the owner will ask for views, starting with "hide what's done"

Once the board is real, the owner uses it to find work — and asks for view controls: *"cái nào xong rồi thì
thêm một mode là không hiển thị các cái xong rồi"*. Treat this as a first-class deliverable, not a cosmetic
tweak, because the way it is wired either helps them find today's blockers or hides them.

- **A done-hiding toggle must default to hidden, be reversible, and survive a reload.** Persist the choice
  (localStorage) *and* mirror it into the URL, so refreshing or pasting the link to someone else reproduces the
  view. A toggle that resets on reload gets re-set by hand every session and is worse than none.
- **State the hidden count in the summary line**: `đang hiện <N> / <total> dòng · ẩn <M> việc đã xong`. Without
  it, a collapsed list reads as missing rows — the same misreading as an unexplained empty filter result.
- **The intersection trap is the one that bites.** Hiding done while the owner filters state to `XONG` yields
  zero rows and looks like data loss (see §7). Either auto-clear the hide mode when the filter selects the hidden
  value, or explain the empty result in place with the counts per filter and a clear-filters control, and make
  clear-filters restore the default view.
- **Match the state value loosely** — trim whitespace and compare case-insensitively; a row stored as `XONG `
  or `xong` otherwise stays visible while its neighbours disappear.
- **Ship it in every UI the owner can reach** (the new React `/v2` *and* the old vanilla page) so the two do not
  disagree about what the board contains; use the component library's own control, not hand-written CSS.
- Acceptance: a role-play test that (a) lands on the page and asserts the done rows are absent, (b) toggles the
  control and asserts the visible count changes by exactly the hidden count, (c) reloads and re-asserts, (d)
  opens a fresh tab from the copied URL, (e) exercises the filter-intersection case above, (f) re-reads the API
  afterwards to prove no row's data changed, and (g) runs at desktop **and** mobile width.

### 5e. When the board gets mixed, the owner asks for GROUPS — split by audience and hide the group they deprioritised

The next request after "hide done" is usually a *grouping* one, and the owner states the split themselves
(*"nhóm test case t đánh giá chưa cần mà đang gây rối, chia nhóm event khách hàng ra đi"*): a board that grew past
~40 rows mixes player-facing feature work with internal quality/tooling work until it is unreadable, and the
rows the owner is not acting on are what they want gone from view.

- **Group by audience/deliverable — not by severity or by who works on it.** Three buckets cover the real mix:
  player-facing event/product work, internal test-and-quality work, and infrastructure/tooling work. Ask nothing:
  the owner names the buckets while complaining.
- **Allocate contiguous sort-order bands per group** rather than adding a table or renaming ids: `100–199`,
  `500–599`, `800–899`. The groups then sit together in every view (including any CSV/export) with no schema
  change, and a band makes the group derivable — the worker can assign the group column by `sort_order` range
  instead of by a hand-written id list that will rot.
- **Default-hide the group the owner called noise**, using the same mechanics as the done-hiding toggle (§5d):
  framework-native switch, default ON (hidden), persisted in localStorage **and** the URL, with a summary line
  naming the hidden count (`đang hiện 34 / 67 dòng · ẩn 26 việc nhóm TEST`). Keep it a separate control from
  hide-done — they are independent preferences and merging them makes both unpredictable.
- **Same filter-intersection trap, new axis**: filtering the group to the hidden bucket must auto-clear (or be
  explained), never yield an empty board.
- **Say the group split in the report as numbers** (rows per group, hidden by default or not) — the owner checks
  the counts, not the toggle.

## 6. Reading the owner's answers

- Read the **full cell text**. A truncated read (first N characters) silently drops half a decision — an answer
  like "do both, and fix the bug too" arrives looking like "do both". Read whole cells, then act.
- When a row's answer names an option ("A", "the second one"), restate it as what-changes before dispatching, so
  a mis-binding is caught while it is still cheap.
- A row the owner answered moves out of `CHỜ CHỐT`; update its state in the same round you dispatch the work, and
  add rows for the follow-ups the answer created.
