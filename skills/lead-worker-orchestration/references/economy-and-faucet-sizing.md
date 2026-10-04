# Sizing a Faucet to a Target (Event Economy)

Depth for Step-1 planning when the owner asks to open, close, or scale a source of event currency — "mở boss X
kiếm N/ngày", "nâng/hạ mốc", "cost ghép = cost kiếm ngày". These asks are design numbers, not bugs: the Lead
owns the arithmetic and must hand the owner an **anchored choice with a table**, never a guess and never a
figure the owner quoted back unexamined.

## 1. Measure the ladder and the live faucets before proposing anything

```sql
-- the reward ladder the number has to land on
SELECT tier, required_<currency> FROM <milestone_table> WHERE <scope_key>='<feature>' ORDER BY tier;

-- every configured faucet, and its per-day ceiling if the schema carries one
SELECT <config_fk>, <name>, <reward_type>, <amount> FROM <quest_reward_table> WHERE <reward_type>='<CUR>';
SELECT <source>, COUNT(*) rows_n, SUM(<amount_col>) total FROM <counter_table>
WHERE <scope_key>='<feature>' GROUP BY <source>;

-- what players actually earn (not what the config promises)
SELECT DATE(created_at) d, COUNT(DISTINCT user_id) users, SUM(<delta>) total,
       ROUND(SUM(<delta>)/COUNT(DISTINCT user_id)) avg_per_user, MAX(<delta>) biggest
FROM <ledger_table> WHERE <scope_key>='<feature>' AND <delta> > 0 GROUP BY d ORDER BY d;
```

Configured income and measured income routinely differ by 5–20× when a cap, a resource ceiling, or a broken
step intervenes. Quote the measured pair (daily average per user, and the best user's day) whenever the owner
asks "is this achievable" — the config number alone has already been wrong at least once.

## 2. Anchor on the design's own season total, not on the number in the request

Milestones are almost always derived backwards from a season budget the designer computed, so **find that
anchor** — then an exact-hit proposal is possible instead of a vibe. Two signals:

- The top milestone's value is usually that season total (a ladder ending at 29 000 when the plan's own table
  sums hardcore to 29 210 is the budget wearing a round-number costume).
- The plan doc will carry a per-source breakdown summing to it. Derive the new faucet as
  `target_total − (existing measured faucets + one-time rewards)` rather than re-picking a number.

**When two tables in the same plan disagree, anchor on the one that matches live config**, and say which one you
used. Design docs drift; the deployed rows are the truth. ``grep`` the plan for the ladder values and the source
breakdown, and cross-read against `SELECT` on the config tables before trusting either.

## 3. Size the faucet as a difference, and split it the way the owner splits it

When the owner asks for equal shares ("một nửa thuộc về săn boss, một nửa thuộc về mini game"), compute the
**per-share per-day** figure for the milestone they picked, and present the resulting coverage of the whole
ladder:

| share A/day | share B/day | season total | milestone reached | what dropping one share costs |

Show explicitly what each source is worth: "drop the mini-game share and the season falls to milestone 6, i.e.
the second source is load-bearing, not decoration". Equal shares are a design statement — demonstrate that
neither source alone reaches the target, or the split is not actually a split.

Before presenting candidates, compute the ladder-closure table (`for each milestone: gap after fixed income →
per-share/day needed`) so the candidate numbers you offer are the ones that land exactly on a rung.

## 4. Verify the resource ceiling before promising a per-day number

A per-day currency figure is only reachable if the underlying consumable permits it. Convert:

- regen rate → free units/day (e.g. `1 per 8 min` ⇒ 180/day), plus any purchasable units/day and what they cost;
- cost per attempt (read it from real activity rows — e.g. per-match turn/energy usage in the history table) →
  attempts/day = ceiling / cost;
- attempts/day × reward-per-attempt = the **soft** per-day ceiling on that faucet.

If the requested per-day figure exceeds that soft ceiling, say so with the arithmetic and offer the two honest
resolutions (raise reward-per-attempt, or add purchasable resource) instead of quietly picking a number the
system cannot deliver. Also state the currency sink that makes a high ceiling non-inflationary, or flag its
absence.

## 5. Mandatory guardrails for every new faucet

- **Per-day cap** on the new source, enforced by a counter read inside the transaction — no faucet without a
  ceiling, since the whole point of a cap is that unlimited play stops paying.
- **Per-instance idempotency key** (the match/room/session id) so a retried or replayed result callback cannot
  pay twice. Prove it: replay the same instance and show the credit does not move.
- **Never trust a client-reported value** (score, damage): derive the payout server-side from a value the server
  recorded, as a step function of it.
- **When a reward container cannot travel through the reward transport, do not invent a new item type — grant the canonical reward and fake the container**: a "chest"/"box" the player supposedly opens is often an artefact of the delivery path, and if the transport (gift/inbox) cannot carry it, the tempting fix is to add a new item code. Correct shape instead: the server picks and credits the **real** reward to the canonical table at claim time, while the client shows a container-open animation over the reward that is already in the bag. State the owner's intent in exactly those terms ("the essence is the player receives the cake; the UI shows them opening a chest"), and make the acceptance prove the negative too — the container item's count must **not** increase, the real reward must increase by exactly the claimed amount, a second claim must add nothing, and two different milestones must not yield the same reward. Where an alternate transport already exists, check its schema first: a transport with a fixed column set cannot carry an arbitrary item, and that finding is what forces this design.
- Keep the ledger invariant intact (`SUM(delta of currency rows) == wallet balance`): if the platform's game
  server has no path to the web-side wallet, say so and let the brief choose the architecture rather than
  inventing a second source of truth.

## 6. A documented cap is not an implemented cap

**Prove a breach with a per-day, per-source query — a lifetime sum is not a daily figure, and an all-source total is not one source's total.** Two wrong reads in one session (first a worker's "this faucet has no cap", then the Lead repeating it) declared the biggest faucet "over cap by 44%" and nearly triggered a nerf of it, while the raw table showed every top account pinned at exactly the cap and stopping there. Both misreads are structural:

- `SUM(delta)` across all days is a **lifetime accumulate**; comparing it to a per-day ceiling manufactures an overflow. Always `GROUP BY user_id, DATE(created_at)` and paste that table.
- Summing without `GROUP BY source` mixes faucets: a single "2 626 total" turned out to be one player's `boss 1 411 + quest 680 + combo 200 + lantern 150 + …`, none of which is that one faucet's income for one day.
- Cross-check the **enforcing counter table** against the ledger for the same user + day (`WHERE source=… AND ymd=<today>`): if the counter is pinned at the cap and the ledger matches it, the cap works and the premise is dead.

Then name which of the two different claims you are making, because they carry different fixes: **"the cap is broken"** (requires a day-grouped query showing an overflow) versus **"the configured pace exceeds the plan budget"** (a design question — e.g. 740/day from one faucet against a 540/day plan total across all sources — answered with a number, not a patch). Only the first justifies a dispatch. Distrust a supplier report until you have reproduced its aggregate shape yourself; the worker that refused to change code because the brief banned a figure change, and pasted the per-day table instead, was the gate working.

**A cap can also be per-source while the season total stays too generous with no bug anywhere** — when the plan's own totals say otherwise, put the pace comparison to the owner as a labelled choice (keep the current per-day ceiling, or lower it to ~N/day) rather than silently nerfing or defending it.

Design docs assert limits that were never built. Before repeating any ceiling to the owner — or putting it in a
brief — `grep` the value across the codebase and the config tables:

```bash
grep -rn '<value>\|<value_with_sep>\|<CamelCaseCapName>' <web_src> <backend_src> --include=*.ts --include=*.cs \
  | grep -v node_modules | grep -v '/bin/\|/obj/'
DESCRIBE <wallet_table>;   -- confirm no cap column exists
```

Also read the credit function itself: an unconditional `balance = balance + delta` with no comparison against a
ceiling proves there is no cap at all, so the only ceiling is the sum of the capped faucets. Reporting a doc's
cap as fact and then having the owner act on it is the expensive version of this mistake — and the doc usually
needs a correction note once disproved.

## 7. A daily-reset requirement must be satisfiable within one day

A quest that resets every day must be completable with one day's measured income of its input. Sizing a craft
whose cost exceeds daily income makes the requirement **structurally impossible** — the tell is zero completion
rows for every player who performed the action, plus a long-run completion count that implies more days than the
season has.

- Set `cost = one day's measured income` when the owner says "cost = cost kiếm ngày"; then verify the season
  total of the crafted output against any downstream quest that consumes several of them.
- A requirement whose real completion horizon is N days belongs in the season-long bucket, not the daily one —
  but change the bucket only when the owner chooses it; present both options with the numbers.
- **A cost/limit that lives both in a config table and as a hardcoded constant in code will drift.** Change both
  (`UPDATE <table>` AND the constant), or make the code read the table, and grepping for the constant is part of
  acceptance — a DB-only edit silently leaves the old cost enforced.

## 8. Present the choice, then wait

Deliver up to three candidate numbers as a table with what each buys (which milestone, on which day, and what it
costs the player), state your recommendation with its reason in one line, and stop. Do not implement a number the
owner has not picked, and do not re-ask one they already gave — an owner who answers with a bare number is
answering the table you just sent (see SKILL.md §6 on binding bare-number replies).
