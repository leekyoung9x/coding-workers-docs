# Brief Facts and Data-Mutation Hygiene

Depth for Step 1 (brief authoring) when a task asserts facts about a system or mutates live data.

## 1. Verify the facts you put in the brief

A brief is a spec the worker is expected to challenge. Every wrong fact costs a worker cycle: it either
implements against a phantom (a table that does not exist, a column that is not there) or stalls to
discover the truth. Confirm, do not recall:

| Fact you want to assert | Command that settles it |
|---|---|
| Table / column names, column count | `SHOW TABLES`, `SHOW FULL COLUMNS FROM <t>`, `DESCRIBE <t>` |
| Which container serves which DB / port | `docker ps --format '{{.Names}} {{.Ports}}'`, `docker inspect <c> --format '{{range .Config.Env}}{{println .}}{{end}}'` |
| Which DB a web app actually writes | read its env (`DB_NAME`, `DB_HOST`) and `docker inspect` mounts — not its docs |
| Whether a remote asset/URL exists | `curl -s -o /dev/null -w '%{http_code}' <url>` |
| Row counts / distributions you cite | the exact SELECT, run now |
| Which repo will carry the commit | `git -C <dir> rev-parse --show-toplevel` |

If you cannot settle a fact with a command, write it in the brief as a question the worker must answer
first — an honest open question is cheaper than a confident error the worker builds on.

## 2. Git topology: a directory is not a repo

A working directory can sit inside another repo's tree with no `.git` of its own, or be covered by
`.gitignore`, so a brief that says "commit your changes in `<dir>`" is unexecutable there. Determine the
single repo that will carry the commit and name it by absolute path:

- `git -C <dir> rev-parse --show-toplevel` — prints `<dir>` only if it IS a repo root; anything else means
  it is not one (or is a nested worktree of another repo).
- `git -C <parent> check-ignore -v <dir>` — a gitignored dir is a build/copy artifact: run tests there,
  never commit there.
- Source trees that exist twice (a committed build-tree and a scratch copy) drift apart file by file.
  Never rsync/copy the whole tree between them; copy the single files the task touched and prove the copy
  with a hash (`md5sum` on both sides).

## 3. Shared-repo commit hygiene for parallel workers

When two workers run against one repo, have each one:

- `git add` only its own explicit file list. Never `git add -A`, `git add .`, or `git commit -a`: repos in
  active work carry dirty submodules and untracked junk that get swept in and are painful to unwind.
- Print `git status --porcelain` before and after staging, so the report shows exactly what entered the index.
- On `Unable to create .../index.lock`, `sleep` and retry in a bounded loop; never delete another process's
  lock file.
- Verify the push landed by comparing local and remote: `git rev-parse HEAD` == `git ls-remote origin <branch>`,
  and treat the worker's commit URL as a claim to check, not proof.

## 4. Data mutation: gate the producer, then wipe

A wipe brief that only deletes rows is a temporary fix whenever something still generates them. The check
is one query: does the table contain rows dated AFTER the feature was supposedly turned off?

```sql
-- rows produced while the feature was nominally OFF
SELECT <date_col>, COUNT(*), SUM(<metric>) FROM <progress_table>
WHERE <feature_key> = '<feature>' GROUP BY <date_col> ORDER BY <date_col> DESC LIMIT 10;
```

- Non-empty with today's date = a live producer (background tracker, queue consumer, cron) is still writing.
  The brief must gate that producer by the same predicate the user-facing entry points use, and only then wipe.
- Say which predicate is authoritative (e.g. active flag AND earning flag, both required) and reuse it verbatim
  across every surface — web entry points, backend tracker, scheduled jobs. Two different definitions of
  "enabled" is how a gate leaks.
- Reset adjacent to enable. State explicitly whether the reset is protected by the producer gate (safe to do
  early) or not (must happen immediately before enabling).

## 4b. Shared test databases: forbid flag flips, not just data wipes

A wipe is not the only destructive write a worker performs. When the test DB is shared by concurrent
sessions, the feature-toggle flags themselves are shared state, and a worker touching them kills another
session's environment silently.

The trap: a brief that says "test the disabled path" invites `UPDATE <flag_table> SET enabled=0`, and the
worker's own cleanup usually snapshots the *current* value as "original" — so after it flips the flag off
and cleans up, it restores the OFF value it just wrote. The feature stays dead for everyone else, and
nothing in the worker's report flags it because from its point of view cleanup succeeded.

Rules to put in every brief that touches a shared test DB:

- **Forbid flipping any feature-toggle flag** (`is_active`, `enabled`, `earning_enabled`, …) — including
  "flip it off, test, flip it back". Testing the disabled branch must use a private test DB, a unit test
  against a mock, or a temporary row the worker owns. Name the flag columns explicitly.
- **List the tables/flags other sessions rely on as read-only**, separate from the tables this task may write.
- **Require the cleanup code to restore a value captured by the LEAD before dispatch** (or a hard-coded
  expected value), never "whatever it is when I finish".

Lead-side acceptance for any such brief: snapshot every flag in the toggle table before dispatch
(`SELECT <key>, <flag1>, <flag2> FROM <flag_table>`) and re-read the WHOLE table after, not just the row the
task touched. A single-row check misses collateral flips.

Recovery when a flip escapes anyway: `mysqldump --where="<key>='<value>'" <db> <flag_table>` as the restore
record, restore the flags, then **verify through the running app** (an authenticated request that renders the
feature) — a DB read alone does not prove the app is serving it again.

- Remaining consequence to own: a worker resetting for its own task still deletes rows its own tests need
  nowhere but which another concurrent session was using. Tell the user plainly which rows went, that a
  backup exists, and ask whether to restore rather than deciding silently.

## 4c. Every mutation brief names its own rollback

Write the rollback into the brief as a command, not as an intention, next to the backup path:
`docker exec -i <mysql-ct> mysql -uroot -p<...> <db> < /root/backup-<tag>-<ts>/<table>.sql`, or a per-row
`UPDATE ... WHERE id IN (...)` restoring the exact pre-state values the dry-run printed. State which one and
for which ids. A report that says "backup exists" without a runnable restore path leaves the next person
improvising on live data — and the dry-run's pre-state dump is what makes the per-row restore possible at all.

## 5. Before/after evidence the brief must require

1. `mysqldump` of every table to be mutated into a timestamped backup dir; print `ls -la`.
2. Require the backup to live **outside the worker's own workspace** (a host path like `/root/backup-<tag>-<ts>/`,
   not `<repo>/backup/`), and require the report to print its absolute path plus a checksum
   (`sha256sum <dump.sql>`). A dump inside the repo the worker is editing can be deleted by its own
   cleanup, and a backup nobody can locate after the fact is the same as no backup.
3. A dry-run SELECT counting the rows each write will touch, then the same count after — equal, or the scope
   is wrong. On live data, assert per id (the ids from the dry-run), not on whole-table totals: real traffic
   moves the total between the two measurements.
4. Neighbouring features' row counts before and after, to prove the scope boundary held.
5. Idempotency: state that a second run changes 0 rows, and run it twice to show that.
6. Prefer an idempotent statement over an exact-count one. A conditional `UPDATE ... WHERE id IN (...) AND
   is_claimed=1` applies once and changes 0 rows on a rerun, so a late or duplicated run cannot double-grant;
   a write shaped as "set these to X" silently reverts anything the player did in between.
7. Test environment first, then the target — never in the other order.

## 5b. Consolidating fragmented sources into one: the most COMPLETE source wins

When the owner asks to merge duplicate/overlapping config into a single source of truth ("it's hard to manage
fragmented like this"), two traps decide whether the merge loses data or not.

**Trap 1 — taking the source the app currently reads as canonical.** The column/table the running app already
reads is not necessarily the fuller one. Observed: the app read a JSON column holding 3 items while a legacy
table held the same 10 — migrating with the rule "current column wins" deleted 7 items of a real cost table
(player economy data), and every test stayed green because the covering spec asserted one row plus one extra
field. Take a **snapshot of every source first** (read-only, into the backup dir, even if nobody asked), then
merge at ITEM granularity from the fullest source, preserving every quantity exactly. The owner's requirement in
a storage-move is normally "nothing changes, only where it lives" — confirm that, because altering values during
a merge is a separate decision the owner must make explicitly (e.g. a required level moving from 4 to 5).

**Trap 2 — a "no readers, safe to drop" verdict scoped to one repo.** A consolidation brief invites the worker
to declare legacy objects dead, and it answers against the codebase it was given. Two config tables were queued
for DROP while a live service of ANOTHER language in the same machine read them with hard-coded SQL in its own
query/repository layer — the drop would have broken the feature in production, and nothing in the worker's
report flagged it because from its scoped grep the reader count was zero.

### Gate before any DROP

1. Sweep **every codebase on the machine**, not the app being edited — every language/solution, plus migration
   files. `grep -rn '<table_or_column>'` across the workspace root, one language tree at a time.
2. Sweep **DB metadata**: FK, VIEW, TRIGGER, STORED PROCEDURE/FUNCTION, EVENT referencing the object
   (`information_schema.KEY_COLUMN_USAGE`, `.VIEWS`, `.TRIGGERS`, `.ROUTINES`).
3. Emit an evidence table shaped `legacy object | reader count | file:line or DB object | verdict`. "Grep of
   app X = 0" is NOT evidence, and a worker's paraphrase is not either — re-run the sweep at acceptance.
4. Any surviving reader ⇒ **do not drop**. Migrate that reader to the canonical source, give it its own test,
   and drop in a later pass. When not certain: mark deprecated only (table COMMENT — metadata-only, reversible).
5. Prove the schema is the only thing moving: capture row counts / checksums for the objects that must stay
   untouched and assert them unchanged afterwards. Consolidate and drop are **two briefs**, never one.

### Ordering for a merge that ends in a production write

The owner's "merge it" authorises the data work, not a production mutation — get an explicit yes for prod
before it happens, and record it in the brief. Then: (1) clone the prod DB into a scratch database, merge and
run both test suites there; (2) migrate every remaining reader to the canonical source and build/test that
service; (3) only then the target — backup + checksum, a read-only pre-check that must match or STOP, an
idempotent write keyed on business keys (**never** on `id`, which differs between environments), re-verify
against the snapshot, deploy, and verify the live endpoint returns the full expected payload.

Because legacy tables and the canonical store coexist during phase 2, do not delete the legacy tables until the
schema spec asserts they are gone — and expect a spec asserting "deprecated" to go red on purpose at that
moment, which is the reminder that the last step is still owed.

## 6. Text/encoding fixes: verify bytes, never the rendered string

A mojibake repair is a byte-level write and the decoded result lies: Unicode diacritics that differ by one code
point render almost identically, so "looks right", `LENGTH()`, and row counts all pass on the WRONG character.
The worker will also print a hex it believes is correct — as Lead, re-run that hex yourself against a
known-good reference before accepting the fix.

- Find a known-good copy first (the same item in the test/staging DB, the seed file, the design doc) and diff
  `HEX(col)` against `HEX(reference)` — not the human-readable text. A prod `…E1BBA1…` against a reference
  `…E1BB9B…` is a single-glyph difference (`ỡ` vs `ớ`) that no eyeball catches.
- Distrust mechanical re-decoding: a double-encoded string can decode "successfully" into a different valid word,
  which is how a plausible-but-wrong repair gets shipped. Take the verified literal and write it as bytes so the
  client charset cannot re-corrupt it:
  `UPDATE <t> SET <col>=CONVERT(UNHEX('<verified hex>') USING utf8mb4) WHERE id=<id>;`
- Sweep the whole DB for the corruption pattern instead of fixing only the reported row: the same bad import
  usually hit several tables (an item catalog row AND the shop row that sells it). Scan by hex pattern
  (`HEX(<col>) LIKE '%C386%'`) — the corrupted string is not searchable by the characters you expect to find.
- Expect false positives: a legitimate `Ã`/`Â` inside a Vietnamese sentence shares the same lead bytes as a
  mojibake artifact. Confirm the whole sequence decodes to valid words before rewriting, and report the ones you
  deliberately left alone.
- Backup the exact pre-state as a runnable per-row statement (the `quote(<col>)` value), so rollback does not
  depend on re-typing the corrupted text by hand.
