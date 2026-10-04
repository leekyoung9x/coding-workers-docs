## 0. The contract is the table the CODE reads — a second table describing the same requirement may be dead

When two config sources describe the same game requirement with different contents, only one is the contract, and
building against the wrong one demands something **impossible**. Observed: the requirement row carried a JSON
column with **3 items** (read by the live web flow — `grep -rn '<table_or_column>' <src>` lands on the executing
line) while a separate materials table carried **10 items** including an extra element-essence; that table was a
leftover from the original plan and read by no live path. Taking the richer table as truth produced a requirement
for an item with **zero sources anywhere in the product and zero holders in the DB** — every player locked out —
and it was reported to the owner as "the economy is broken" when the table was simply stale. The owner caught it
("does it really need that item? the web has no such thing"), which is the second reason to verify before
claiming.

Procedure: locate the reader first (`grep -rn '<table_or_json_column>' <src>`; the executing line beats any
comment), treat only that as the contract, and **mark the stale source stale inside the artefact itself** (set its
note/description to e.g. `KHÔNG dùng — web only checks 8 items`) so the next reader is not misled a second time.
Do not silently delete a table another service may still reference. Two holder counts settle any argument about
"nobody can progress": holders of the item (`SELECT COUNT(*) FROM <bag> WHERE code='<X>'`) and completed instances
(`SELECT COUNT(*) FROM <target_table> WHERE id=<goal>`) — both were `0`, and that was the finding.

Corollary for the owner's challenge: answer from the executing path, not the plan doc — and when the owner's
surprise contradicts a table you just read, re-check the reader before defending the claim.

# Auditing a Live Event / Economy Feature (Read-Only)

Depth for Step 1 recon when the user reports a *runtime data* symptom on a shipped feature:
"I did X but my progress/points did not move", "I claimed Y and got nothing", "the server is slow".
All recipes here are read-only and take seconds — they belong in the brief, not in the worker's unknowns.

## 1. Localize first: build a per-config-row progress table

The single most productive query on any event/quest system: how many progress rows exist per config row,
and how far they got. It immediately shows which rows are dead and which are saturated.

```sql
SELECT c.id, c.<name_col>, c.<key_col>, c.<target_col>,
       COUNT(p.*) AS rows_n, SUM(p.is_completed=1) AS completed,
       MAX(p.<progress_col>) AS max_prog, SUM(p.<progress_col>) AS sum_prog
FROM <config_table> c
LEFT JOIN <user_progress_table> p ON p.<config_fk> = c.id
WHERE c.<scope_key> = '<feature>'
GROUP BY c.id, c.<name_col>, c.<key_col>, c.<target_col>
ORDER BY c.id;
```

`rows_n = 0` for a row whose trigger activity demonstrably happened = that config row never receives
anything. Do not read it as "nobody played" — cross-check the trigger's own counter table first.

## 2. Shared-key starvation (two config rows, one dispatch key)

Symptom: one requirement (e.g. a big 3 000-unit tier) never moves, while a smaller one on the same trigger
fills up and then sits pinned at its cap.

Cause in code: the dispatcher maps a trigger to a config row with a single-result lookup —

```csharp
var quest = quests.FirstOrDefault(q => q.TrackerId == trackerId);   // only ONE row survives
```

With a deterministic ordering upstream (`ORDER BY <sort_col> ASC`), the lowest-sorted row wins **every**
increment forever; sibling rows sharing the key are permanently starved. Fix belongs in code as "apply the
increment to ALL rows matching the key", never as a data edit to the key column (that just moves the
starvation to another row and diverges from the shipped config).

Detection query — group the config by dispatch key and look for >1:

```sql
SELECT <key_col>, COUNT(*) AS n,
       GROUP_CONCAT(CONCAT(id,':',<name_col>,'(',<type_col>,',target=',<target_col>,')')
                    ORDER BY id SEPARATOR ' | ') AS rows
FROM <config_table> WHERE <scope_key>='<feature>'
GROUP BY <key_col> HAVING COUNT(*) > 1;
```

Then compare the config sort order against which row got the data — the receiving row is the minimum,
proving the `FirstOrDefault` path.

## 3. Early `return` that drops a side effect (once-per-period actions)

Symptom: an action a player can legitimately perform only once per day (check-in, daily claim) is not counted
for everyone who performed it *before* some deploy/flag time, and there is no way for them to re-trigger it.

Cause: the handler returns on the "already claimed" branch **above** the line that reports the event to the
progress tracker:

```csharp
if (existing != null && existing.Claimed)
    return ... "already claimed today";     // ← returns first
...
await _tracker.<SideEffectAsync>(userId, eventKey);   // ← never reached on the second call
```

The fix has two halves and the brief must own both: call the side effect on the already-claimed path too
(after the same guard), and make it idempotent per period. Do **not** re-fire a blanket "period" idempotency
key on a tracker that is shared by several config rows (it would suppress the siblings) — if the tracker
belongs to one row only, a unique-keyed ledger row is the cheapest correct dedupe.

Diagnostic — a LEFT JOIN of the action's own record against the progress row shows the whole lossy subset:

```sql
SELECT a.user_id, a.<claim_time_col>, COALESCE(p.<progress_col>, -1) AS prog, p.<date_col>
FROM <action_table> a
LEFT JOIN <user_progress_table> p
       ON p.user_id = a.user_id AND p.<config_fk> = <config_row_id>
WHERE a.<claimed_col> = 1 AND a.<date_col> = CURDATE()
ORDER BY a.<claim_time_col> DESC;
```

Every `prog = -1` row whose claim time precedes the failure window is a lost unit of progress. Counter-check
that the rows WITH progress all have claim times AFTER the enable/deploy timestamp — that is the proof the
cutoff is temporal, not random.

## 4. Producer still writing while the feature is off

Before any reset, measure rows generated while the feature was nominally disabled: group by date and look for
today's date (see `brief-facts-and-data-mutation.md` §4 for the gating procedure). A reset without gating is
refilled within days and the symptom returns.

## 5. Acceptance numbers that are actually diagnostic

For "is everyone counted", the useful pair is coverage plus cardinality, not a total:

```sql
-- coverage: everyone who did the action has a progress row
SELECT (SELECT COUNT(*) FROM <action_table> WHERE <date_col>=CURDATE()) AS did_action,
       (SELECT COUNT(DISTINCT user_id) FROM <user_progress_table> WHERE <config_fk>=<id>) AS have_progress;

-- cardinality: nobody got double-counted
SELECT <progress_col>, COUNT(*) FROM <user_progress_table>
WHERE <config_fk>=<id> GROUP BY <progress_col>;
```

Equal counts and a single `progress = 1` bucket = clean. A bucket with `progress = 2` means the dedupe key is
wrong (frequently a period key colliding with shared rows — see §3).

On live production, assert per-id, never on global totals: real players write while your acceptance runs, so
the table total drifts a few rows between the worker's dry-run and your re-measure, and a `COUNT(*)` equality
fails on the traffic rather than on the worker. Take the exact id list from the brief and verify those rows.

## 6. Backfill policy (when restoring lost progress is allowed)

- Allowed ONLY with a **measurable per-user source** for the increment (a counter table, a deduction log, a
  damage table). Query it, aggregate per user, and show the dry-run count before writing.
- If no such source exists, **do not backfill** — report "no reliable per-user source, not backfilling" with
the reason. Inventing or apportioning numbers corrupts the economy permanently and is unrecoverable.
- Cap at the config target, and for period-scoped rows add only the current period's worth.
- Backup the whole affected scope, dry-run, write, then re-run the coverage/cardinality queries from §5 and
  assert the delta equals the dry-run.
- Never restore by widening the reset: a post-enable restore deletes progress real players earned legitimately.

## 6b. Compensating an "I got nothing" report: check the ledger before paying

A player-facing "not received" is not evidence a reward was lost. Where the claim path is idempotent through a
ledger/transaction table, the per-row `is_claimed` flag can be meaningless: the reward lands in the ledger while
the row still reads unclaimed, and the UI then renders it as pending. Before promising or paying anything:

```sql
SELECT * FROM <ledger_table> WHERE user_id=<id> AND source='<source>' ORDER BY created_at DESC LIMIT 5;
```

- Ledger row present for the period ⇒ the report is a display bug; the fix is the UI/report path, and paying
  would double-grant. Say which it is explicitly, because "we gave it to you already" and "we owe you" lead to
  different work.
- Ledger row absent ⇒ compensate per §6, per user, only where a counter proves the action happened today.
- Compensate by making the row CLAIMABLE (`is_completed=1, is_claimed=0, <date_col>=today`), never by crediting
  the currency/items directly: the player then receives exactly the configured reward through the normal claim
  path, so the config stays the single source of truth and the amount cannot drift.
- Re-read the compensated rows by id, and treat a real claim (with its ledger row) as the proof it landed — a
  row left claimable is intent, not delivery.
- The many rows stuck in the same state are the size of the display bug, not the size of the debt; only the
  ones with today's counter are owed, and that subset is usually a handful.

## 6c. An audit table is evidence only if the path you are auditing writes it

Before briefing any "prove who received what" investigation, confirm the log table is populated **by that
path** — sample a known-recent transaction and read its timestamps:

```sql
SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM <log_table>
WHERE <item_or_source_col> LIKE '<thing>%';
```

Many projects ship a transaction/audit table that only the game client writes, or that only one of several
services writes, so the web/API path under investigation leaves it empty. An empty result from such a table
reads exactly like "no grant ever happened", and a worker handed that query returns a confidently wrong
verdict. Confirm the writer before the query becomes an acceptance criterion.

Fallback when the path does not log: the per-user item table's `updated_at` (`ON UPDATE CURRENT_TIMESTAMP`).
One logical grant touches every affected row **within the same second**.

- Same second as the action's own timestamp ⇒ **positive evidence** the grant committed.
- A later timestamp ⇒ **no evidence either way**: the column holds only the LAST mutation, so an earlier grant
  is overwritten by any later unrelated change to that item. Never report "reward was lost" from this alone.
- Classify every case into three buckets and never merge them: `CONFIRMED RECEIVED` (same-second rows),
  `CONFIRMED LOST` (a failure window is proved AND the action falls inside it), `CANNOT DETERMINE` (no positive
  evidence and no provable window). Only the middle bucket is owed automatically; hand the third to the owner
  with the item and amount. Never let a worker's inference — "the ledger row exists, so the transaction
  necessarily committed" — count as the first bucket; require the raw rows.
- The failure window itself needs both halves before it exists: the moment the config first carried the new
  value, and the moment the code that can consume that value started serving. Prove each from file/backup/
  container timestamps, and note that a mapping constant present in an OLD commit means that value could never
  have been swallowed — which shrinks the window to the genuinely new codes.

## 6d. Refund the thing that was SPENT, apply it to every affected user, and never claw back below zero

Three rules that turn a compensation round from a second incident into a closed one.

**Direction: return what they paid, not what they would have received.** When a trade consumed item A and the
grant of item B failed, the debt is **A**. Paying B looks reasonable ("B is what the recipe promised") and is
wrong: it changes the player's inventory into something they never chose, and if B is a higher-tier currency it
is a stealth upgrade. State the rule in the brief in exactly this form — *return the input, not the output* —
and make the worker prove per case which item the player actually spent before it writes anything.

Same rule applies to a review of an earlier compensation round: when an earlier round paid the output, the correction is
to **reverse the wrong grant and pay the input**, which means two ledger directions in one pass, not a third
grant on top.

**Consistency: fix the rule, then sweep every user it applied to — not just the one who complained.** The
complaint localizes the bug; it does not define the affected set. Query the grant/trade history for **all**
rows matching the same fingerprint and list them before writing; in practice the complainer is one of several
(one user's case was handled while the identical mis-grant survived for three more users, which is how the
inconsistency became visible). Present the full set and the per-user amounts; if the owner has chosen a
direction, applying it to part of the set is a defect, not caution.

```sql
-- find EVERY row a partial fix left behind, not just the reported one
SELECT id, user_id, <amount_col>, <detail_col>, created_at
FROM <grant_table>
WHERE <action_col> LIKE '<mis-grant-action>%' OR ref_id LIKE '<fingerprint>%'
ORDER BY user_id, created_at;
```

**Arithmetic: a clawback must not push a balance negative — stop that case and report.** If the player already
spent the wrong grant, subtracting it drives the balance below zero and corrupts the ledger. Do not clamp,
do not borrow from another item, do not silently skip: halt that user's case and hand the owner
(user, shortfall, current balance). Put the constraint in the brief as a hard stop, because the worker's default
is to make the number go down.

Acceptance numbers for a reversal round, all required:
- a mapping table **each mis-grant row → the original transaction → the item actually spent → what is owed**;
- rows that cannot be tied to a definite spent item are marked **NOT PAID + reason**, not guessed;
- before/after balances per affected user showing the wrong grant down by exactly what it added and the correct
  refund up by exactly what was spent (total delta 0);
- a scan proving **no negative** balance anywhere;
- a second run that is a **no-op**, which is what proves the dedupe key is right;
- rows outside the affected set (other users, other event keys, other quarters of the ledger) unchanged.

## 6e. "I claimed the reward and got nothing" — check the delivery CHANNEL, not just the grant

A grant can commit perfectly and still be reported lost, because the player looks somewhere the reward never
appears. Before treating the report as a data bug, check that the surface the reward lands on is a surface the
player can actually open:

- Trace the reward to where it is stored (bag table, gift/inbox row, chest row) **and** to the UI that opens that
  container. A container whose only opening control exists on one channel (e.g. a chest purchasable and opened
  only on the web page) is invisible to a player who received it in-game — they search the game, find nothing,
  and report a lost reward.
- Prove it from the data before paying anything: if every claim row has its matching open/spend row, the reward
  was delivered and consumed, and the complaint is a **channel/visibility mismatch**. Repair the visibility (or
  stop routing rewards into a container the receiving channel cannot open), and do not re-grant.
- Check this as a **design** question too, not only as a bug: before routing a reward through a container, confirm
  the receiving channel has an opener. If the inbox schema is a fixed column set (no arbitrary-item field) then
  an item-container cannot travel through it at all — deliver the resolved item, or add the schema field, and say
  which, instead of shipping a grant that strands the item.

## 7. "The server is laggy" — separate host load from the network path

Measure both before accepting either explanation, and measure from at least two vantage points, because a
single vantage proves nothing about the players' route:

- **Host**: `cat /proc/loadavg` (compare to CPU count), `free -m`, `df -h` + `df -i` (inodes), `docker stats --no-stream`
  for per-container CPU/RAM, `docker inspect <c> --format '{{.RestartCount}}'`, `dmesg | tail` for OOM/IO errors.
- **Data layer**: processlist for queries running long, connections vs `max_connections`, slow-query counter,
  and the largest tables by `data_length+index_length` — a bloated table is the usual real cause.
- **Network path**: `ping -c 20` (report packet loss, not just RTT) and `mtr -rwzc 15 <ip>` — the per-hop loss
  column identifies the exact inter-carrier segment. Correlate with app latency: a bimodal TTFB
  (fast most of the time, ~3x spikes) matches packet loss, not server load.
- **A/B the same app on two hosts** through the same CDN — if one host answers in tens of ms and the other in
  ~1 s while both are idle, the finding is the path/host quality, not the code.
- Never "confirm" the fix for a lag report from one vantage point; state whose measurement it represents and
  what would settle it (a probe from the players' own network).
- Also read the app log for the OTHER reason a user says "lag": a failed auth/token exchange that blocks them
  from entering the game at all looks identical to slowness in a bug report. `grep -i 'token\|unauthorized'`
  the web/app logs for the reporting window before chasing infrastructure.

## 8. Period rollover: the reset must run BEFORE the already-done check

Symptom: a daily/periodic task shows `0 / 1` and cannot be re-completed by players who completed it on an
earlier day — while the trigger's own counter table proves the action DID happen today.

Cause: the handler tests "already claimed" before it tests "is this row from an earlier period", so yesterday's
completion short-circuits the rollover:

```ts
if (Number(rows[0]?.is_claimed ?? 0)) continue;   // ← bails out first
const stale = row.date_ymd !== today;
if (stale) { progress = 0; claimed = 0; }         // ← never reached
```

Recompute period staleness from the date column FIRST (clearing `is_claimed`/`claimed_at` as part of the reset),
then apply the already-done check. When a web path and a backend path handle the same row and only one is
broken, that disagreement itself localizes the bug — the correct path resets before it checks claimed.

Second half of the same bug: the write that stores progress must also write the period date column. An
`UPDATE ... SET current_progress=..., is_completed=... WHERE id=@Id` that omits `event_date` leaves the row
stale forever, so every later increment re-enters the rollover branch instead of accumulating.

Detection — join the period counter against the progress row and look for a date older than today:

```sql
SELECT p.user_id, p.<date_col>, p.is_completed, p.is_claimed, c.<date_col> AS counter_date, c.<value_col>
FROM <progress_table> p
LEFT JOIN <counter_table> c ON c.user_id = p.user_id AND c.<key_col>='<action>'
WHERE p.<config_fk>=<id> AND (p.<date_col> IS NULL OR p.<date_col> < CURDATE());
```

- Separate "stuck from an earlier period" from "owed today" with that join: only rows whose counter is dated
today are lost work (§6/§6b); the rest heal on their own once the ordering is fixed.
- An empty `catch {}` around the progress/tracker call hides this whole class for days. Every call site that
  reports progress must log on failure — a swallowed exception on a once-per-period action is invisible until a
  player complains.

## 9. An entity is never "missing" until the activity table says so

When a gated feature keys on an id (a boss pet, a stage, an item) and the obvious config table contains no such
row, do NOT conclude the entity does not exist or the feature is impossible. Config tables describe only the
flows they serve; two flows can carry the same-named FK with different meanings. The live activity table is the
proof of what actually happens.

- Read the activity/history tables (`match_history`, room/battle tables, attempt tables) and group by the id.
  Rows dated today with that id prove the flow is live, whatever the config table says.
- Then read the submit path to learn the id's meaning per flow: one dispatcher may send `<fk> = <entity>.id`
  (the entity id directly) while another sends a scheduling-table id that must be mapped through a lookup —
  same column, two meanings, so a plain `grep` of the config-table name inside the service can come back empty
  while the id genuinely flows every minute.
- Report it as "not found in `<table>`" and keep probing until the activity table confirms or refutes.
- **A query that errors is not a query that returned nothing**: `Unknown column 'x' in 'field list'` is a
  stopped query, not an absence — read the real names from the catalog (`information_schema.columns`,
  `DESCRIBE`, `SHOW TABLES LIKE`) and re-run before drawing any conclusion. Announcing an absence that the
  very next activity table disproves costs credibility that the correct query would never have risked.
- Two-sided acceptance recipe once a gate keys on that id: take the newest activity row, sum the per-player
  values it records, and assert the counter delta equals that sum exactly
  (`43014 + 11300 → counter +54314`). That proves the ALLOWED path flows end to end; the DISALLOWED path is
  proven by the same counter standing still for the other ids in the same window — check both, in the same run.
- Also confirm the neighbouring flow sharing the changed code still works (a second event keyed on the same
  submit path): compare its quest completions before/after the deploy timestamp, not just its counter totals.
- **Narrowing a rule retroactively leaves pre-gate accruals in place — never wipe them as a side effect.**
  When a gate starts crediting only one id, the data accumulated under the old permissive rule stays. Measure it
  (rows, distinct users, summed value, and any reward rows already claimed from it) and hand the wipe/keep
  decision to the owner with that evidence; deleting player accruals or already-granted rewards is their call,
  and keeping them is the safe default.

## 9b. A progress row's own description enumerates its producers — count the bump sites against it

Symptom: "this new feature should count toward quest X, but quest X does not move for it".

The config row's description is a checklist. When it reads *"each bake counts 1, each trade counts 1, each
pack-open counts 1, three total completes it"*, then three **distinct producers** must call the tracker bump —
and a fourth producer that consumes the same resource (a second crafting machine, a second entry point) belongs
in that set too, or it silently spends the player's allowance without advancing the quest.

Method, three read-only queries:

```sql
-- 1. the config rows and the shared dispatch key
SELECT id, <name_col>, <desc_col>, <key_col>, <target_col> FROM <config_table>
WHERE <scope_key>='<feature>' AND (<name_col> LIKE '%…%' OR <desc_col> LIKE '%…%');

-- 2. who performed the new action, and when
SELECT user_id, COUNT(*) n, MIN(<ts_col>) first_at, MAX(<ts_col>) last_at
FROM <action_log> WHERE <action_col>='<new_action>' GROUP BY user_id ORDER BY n DESC LIMIT 10;

-- 3. what each of those users actually got counted for
SELECT p.user_id, p.<config_fk>, c.<name_col>, c.<key_col>, p.<progress_col>, p.is_completed, p.<date_col>
FROM <progress_table> p JOIN <config_table> c ON c.id = p.<config_fk>
WHERE c.<scope_key>='<feature>' AND p.user_id IN (<ids from query 2>);
```

Read the result as arithmetic, not as a boolean: a user who performed the action **3 times** should show the
expected count on the row the description assigns it to. A row absent for *every* actor of the new action
(while the sibling row on the same shared key advanced) pinpoints the missing bump site — the new code path
calls the tracker with the sibling's key only.

- The code side is a `grep` of the bump helper (`grep -n '<bump_fn>' <actions_file>`) mapped back to enclosing
  function names, so the brief can state exactly which producers do and do not report progress.
- **Answer the anti-abuse counter-argument inside the same brief**: this project had *deliberately* left one
  producer un-bumped because its inputs were purchasable with the reward currency, which would have closed a
  buy→progress→reward loop. Before asking a worker to add a missing bump, show the new producer's inputs are
  earned (fixed drop cost, no currency purchase path); if the loop can close, stop and escalate instead.
- A sibling producer the description does not mention (e.g. the older machine on the same resource): raise it
  as a **proposal for the owner**, never as part of the fix — same key, same resource, different intent.
