# Proving which duplicated source tree is LIVE

A repo can hold `app/` + `lib/` **and** `src/app/` + `src/lib/` at once (two hand-synced copies, synced by
commit messages like "dong bo 2 cay test"). Two grep-based verdicts are both unreliable:

- **A marker ABSENT from the bundle proves nothing** when it is a module-local variable (`const drawnRectLog`,
  `function instanceOffset`, `const fixedBox`): the minifier renames those, so absence is expected. Only
  *exported* names or object keys survive (an `__POC__` hook key like `drawnRects` does survive).
- **A marker PRESENT in the bundle attributes nothing** by itself: it may live in the *page* tree while the
  *library* tree is the other copy.

## Decisive evidence — two commands

```bash
# (a) Next's own generated entry names the compiled app tree
grep -n 'entry from' .next/types/app/<route>/page.ts
#    → import * as entry from '../../../../../../app/<route>/page.js'   ⇒ app tree = root app/

# (b) a file reachable ONLY through the path alias pins the library tree
ls lib/<x>.ts src/lib/<x>.ts          # only src/lib exists
grep -n '@/lib/<x>' app/<route>/page.tsx
#    → alias resolves to src/lib; pointing at root lib/ would break the build
```

Observed result shape: **page tree = root `app/`, library tree = `src/lib/`** (tsconfig `"@/*": ["./src/*"]`),
with `src/app/` (170 files) and root `lib/` (47 files) outside the bundle. Inside the container, the live
bundle then carries page-root markers *and* src-lib markers at the same time — which is exactly what makes a
single-marker conclusion wrong.

## Corollaries

- Brief this as **one question with two candidate answers**, never as an asserted conclusion. The worker
  correcting the Lead's tree hypothesis on the first run is the expected outcome, not a failure.
- **Dead code test**: a directory whose name string appears in **no** `.ts/.tsx` of the live trees cannot be
  reached even by dynamic `import()` (the path string must exist in source). `grep -rn '<dirname>' app lib src
  --include='*.ts*'` → empty ⇒ dead; re-run at deletion time. (Here: `src/app/game/**/engines/` 6 files,
  0 imports, 0 markers in the build.)
- **Count the copies instead of assuming newer/older**: two `canvas-renderer.ts` copies here are two
  different *mechanisms* (root = copies a pre-rendered Figma reference image for static text; src = exposes a
  `drawnRects` render-state hook for tests), so "keep the newer one" would delete a capability.

## 3. Two backends, one database — audit table WRITE ownership before proposing any migration

When an owner asks "why do we even have X?" about a layer (a web framework, a service, a proxy), answer from a
**write-ownership census**, not from the cost of removing it. "Expensive to replace" is not a reason a component
exists, and presenting it as one reads as defending the incumbent.

```bash
# per table: how many files in EACH tree touch it
for t in <table_a> <table_b> <table_c>; do
  printf '%-24s backendA=%s backendB=%s\n' "$t" \
    "$(grep -rl "$t" <treeA> --include=*.cs | wc -l)" \
    "$(grep -rl "$t" <treeB>/app/api --include=*.ts | wc -l)"
done
```

Findings that matter, in order of severity:

1. **Tables with two owners** (`>0` in both trees) are the money-bug surface: two write paths, no shared
   transaction, no DB constraint — e.g. an event wallet/ledger written by a .NET econ service *and* by web API
   routes. This is the real answer to "why do we have both?", and it is a defect, not a design choice.
2. **Tables whose owner already exists on the other side**: before repeating the owner's fear ("do we have to
   rewrite all the game queries?"), grep the survivor for services/queries by name — a wallet service, a shop
   service, a progression repository. If they exist, the fix is deleting a duplicated query path, not writing
   one, and saying so is what makes the decision cheap instead of terrifying.
3. **Tables owned uniquely by the layer under question** are the only part that is genuinely its own — what the
   layer should keep, usually small (here: payment orders, notifications, cosmetics, web session rows).

Check the survivor's capabilities with the package index before listing them as blockers —
`https://api.nuget.org/v3-flatcontainer/<pkg>/index.json`, `registry.npmjs.org/<pkg>` — plus a grep of the
target tree for auth/session, payment SDK with webhook signature verification, and mail/SMS/captcha helpers.
They are usually three small adapters, not a rewrite: state that in numbers so the owner is not choosing
between a vague "big migration" and a concrete "keep it".

Gate the single-writer rule mechanically: a spec that greps the losing tree's API files for the other side's
table names and fails on any hit. A written ownership table alone changes nothing.

For authoring the current-state-first document that follows from this audit, see
`references/review-brief-and-current-state-docs.md`.
