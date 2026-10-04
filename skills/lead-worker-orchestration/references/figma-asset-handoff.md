# Figma Asset Handoff in Worker Briefs

When a worker brief requires Figma assets, the Lead pre-pulls them via Figma MCP itself
and hands local paths to the worker — never rely on the worker to call the Figma API.

## Procedure

1. Pull layout first: `get_metadata` on the screen node → record each component's
   `name`, `x/y/width/height`. Hand these rects to the worker in the brief as input
   (saves the worker a discovery round).
2. Export per component node with `download_assets` (one call per component, not one call
   for the whole screen): it returns an `export` render plus `rawImages` (original source
   fills) plus `svgAssets` (icons/vectors). Download promptly with `curl` — URLs are
   short-lived.
3. Note the 20-image cap: `rawImagesTruncated: true` means the subtree holds more than 20
   source images and only the first 20 came back. Drill into smaller sub-nodes and call
   `download_assets` again per node.
4. Record provenance in the asset manifest (which Figma node each file came from) so a
   later audit can tell export from placeholder.

## Standing rules

- Forbid screenshot-cropping as an asset source in the brief, explicitly. A cropped
  screenshot has the wrong resolution and aspect, merges layers that must stay separate
  (e.g. a single mirrored sprite where two distinct pets are needed), and silently
  substitutes placeholder art for production assets.
- A worker reporting "no Figma token/MCP access, so I cropped the screenshot" is a brief
  defect, not an acceptable excuse — the Lead holds MCP access and owns the handoff.
  Fix the brief (pre-pull the assets), do not accept the crop.
- `get_design_context` returns React + Tailwind code. The brief must require converting it
  to the target stack (Pixi/Canvas components, project conventions) — never paste the
  React output into the game.
- Acceptance for any Figma-import task: `ls` the asset dir plus manifest, and `file` the
  PNGs — dimensions must match the metadata rects, not the screenshot size. A `281x284`
  pet where Figma says `395x400` is a crop until proven otherwise.
- Watch for off-canvas nodes in the metadata (e.g. `x=1437` on a 1440-wide canvas):
  require the worker to place them symmetrically inside the canvas and say so in the report.
