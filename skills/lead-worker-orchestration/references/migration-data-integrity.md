# Data-integrity gates for worker-run migrations

Lessons from a store-merge migration (two inventory tables holding the same asset) that shipped a
testing layer which passed while production was actively losing player data. Applies to any brief that
moves, merges, backfills, or deletes rows players own.

## 1. A test without a named invariant is not a test

"Compare old vs new and flag any difference" is worthless: it has no opinion on which side is correct,
so it passes through a wrong migration. Every gate must start from a written rule of the form
`<table_a>.qty >= <table_b>.qty for every (owner, item)` and assert that rule literally.

Symptoms that a gate is false-green — treat any one of them as a blocker:

- It passes while a known-bad state exists in the data.
- It compares two queries over the SAME already-mutated database (so both sides are equally wrong).
- Its output is identical for every entity (a query that dropped its `WHERE owner_id = ?`); add an
  assertion that two different owners MUST produce different values, and fail on zero collected cases.
- It reports pass without printing how many cases actually ran.
- Tolerance wording like "within expected range" instead of a number you can prove.

## 2. Prove the gate catches the real failure

Before trusting a gate, reproduce the actual past incident as a fixture (seed the exact bad numbers),
show the gate FAILS with the right diagnostic, fix the fixture, show it PASSES, then run a negative
variant (decrement a value) and show it FAILS. If the fixture does not fail, the gate is useless —
stop and report rather than proceed.

## 3. Migration deltas are one-directional

When merging store B into store A (or A into B), the only safe operation is additive:

- Assert `MIN(delta) >= 0` and paste it. Any negative delta means someone is about to lose assets.
- Never delete "orphan" or "clean-up" rows to make totals line up — surplus above the old store is a
  legitimate state and must be preserved.
- Use `GREATEST(a, b)` per key rather than a blanket overwrite: a blanket overwrite silently discards
  value that exists only on one side (e.g. items bought through the web shop that never reached the game
  store). State the per-key formula in the brief and require proof that no owner decreased.
- Freeze a snapshot/audit table of what was applied, so a second run is a no-op and a rollback is
  row-scoped rather than a full restore.

A source that keeps writing during the migration makes any pre-deploy "all invariants pass" condition
unsatisfiable — say so explicitly instead of emitting a gate that can only fail forever. Deploying the
new reader/writer IS the fix for the drift; measure instead of obstructing.

## 4. Verify the write source stopped, by measuring twice

After cutting over, total of the decommissioned store must be unchanged across two readings minutes
apart. If it still grows, an un-migrated write path remains — report that, do not patch the symptom.

Once players start SPENDING from the new store, the old `a >= b` invariant legitimately breaks
(spending lowers the new store while the frozen old one stands still). Re-state the gate as
"the old store is never written again, and no owner's total decreased" rather than leaving a rule that
will scream forever.

## 5. Secrets hygiene in briefs and verification

- Forbid inlining passwords in shell commands: `ps` prints full command lines and leaks them. Route
  everything through the `ops/` helper scripts that read credentials from a file.
- Ban `git add -A` in every brief. Shared repos carry hundreds or thousands of other people's dirty
  files; commit only paths your own work touched, and check push candidates for dumps/`.env`/keys first.
- Never push a repo whose history contains DB dumps or credential files without the owner deciding —
  surface it as a blocker with the file list instead of pushing and hoping it is private.

## 7. A merge that keeps BOTH representations of a requirement writes and charges twice

When a row holds both an old scalar-column form and a new JSON/list form of the same set (five `req_x1..x4` columns
plus a `required_items_json` array), a reader that appends both produces a payload with every item duplicated — and
if the same append feeds the **check-and-subtract** path, the player is charged twice (an amount of 1200 becomes
2400). Visible as "the same item shows up in two boxes" in the UI, but the money bug is the write path, not the
render path.

- The gate must assert the **merged representation equals the canonical set** (item count, per-code quantity, and
  no code twice), and separately that the **charge equals the canonical quantity once** — a display-only assertion
  passes while the economy is broken.
- Dedupe by **resolved item key**, never by label: two labels naming the same item (`"Tinh Thể"` vs `"CRYSTAL"`) look
  like two items and pass a string-level check.
- Diff the representation pair **for every row, not just the one in the report** — a second row sharing the same
  target (a newly inserted source row) carries the same latent bug and is where a naive `LIMIT 1` lookup also picks
  the wrong row.
- A migration that fills the canonical column from the scalar columns must copy them **completely**: a rule that
  prefers an already-populated canonical column silently freezes the poorer version and drops every scalar-only
  item. Prove the post-state against the source-of-record's full item list, once per row.

## 6. Report shape the owner actually wants

Lead with the number that answers their question ("the new store gained N items; it was M short of the
old store before, is P ahead now"), not the process. When a premise you were handed is wrong, refute it
with a query in the same message. Do not re-ask a decision the owner already made, and do not invent an
approval gate they never asked for — those read as obstruction, not diligence.
