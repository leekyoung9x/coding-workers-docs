# Figma Export–Import Verification (Lead–Worker)

Rules for tasks where a worker converts Figma designs to runtime code (PixiJS or
any renderer). The recurring failure is the pipeline silently losing style data,
then the worker inventing substitutes that drift from the design.

## 1. Treat the designer's screenshot as ground truth

When the user shows a screenshot of their own Figma node (e.g. Stroke = Linear,
Outside, Weight 3), that beats every tool output. Never argue tool data against
it — reconcile the tool to the screenshot, not the reverse.

## 2. Never trust a single abbreviated Figma source for style fields

Metadata/design-context endpoints may simplify or drop fills, gradient stops,
strokes, and effects (a linear gradient can come back as one solid color, or
vanish entirely). Before concluding what the design contains, cross-check style
fields through the full REST nodes endpoint for the disputed node and compare
stop-by-stop. A PNG export shows baked pixels, not node fields — do not read
node styles off a flattened export.

## 3. Ban substitute drawing in briefs

Forbid placeholder/fallback/mask/temporary rendering in worker briefs (including
synonyms in the working language). Missing art = render nothing + one `warn` per
key, never a drawn substitute. Substitutes always drift (wrong colors, double
borders, invented gradients) and each one costs a full fix cycle.

## 4. Style numbers come from the tool, never invented

Strokes, gradient stops, weights, and positions must arrive via the export tool
into `nodes.json` and be rendered from there. If the tool lacks a value, the
importer warns and skips — it must not invent stops, widths, or fonts. Fix the
tool, not the symptom.

## 5. Tool must scan the full tree, never prove by one sample node

A brief that asks the tool to prove correctness on one example node guarantees
the next node is still broken. Require full-subtree traversal (batched IDs,
cache-first) with per-node warnings for absent fields, plus a test that adds a
new synthetic node and asserts it is picked up.

## 6. Figma API hygiene (rate limit + token)

No polling and no dense cron against the Figma API — export on demand or per
commit, cache `nodes.json` + PNGs (skip unchanged by hash), batch IDs into one
request, back off with jitter honoring `Retry-After`. Token comes from env only,
is never printed to logs/stdout/files, and never committed.

## 7. Verify + report on every worker completion without being asked

A completion notice is the trigger, not background noise. On each one: read the
worker's log tail, confirm the process ended, re-measure the claimed result
independently (screenshot/pixel/grep — never the worker's word alone), then
report to the user with the visual evidence in the same turn. Never let the user
have to ask 'is it done yet'.
