# Shipping and verifying a production DATA migration

For merges, backfills, and "two stores hold the same asset" repairs on a live database. The failure these
rules prevent: a migration that reports success, passes a green suite, and has silently removed rows from real
users' inventories.

## Pre-flight (before any write)

- **Freeze a baseline first.** Tag the commit/branch you will deploy from (`baseline-<change>`) and record every
  container's start time. Without a frozen baseline there is nothing to diff against, and the next edit — yours
  or a parallel worker's — destroys the evidence needed to prove equivalence.
- **Map blast radius with a tool, not by eye.** Grep every READ *and* WRITE site of the affected table/column
  across all consumers (web, API, admin, other services) and print `file:line | READ|WRITE | service`. One table
  is routinely touched in a dozen places by several services; a hand-written map misses the one writer that
  matters.
- **Identify the canonical store per consumer** before choosing a merge direction. Two tables holding the same
  logical asset is the normal cause of "this screen shows 5, that one shows 0". Which store each service
  *reads* is a separate question from which it *writes* — confirm both.
- **Stage the intent before applying it.** Write `(key, current value, target value, delta, reason)` rows into a
  staging table. That table is your audit trail, idempotency guard, and rollback source at once.
- **State the test tier explicitly, more than once.** A brief that says "run the migration" without a carve-out
  gets executed against production. Say "test database only, target host `<test host>`" in the vendor-constraint
  section *and* in the acceptance checklist.

## Invariants — the only thing that makes a test a test

- **Assert the invariant as a hard, single-command check that exits non-zero.** For a merge this is
  `new_store >= old_store` **per key**, with violations printed as key + shortfall.
- **"Old != new" and "diff within range" are not assertions** — they pass straight through data loss. Every
  deviation must carry a specific number, never "within expected scope".
- **Assert per key, never by total.** A total-sum check hides offsetting damage: the sum is unchanged while one
  user is down 192 and another is up 192.
- **Assert the test actually ran.** Zero collected cases must FAIL. A harness can print `1 passed` while every
  query silently returned nothing.
- **Assert per-key results differ.** If a column that varies between keys reports the identical value for every
  key, the query is missing its key predicate. Encode that as an assert — the cheapest false-green detector
  there is.
- **Prove the gate can fail on a real past failure.** Build a fixture reproducing the known-bad state, assert the
  gate FAILS naming the right key and shortfall, correct the fixture, assert it PASSES. A gate never observed
  failing is unverified. Never widen or narrow an invariant to make a run go green.
- **For merges that must not reduce balances, require positive deltas only** and assert `MIN(delta) >= 0`.
  A merge that "resets" a store to a snapshot removes whatever it legitimately held on top.

## Equivalence testing, old build vs new

- **Query-vs-query diff on the same post-migration database is near worthless** — both sides read the already
  corrupted data. Capture golden output from the OLD build/state *before* the change, from the canonical store,
  into JSON + sha256.
- Compare **contract shape** (field names, types, nullability) as well as numbers; a renamed field breaks clients
  even when the values are right.
- Where a value is expected to change by design, require the change to equal a computed, named delta — not an
  allowed band.
- A gate that reads **live production** may be impossible to satisfy before deploy: the old code keeps writing
  the legacy store while you migrate, so "new >= old" fails until new code is live. Do **not** block the deploy
  on it. Sequence: final sync → deploy → re-run gate → confirm drift reaches zero. When the user has already
  approved the deploy, never invent a process gate that blocks it.

## Rollback

- Generate **id-scoped guarded** SQL from the staging table (one statement per key) — never a blanket restore of
  a whole table.
- **Drill it end to end** on the test tier: apply → rollback → verify every value returns exactly → re-apply.
- Keep a full dump, a per-table dump of the tables in scope, a source tarball, and `:pre-<change>` image tags
  for every service you will rebuild. A merge that only adds needs no data rollback, but the code deploy still does.

## Deploy order and verification

- **Verify which services actually contain the changed code** (`docker inspect` the image + grep the string
  inside the image) rather than trusting a remembered list — code may live in a shared library, which changes how
  many services need rebuilding and in what order.
- **One service at a time.** After each: start time changed, status `running`, logs free of exceptions, key route
  200. If smoke is red, roll that service back immediately with its `:pre-<change>` tag, then stop and report —
  never continue down the list.
- Never deploy from an uncommitted tree, and never commit unrelated dirty files to make a deploy possible;
  commit only the files that belong to the change.

## Reporting

- **Every number carries its source** (query output, `file:line`, command + exit code). A figure not measured this
  turn is not reportable, and a keyword grep is not a measurement.
- Log a journal row per migration: table/column, rows and keys affected, backup path + sha256, rollback file, how
  it was verified, which services were deployed.
- Keep staging and backup tables until the change survives a full cycle; list which to keep, archive, or drop.
