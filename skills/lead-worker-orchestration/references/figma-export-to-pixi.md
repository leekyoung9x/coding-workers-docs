# Figma → PixiJS Asset Export (no hand-drawn substitutes)

When the job is bringing a Figma screen into a PixiJS client, it is literally
*export then import*: pull PNGs + geometry out of Figma, drop them into the client
as Sprites at design coordinates. It is not authorization to build a loader
framework, a role-mapping system, or any new abstraction — brief exactly the
export→import job.

## 1. Export per component node, not per screen

Call `get_metadata` on the screen to learn the tree, then `download_assets` on
each component node (panel, pet art, timer, buttons, tabs). A screen-level call
returns one flattened render plus a capped list and hides the per-part geometry
the client needs.

## 2. Download asset URLs immediately; never hotlink them

Every URL from `download_assets` / `get_design_context` is short-lived (days) —
`curl -L -o` them into `public/assets/<screen>/` in the same pass that requested
them, then `ls -la` + `file` to confirm real PNG bytes (a 40–60 byte body is an
error page, not an image).

## 3. `download_assets` caps `rawImages` at 20 per call

A `rawImagesTruncated: true` response means assets were dropped — drill into
smaller sub-nodes and call again per node instead of accepting the partial set.

## 4. Render exports as Sprites; never recreate Figma art with Graphics fills

A flat fill next to real gradients/glows reads as placeholder and gets rejected.
Static text stays baked in the image; only text that changes at runtime becomes
Pixi Text overlaid on top. A missing asset gets a visibly labeled placeholder
plus an entry in a `MISSING_ASSETS.md` list — never a hand-drawn substitute
presented as done. Put this ban in the brief verbatim: workers take the cheapest
route to a green screenshot, and a hand-drawn panel next to exported art is the
cheapest route.

## 5. Register every new PNG in the asset bundle map

Alias → file path, loaded through the AssetManager, unloaded on scene exit. A
file sitting in `public/` that no bundle references is not imported.

## 6. Verify WebGL rendering by reading pixels, never by screenshot alone

Headless `capture_screenshot` returns a black image for a WebGL canvas unless
`preserveDrawingBuffer` is on — a black screenshot proves nothing about the
scene. Gate the flag behind a debug query param (e.g. `?shot=1`) so production
keeps it off, expose a read-only scene-stats hook (node/sprite/text counts) for
specs, and assert a minimum sprite count in the route spec so a black screen can
never pass green.
