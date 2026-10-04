# Hardening a Functional Spec Suite

Depth for the question the owner eventually asks: *"we already have tests and a written rule that they must
impersonate the player — why did basic defects still reach players?"*

The answer is never "write more tests". It is: measure the suite mechanically, classify each blind spot, and
prove the new case catches the defect the old suite missed.

## 1. Audit procedure (defect → test → why was it green)

Take the list of defects real players found. For each one, answer three questions in writing:

1. Is there a spec that claims to cover this behaviour? (name the file, and the line)
2. If yes, why did it stay GREEN while the defect was live?
3. If no, which uncovered surface does it belong to?

Emit the result as a **defect-to-testcase mapping table**: defect | covering spec or `NONE` | verdict
(`green-by-blindness`, `green-by-dead-assertion`, `never-run`, `not-covered`). This table is the deliverable;
it is what converts "the tests are bad" into work items.

## 2. The blind spots to measure (in this order)

### 2.1 The gate script decides what actually runs

A suite entrypoint that lists a couple of legacy specs runs **none** of the feature's cases, however many
files exist. This is the cheapest and most commonly missed one — a large number of written, passing cases can be
unreachable.

```bash
# what exists
ls <test_dir> | grep -c '<feature>-'          # spec files present
# what the gate can reach
grep -c '<feature>-' <gate_script>
```

If the second number is zero, the feature has no gate at all regardless of the first number. Adding the specs
to the gate belongs in the same brief as the fix, and the unit-test suite is usually missing from the gate too.

### 2.2 Handler calls measured against gestures

Count, per spec file, the direct handler/RPC invocations versus real user gestures:

```bash
for f in <test_dir>/<feature>-*.spec.ts; do
  printf '%s rpc=%s gesture=%s\n' "$f" \
    "$(grep -c 'callAction\|invoke(' "$f")" \
    "$(grep -cE '\.click\(|\.fill\(|\.type\(|\.tap\(' "$f")"
done
```

A file whose comment/filename claims player impersonation while its gesture count is 0 tests the server, not
the player. Every defect that lives in the presentation layer — control disabled, popup never rendered, list
never refreshed, error text shown to the player — is invisible to it. Require the two counts in the worker's
report so the trend is measurable.

### 2.3 Which tier is asserted, and against which table

The frequent failure: the spec asserts the table the **web** path writes, while the client reads a different,
canonical table. The spec is genuinely green and the player genuinely sees nothing. (Mechanism in
`live-event-data-integrity-audit.md` §6b.) For each reward/quantity assertion, confirm the table asserted is
the table the running client joins, by reading the query path — not by reading the spec's own assumption.

### 2.4 Dead assertions

Read every assertion of the form `expect(x).toBeTruthy()` where `x` is a collector array, a count, or an
object — always true, so the case cannot fail. Replace with an exact check (`toEqual([])`, a length, a numeric
bound) and add a static sweep of the risky call sites so it cannot rot back.

When a project keeps a second copy of the suite (a mirror/staging tree), **diff the assertion bodies across
copies**: a fork can have relaxed a guard while the original stays correct, so which copy the gate runs decides
whether the case protects anything.

**The adjacent rot: a collection assert that only checks membership instead of the full set.** A case that
asserts "the response has at least one row", "contains the field I just added", or "the total is > 0" stays
green while most of the payload is gone — observed on a config merge where 7 of 10 items were dropped and the
suite never blinked, because it checked one item plus one extra column. Rule: for any collection with a known
expected size, assert the **exact set and each element's value** (item code/count per row), never a sample. When
acceptance is "nothing changed", assert row-by-row against a snapshot captured before the change. A related
variant: a case that asserts the CURRENT number of a growing list has to be written as inclusion (`>=`,
"every X in source exists in target") — an absolute equality goes red on unrelated concurrent writes and its
failure then means nothing.

**When a defect escapes to the owner, the spec that missed it is part of the same fix.** Ask *which assertion
should have caught this?* and repair that assertion in the same brief as the code fix — shipping the fix with
the weak spec intact guarantees a silent return. The repaired case must reproduce the owner's exact failure
(real click/gesture through the browser, the same data shape, the same viewport) rather than calling the
handler or debug API directly; a handler-level case passes while the owner still sees nothing.

### 2.5 Seeds that bypass the real producer

A spec that seeds the final resource directly (setting the fragment count, the damage total, the currency)
never exercises the path that produces it, so every defect in that path stays invisible. Seeding a *precondition*
is legitimate; seeding the *outcome under test* is not. Make the new case obtain the resource through the
player-reachable action and assert the downstream value.

### 2.6 Reachability: can a player even find the surface?

A suite can be entirely green on a feature that no player can reach. The spec navigates by URL; the product
has no link to that URL. Both facts are true at once, which is why this survives every other check.

```bash
# the route answers
curl -s -o /dev/null -w '%{http_code}\n' <live_host>/<new-route>
# but does any product surface link to it?
grep -c '<new-route>' <the page/menu that should link it>     # 0 = unreachable in practice
```

For every new player-facing screen, require: (a) a visible entry point on the natural surface (event page, hub,
menu) with the inserted markup quoted in the report, and (b) at least one case whose first step is a **real
click on that entry point** — never a direct navigation. Treat "route returns 200" as proof of routing only, and
say explicitly in the acceptance which of the two you verified: *exists* or *reachable*. The same check applies
to a feature reachable only by typing a URL the owner would have to be told.

## 3. RED proof is part of the deliverable

A new case that only ever ran green proves nothing. Require the worker to force the failing condition —
temporarily remove the fix or withhold the element the assertion needs — capture the failure output, then
restore and capture the pass. Both outputs go in the report. A case whose RED is "could not reproduce" is
not a case.

## 4. Interaction budget

Prefer cases that touch the surface a player touches, in the fewest steps that still measure the value:
seed the precondition, drive the gesture, read the rendered value, cross-check the persisted row. Two
viewports (desktop + a narrow mobile width) when the surface is responsive, because a layout gate can remove the
control on one of them.

## 5. Reporting shape

- The mapping table from §1.
- The two counts from §2.2 before and after.
- The gate script before/after (which specs it now reaches).
- RED output and GREEN output for every new case.
- An explicit list of defects still covered only visually or not at all — never imply full coverage.
- The reachability evidence from §2.6 for each new surface (entry-point markup + a gesture-driven case).
