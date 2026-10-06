# Console / pageerror gate — flow checklist and the null-guard fix pattern

A "no console errors" case is only worth having if it (a) asserts an exact empty list and (b) walks every
flow. Below is the checklist that caught a production `TypeError` a narrow guard had been missing.

## Why the old gate was decorative

```ts
expect(errs).toBeTruthy();   // an array is ALWAYS truthy — never fails
```

Rewrite as `expect(errs, message).toEqual([])` and log each captured entry with the flow that produced it.

## Flows to walk (each labelled in the log)

1. Load in every URL mode: plain, static/measurement mode, and real-data mode.
2. Open every tab in the tab bar.
3. Open the primary action panel in BOTH states: insufficient-resource (assert no write) and sufficient.
4. Open/close every popup, including one popup per option (e.g. all sort keys).
5. Switch entity twice (A→B→A) and scroll the list.
6. Enter and exit fullscreen; repeat on a portrait viewport so the rotate branch runs.
7. FAULT INJECTION: intercept the state endpoint and null the numeric fields, then trigger a redraw.

Measured outcome of the fault-injection flow: 4 pageerrors, all the same production message, before the
fix; 0 in all 12 flows after.

## The null-guard fix pattern

Symptom: `Uncaught (in promise) TypeError: Cannot read properties of null (reading 'toLocaleString')`.

Cause: a field that can legitimately be null (an optional cost/stat row) flowing into a formatter.

Fix at the SHARED build/format layer that every consumer passes through:

```ts
const gold = Number(src.goldNeed ?? 0);      // then format gold
const hp   = Number(src.hp ?? 0);
```

Bans that belong in the brief:

- no `try/catch` around the formatter (hides the class of bug),
- no silent `?.` that makes the value vanish from the display,
- no default chosen per call site — one place, one rule.

Then add the static scan case (see SKILL.md §3) so the pattern cannot come back in a file the runtime
flows never touch. Measured: 13 call sites, 10 files, 4 unguarded before the fix, 0 after.
