# Export-then-import briefing (Figma to PixiJS client)

When the deliverable is a Figma screen running in a PixiJS client, the brief is
an export-then-import contract — not a rebuild. Hand-drawn panels that look
close are a scope violation, not progress.

## Brief shape

1. Export per component node via Figma `download_assets` (one call per node id).
   A subtree call returns max 20 raw images — drill into child nodes for the rest.
2. Asset URLs are short-lived: download immediately with curl, never hotlink
   them in code or docs.
3. Import PNGs as Sprites at design coordinates, aspect preserved. Overlay
dynamic Text ONLY where the export has no baked copy of the same string.
4. Ban list in every brief: no `Graphics` fill for panels/boards/buttons/pets,
   no screenshot-crop assets except as marked TEMP with a replacement deadline,
   no invented `slice` numbers (null when the API exposes no insets).
5. Missing assets go into `MISSING_ASSETS.md` with keys — never silently
   substituted, never hidden.

## Asset gotchas (why each rule exists)

- Baked text is the norm (timer `00:18`, speed `1.0x` are pixels): overlaying
  the same string makes double-text. Hide the dynamic label when the value
  matches the baked copy, or pin it exactly over the baked bounds.
- Icon exports carry a near-gray low-alpha fringe (alpha ~26) that reads as a
  dark frame on dark backgrounds: key out near-gray pixels with alpha < 60.
- White-background pet exports need white-to-transparent keying; pale
  translucent wings are solid pale color, not alpha, so a naive cut keeps them.
- Black WebGL screenshots lie by default: without `preserveDrawingBuffer`,
  captures return black while the scene is live (stats show sprites, pixel
  reads show light). Gate screenshots behind a debug flag (e.g. `?shot=1`),
  off by default for perf — verify with a pixel read before debugging render.
- Roadmap claims verify against the npm registry plus GitHub releases, never
  a blog alone: no package plus no mention in recent release notes means
  roadmap, not product. Keep the self-written exporter until the official one
  ships. `@pixi/particle-emitter` peer `<8.0.0` is incompatible with Pixi v8;
  use core `ParticleContainer` plus a self-written emitter.

## Lead boundary after killing a worker

After killing a worker on user order, do NOT pick up its implementation
hands-on (exporting assets, editing scene code) — that repeats the same
boundary violation under time pressure and burns the round. Either revert the
partial state and re-brief a worker, or ask the user: keep as-is and hand over
to a worker, or redo via worker.

## Acceptance

- `grep "new Graphics"` in scene/loader files: only debug/grid remain.
- Screenshot vs Figma shows export art, not flat fills.
- Build plus unit plus Playwright specs pass; only whitelisted dirs change.
