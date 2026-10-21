# Brief anti-loopholes, watchdog, and completion reporting

Companion to the Lead–Worker protocol: lessons from rounds where correctly-briefed
workers still produced hand-drawn stand-ins, died silently, or finished without the
user being told.

## Ban fallback language in the brief itself

A worker takes the cheapest route to the numbers you wrote. Any permitted escape hatch —
"temporary", "fallback", "placeholder", "mask", "draw it for now", "keep layout with code" —
becomes the delivered product (measured: five consecutive rounds each shipped a hand-drawn
stand-in through exactly such a clause). Write the rule as: missing art = render NOTHING +
one `console.warn` per missing key + a `MISSING ART` list naming the exact Figma nodes.
Forbid the escape words literally in the brief's CẤM/never section, and add a grep-able gate
(e.g. zero hits for the banned words in `src/`, a fixed graphics-object count) so a
stand-in fails acceptance instead of passing it.

## Separate render-style from art replacement in the brief

Strokes, text outlines, and border gradients are render style; panels, characters, icons,
and backgrounds are art. State per item which class it belongs to and where the numbers
come from: style values must cite a measurement from the source art (colour stops, weight,
position), never an invented constant. A worker handed only a fixture with empty style
fields will invent the numbers — so a fixture that lacks a field is itself a defect to fix
(re-export or re-measure), not a licence to guess.

## Never assert a style fact from MCP output alone

Figma MCP (`get_design_context` / `get_metadata`) can drop or simplify style fields:
observed more than once, a Linear gradient stroke reduced to a solid `border-[#...]`,
and raw metadata omitting strokes/fills/effects entirely. The canvas the designer drew
(Appearance panel: Linear, Outside, Weight) is ground truth, never the MCP output.
Cross-check via screenshot of the Appearance panel or the in-Figma Plugin API
(`node.strokes`, which preserves gradient stops) before asserting "solid" / "no stroke",
and never argue a style fact against the design owner from MCP-derived code alone.

## Watchdog silent workers; do not discover death from the user

A worker process can die (timeout, SIGTERM, transport reset) with only a one-line launcher
note. Poll the process table plus the brief log on a timer while anything is dispatched;
when it exits without a result, re-dispatch promptly. The user asking "is it done yet" is
the failure signal — it means the watchdog did not exist.

## Report completion in the same turn, unprompted

The moment a worker's completion notice arrives, verify (re-run the suites, re-measure the
symptom, screenshot) and report changed / verified / left immediately — never end the turn
waiting for the user to ask. A status-only reply with no verification attached reads as a
stall when the work is unfinished.

## Lead never touches code — including one-liners

Even a "trivial" deletion or constant tweak goes into the next brief, not into a direct
edit. Foreground patches by the lead bypass the brief's gates, break the blame trail, and
the user reads them as role violation. When a past lead edit caused the current symptom,
say so by name in the reply and put the revert in the brief.

## Scope QA gates to the feature; ban sleep-poll loops

A brief that orders the full suite (`test all`) for a scoped feature burns most of its steps on unrelated cases, because the worker obeys literally. Name the exact spec(s) plus smoke in the brief; reserve the full suite for prod deploys. Forbid long `sleep`-poll loops for builds/tests — each sleep is a billed step with no checkpoint, so dozens of them look like progress while measuring nothing; require bounded checks with a result read each round.

## Fail-Closed Economy & Transaction Safety in Briefs (CRITICAL LESSON 20/10)

A Lead must NEVER introduce "test fallback" or "free pass" clauses in implementation briefs for backend mutations, economy endpoints, crafting, or shop actions.

### 1. The "Fallback Shortcut" Catastrophe
- **Forbidden brief pattern:** "Kiểm tra nguyên liệu (hoặc nếu tài khoản chưa có thì cho cắm hoa nhận ngẫu nhiên +10/+20/+50 để test)".
- **Consequence:** The worker implements the fallback literally in production code (`if (!hasAll) grantPoints()`). Players discover zero-cost button spam, in-game currency is minted out of thin air, and massive economy rollback is required.
- **Strict Rule:**
  - **FAIL-CLOSED ALWAYS:** If prerequisites (materials, balance, daily cap, level) are unmet, the server MUST reject immediately (`return { success: false, error: ... }`) and touch ZERO database rows.
  - NEVER permit client or server fallback branches that award progress without deducting full cost.
  - If a test environment lacks materials, the brief MUST instruct seeding actual test rows in DB (`INSERT INTO user_items ...`), NEVER writing mock bypasses in production-bound handlers.

### 2. Mandatory Anti-Cheat / Negative Testing Gates in Briefs
Every implementation brief involving mutation/economy MUST specify explicit negative test assertions:
- **Zero-Balance / Missing Material Gate:** Assert that calling the endpoint with 0 items returns HTTP 400 or `{ success: false }`, and database tables (`user_items`, `event_wallet`, `event_ledger`) have 0 new rows added.
- **Concurrency / Double-Click Gate:** Assert that concurrent spam clicks do not result in double deductions or free duplicate rewards. Transactions must use `SELECT ... FOR UPDATE` or atomic floor conditions (`UPDATE ... WHERE quantity >= cost`).
- **Fake Test Pass Prohibition:** Forbid E2E test suites from looping over broken fallback branches to inflate scores for subsequent milestone tests. A test suite that hacks its own game to pass is a corrupted test.

### 3. Content & Catalog Grounding Gate
- NEVER invent game mechanisms, titles, or items not supported by the underlying engine schema (e.g. inventing "Danh hiệu" or "Khung avatar" when the DB schema only supports `user_items`, `user_pet`, `avatars`).
- Every reward item_code must be cross-checked against database catalogs or existing definitions before appearing in a brief.

