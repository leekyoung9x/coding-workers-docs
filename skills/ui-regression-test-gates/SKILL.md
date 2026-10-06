---
name: ui-regression-test-gates
description: "Use when proving a UI change with automation tests."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [testing, playwright, regression, ui, verification, canvas]
    related_skills: [lead-worker-orchestration, test-driven-development, dogfood]
---

# UI Regression Test Gates

How to make automation tests that PROVE a runtime/UI change: every fix ships a functional (not
pixel-only) case, every case has measured evidence, and all of them join one required suite with a build
gate and a live gate. Sibling skills carry the domain mapping (Figma→canvas, data wiring); this one
carries the TEST GATES.

## 1. What counts as evidence

- **Assert at the boundary the user sees, never a helper flag.** "Ready", "loaded", "eligible",
  "animation on" are claims; evidence is geometry (px), hashes, timings (ms), request counts, DB rows,
  drawn-image size. A case asserting a boolean on a debug object passes while the screen is visibly wrong.
- **Hash/pixel-sample over time when the claim is motion or change.** Capture the region 8–10 times,
  100–300ms apart, and assert the number of DISTINCT hashes plus a changing index exposed by the code.
  This doubles as the RED evidence before the fix.
- **A screenshot-baseline-only case passes on a blank canvas — pair every visual case with a structural assertion.** A freshly-regenerated baseline of a black/empty screen matches itself perfectly, so the suite stays green while the scene renders nothing (measured: route 200, canvas element present, zero HUD, suite green). Require alongside the baseline at least one content proof: drawn child/sprite count above a floor, a non-background pixel sample at a known anchor, or the renderer's own node/draw log non-empty. When a visual round comes back green but the screen looks wrong on a real open, re-run with the structural numbers printed before trusting the baseline.
- **A BLACK automation screenshot proves nothing about a WebGL canvas — verify pixels before calling it a regression.** Without `preserveDrawingBuffer` the harness capture returns solid black while the scene renders fine (measured: 134 nodes / 68 sprites live, center-pixel `readPixels` sum > 0, zero console errors). When a screenshot is black, confirm via a center-region `readPixels` sum plus the renderer's own node/sprite stats before filing it as a product bug; enable `preserveDrawingBuffer` only on a capture-only build, never as a perf fix.
- **Cross-check data claims against the system of record.** For each row the UI renders, compare to a real
  query and log `key | need | have | met`; "the panel has rows" proves nothing.
- **A case that clicks must assert the RENDERED outcome**, not a state variable. For DOM use `elementFromPoint`/locator visibility; Unity exposes only the canvas there. For Unity use a read-only runtime control map plus EventSystem/GraphicRaycaster hit evidence, dispatch a real Playwright mouse action and verify modal-specific pixels AND structural state AND the API/WS outcome. Direct handler calls are diagnostic, not E2E.
- **Click EVERY interactive control, not only the ones the change touched.** A mirror of state
  (`panelOpen: true`, `slots: 10`) stays green while a control INSIDE the panel is dead, because no case
  asserts a reaction to that control's own click — measured: the panel's primary action produced no request,
  no message and no error, and the entire suite passed because every case stopped at "the panel opened".
  Enumerate the controls from the debug object's own anchor/box map, click each at its design-space centre,
  and require an observable reaction: a request to the action's own endpoint **or** a non-empty toast. On the
  refused path (the control must not act) assert the complement — a message naming the reason, no request,
  panel still open, selected entity unchanged. A user reporting "the button does nothing" is pointing at this
  gap, so treat every control lacking such a case as an untested claim, not as a passing feature.
- **Make the measured surface observable before writing the case — an unexposed value is an untestable
  claim.** A canvas app whose debug object exposed only loader stats (`ready`, `imageCount`, `stats`) left
  the whole popup unmeasurable: the spec could open it and prove nothing about its contents. Probe first
  (open the surface, read the debug object, confirm the field you intend to assert is actually there), and
  if it is missing, the EXPOSING step is part of the fix — request it in the brief with the exact shape
  (`{items: [{code, name, need, have}], conditions, after}`) and assert on that. Prefer exposing a small
  read-only mirror of what is drawn over screenshot diffs of the same region: a mirror is stable, fast, and
  gives the RED output a reason, while pixels need a baseline you would have to re-take after every copy
  change.
- **Prove a count-\/limit claim against the FIXTURE's own rows, not against the picture.** "The popup lists
  N items" is an assertion about data plus a slot count; read both (`N` from the payload, `M` from the
  layout's slot/id list) and fail when `N > M` — a layout with fewer slots than the requirement silently
  drops the remainder, and the screenshot still looks complete.

## 2. Console / pageerror gate

- **Capture every channel:** `page.on('pageerror')`, `console` of type `error` (plus `warning` containing
  "Uncaught"), and unhandled promise rejections.
- **Assert an EXACT empty list (`toEqual([])`).** A guard written as `expect(errs).toBeTruthy()` never
  fails — an array is always truthy, so the gate is decorative. Audit any existing "no console errors"
  case for this mistake before trusting it.
- **Cover every FLOW, not just the load** — a narrow guard misses exactly the bugs the user finds in F12:
  each URL mode, every tab, every popup (open and close), every option of every menu, the primary action
  in BOTH its success and failure states, entity switching, fullscreen enter/exit, a portrait viewport,
  and a fault-injection pass that nulls fields in the API response to reproduce the production crash.
  Log the flow name with each captured error so a failure names the flow, not just a message.
- **Null-typed input is the usual console killer** — reproduce it deterministically by intercepting the
  state endpoint and nulling the fields.

## 3. Static source scans as a gate

- Add a case that reads the feature's source files and FAILS if a banned pattern reappears; it catches the
  bug class in places the runtime cases never exercise.
- **The recurring one is a nullable value reaching a formatter.** Every `.toLocaleString()` and every
  arithmetic use of a possibly-null field must sit behind a guard (`Number(x ?? 0)`, `?? 0`, `?.`). Assert
  `N files scanned, M call sites, 0 unguarded`. Fix it at the SHARED build/format layer all consumers pass
  through — not with `try/catch` (hides the bug) and not with a silent `?.` that drops the value from the
  display.
- Keep the file list explicit and log `file (count)` so the report shows coverage, not a bare PASS.

## 4. RED before GREEN, always

- Run the new case against the UNCHANGED code first and paste the real failing output. No RED output means
  nothing was proven.
- **RED only counts if the case RAN.** A spec whose transport dies mid-run reports RED while proving nothing
  (`TypeError: fetch failed` / a `502` from a backend that is unreachable on the dev box), and that fake RED
  ships as "the failure existed", gets quoted in a report, and hides the fact that the case never executed.
  Stamp every RED with HOW the case got its data — live server, stubbed transport on a fixture you control, or
  skipped — and state that explicitly in the brief, so a crashed case can never be filed as RED. A stub is
  legitimate ONLY if it replays the fixture's real shape (read the columns from the DB, not invented field
  names); a stub that guesses the shape proves the guess, not the product.
- **"All cases red" with the loader flag green means the environment, not the product.** A canvas that renders
  (`ready: true`, node count reported) while every case times out is a data-transport failure: read the app's OWN
  status field first — `__POC__.dataMsg` said `lỗi dữ liệu: getaddrinfo ENOTFOUND mysql` with `petCount: 0` and the
  state endpoint returning 500. Probe BOTH environments side by side and print the flags before touching the code:
  the working one reports `"dữ liệu thật · N pet"` and a 200 with a real entity count. When they differ only in the
  flag, fix the environment and re-run — do not go hunting for a product regression, and never "fix" it by relaxing
  the timeout or adding a skip. Seed/verify on the ACCEPTANCE environment (the container the gate actually uses, on
  its declared port) rather than an ad-hoc dev server: a server started by hand on another port runs OUTSIDE the
  compose network, so a compose-internal DB hostname inside `.env` does not resolve and every case reds for a reason
  that has nothing to do with the change. And a verify that ends with a dev server left listening on its port is not
  finished — stop it in the same pass so the next run cannot silently attach to the stale one.
- When the code is already fixed, reproduce RED by temporarily reverting the behaviour (revert the flag /
  stash the change), keep a backup of the modified files, and confirm the checksum is restored after.
- **Also prove the case can fail for the RIGHT reason.** A case that stays green on the broken build is
  testing the wrong thing — fix the CASE first, then the product. A case that cannot fail is worse than no
  case: it certifies the bug.
- **Prove each case is actually IN the gate.** A spec file sitting in `e2e/` proves nothing while the runner's
  list never names it; that is how a whole bug class ships with "all tests green". When a fix adds a case,
  add its path to the required-suite script in the same pass — and when auditing, diff the runner's list
  against the spec files on disk, reporting the ones the gate never runs.
- **A formatter/loader change can make an OLD case fail, and the verifier may misread it as a stale fixture.**
  When a tolerance/normalization rule is tightened, previously-passing cases about the same surface lose their
  slack. Re-derive each expectation from the CURRENT rule before editing the number — "expected 10, got 15" is
  the case doing its job, not a flaky fixture.

## 4b. Prove WHICH source tree the running artifact was built from

A repo can hold two copies of the same app (`app/` at the root and `src/app/`, plus `lib/` and `src/lib/`) with
the framework silently preferring one. Every case then measures a tree nobody edits, and the fix "does not work"
while the file you patched looks correct. Symptoms: brand-new markers absent from the bundle, older features
present instead, and every case red for a state reason.

- **Grep the SERVED bundle for a marker unique to each tree**, never trust the source layout:
  `docker exec <ct> grep -rl '<marker>' /app/.next/server /app/.next/static`. Pick markers that exist in exactly
  one tree (a feature only the new tree has, and one only the old tree has) — the pair tells you which tree won.
- **Brief a disputed tree as one question with two candidate answers, never as an asserted conclusion.** State the two candidate winners plus the commands that decide between them; the worker correcting your hypothesis on the first run is the expected outcome, not a failure. Record which evidence would overturn the current verdict alongside the verdict itself.
- Confirm with per-tree file counts, and compare each tree to the reference environment (the production host):
  when prod has `src/` only and the test box has both, the test box is the divergence, not the feature.
- **Merge before deleting.** Two parallel trees usually each hold features the other lacks (`root` had the toast,
  animated icon and eligibility checks; `src` had the new cost line and the debug mirror). A merge that picks a
  tree by file size or mtime silently drops a feature. Build a per-file decision table (only-root → move,
  only-src → keep, both → merge by FEATURE with a marker table proving every marker survived) and paste it in
  the report.
- **Then add the structural case:** assert the redundant tree does NOT exist (and the canonical one does). A
  repo-shape guard is a real case: prove it red by recreating one directory, then green after removing it.
- Before deleting a tree, grep for relative imports pointing at it; an unresolved reference means STOP, not delete.

## 5. Anti-flake without weakening assertions

- **Replace fixed sample windows with poll-until-condition under a deadline** (up to 5–8s): keep asserting
  the same measured quantity (≥2 distinct hashes, index changed) and still FAIL when the deadline expires.
  Never widen a threshold, raise a timeout toward infinity, or downgrade to a boolean.
- **Distinguish flake from regression by re-running the case ALONE.** Red in a batch and green alone is
  contention; red alone is the product. Report both numbers.
- **Concurrent writers on a shared fixture cause false reds.** Two suites seeding the same account or table
  in parallel drift a count mid-run. Before blaming the change, look for another running worker or process
  writing the same rows, and state the count and the writer you found.
- **Run the whole feature set in one invocation after touching a shared layer**, not one spec at a time.

## 6. Fixtures that survive drift

- **Exact-equality against a production-side count is inherently flaky** when other specs seed extra rows
  for the same entity. Rewrite as **containment per key**: every key present on the reference side must
  exist on the test side with `count >= reference`, plus a floor assertion (e.g. `> 1`). Keep the strength
  that catches the real bug — prove it by deleting one genuine row, pasting the RED, then restoring.
- **Verify the JOIN/visibility path before trusting a fixture.** A row seeded without its definition row in
  the parent table is filtered out by an inner join, so the endpoint returns fewer rows than the table
  holds. Assert against what the endpoint returns, and note the trap when logging.
- **A case needing a precondition must select a qualifying fixture.** The default-selected entity usually
  does not qualify, and leaving the case pointed at it produces a permanent red that reads as a product
  regression. Keep the blocked path as its OWN case (message shown + no panel + no asset requests).
- **Drive selection through the suite's OWN helper — never hand-roll scrolling in an ad-hoc probe.** A
  throwaway probe that walks a virtualised list reports `not-in-view` / "the entity is missing" for an entity
  the specs select fine, and each fruitless iteration looks like a data or fixture problem. Measured: three
  probe rewrites returned nothing while the spec already had a poll-until-selected helper working in ~2s. When
  the thing you want to measure is behind a selector, put the measurement INSIDE the spec that already selects
  (or import that helper) and run the spec — its output is the evidence, and it doubles as the acceptance run.

## 7. The required suite

Keep ONE script as the acceptance gate, re-runnable end to end:

1. **Gate 1 — build**: require exit 0, allowing only the pre-existing baseline errors (name them).
2. **Gate 2 — live**: rebuild, require `healthy` AND the route returning 200 before any test runs.
3. **Functional group**: one spec per fixed bug/feature, each case's comment stating the bug it locks down.
4. **Regression group**: the pre-existing specs, including data-integrity guards.
5. **Fail closed on missing or skipped REQUIRED cases.** A development run may continue to collect other failures and print `[SKIP] missing: <path>`, but it must end non-zero/not accepted; missing work cannot certify a release. Print `ran / pass / fail / skip`, require `ran == required_count` and zero required skips.
6. Print one final verdict line and write a timestamped log.

The owner of the script adds every new spec (one owner avoids two writers racing over it); an
implementing worker is told to report the spec name instead of editing the script.

## 8. Reporting the result

- Report per case `TC | what it locks down | measured numbers | RED → GREEN`, then the aggregate
  (`N passed`, elapsed) and the live gate (container healthy, route 200).
- **Never report a worker's self-report as the result** — re-run the suite and re-measure. Claimed and
  measured numbers diverge; when they do, the measured one is the truth and the divergence goes in the
  report.
- **A green test runner or oracle does not override a visible layout defect.** If the user spots a visual flaw ("hở bên dưới", "bị che nút", "méo/cắt viền"), never argue test status or offer speculative choices. A passing bounding-box or hash check is blind to aesthetic/composition flaws (such as background map leaking under a modal or a floating bottom button). Re-examine the live capture with vision, locate the coordinate or hierarchy cause, apply the layout fix, rebuild, capture a fresh screenshot, and present the image as the deliverable.
- **When a worker says "this case was already red, not my doing", verify BOTH halves:** run that spec alone
  (was it red before?) AND recreate the state it blames (is that really the cause?). It can be right that
  the case was pre-red while wrong about why.
- "Outside my whitelist so I did not fix it" is not acceptable for a spec that is part of the required
  suite and permanently red — fixing its fixture is work to dispatch.

## 9. A layout with N slots cannot render N+1 items — make the shortfall a case

A design frame is a fixed inventory: `Item_Material_01..08` is eight boxes. When the data source grows past the
frame, the extra rows are dropped with no error and no visible clue — the screen simply shows fewer items than
the requirement holds, which reads as "the fix did not work" rather than "the frame ran out of room".

- Before writing the display case, count both sides: slots in the design data (group by parent, per row) and
  entries in the payload. `entries > slots` is the bug, and the case asserts equality with both numbers in the
  failure message.
- Grow the frame **from the design tool**, not from taste: open the source design node, count the boxes it
there, and copy its arrangement. Only when the design genuinely has fewer boxes than the data choose among the
  options (shrink the boxes, wrap into rows, paginate) and state the choice plus the geometry that rules out the
  alternatives — a neighbour panel or the primary action button that the new rows would overlap.
- Items that are **costs** rather than stocked goods have no icon or "have" count to draw. Do not invent one:
  either render a neutral placeholder plus the name from the item table and label it as a cost, or add one text
  line naming the costs. Both are content decisions — put the choice to the owner rather than let a worker pick.
- **Expose the slot map, not just the items.** `{slots: [{slotId, code, text}]}` lets the case prove WHICH box
  holds WHICH item and that no box is reused; an items-only list passes while two boxes show the same thing.

## Support files

- `references/unity-webgl-test-strategy.md` — layered Unity automation, read-only bridge and real click/visual/API proof.
- `references/canvas-animated-assets.md` — animated GIF (CDN) on a canvas: decode, animate, cache,
  fallback, and the measured evidence for each.
- `references/console-guard-flows.md` — the flow checklist for the console gate and the null-guard
  fix pattern.
