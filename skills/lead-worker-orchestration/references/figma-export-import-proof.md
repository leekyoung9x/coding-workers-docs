# Figma export → client import: dumb path first, picture first

Two rules for any "export this Figma screen and import it into the client" task.

## 1. Prove re-import with the dumb path before building anything smart

Export node → save PNG/JSON into the target client → render sprites at the exported
coordinates. Only after that renders close do you build a semantic loader (role mapping,
NineSlice inference, layout). A framework built before the file→render path works hides
missing assets behind hand-drawn placeholders, and the owner reads that as fabrication.

- Missing assets get NAMED placeholders plus a written missing-asset list — never silent
  code-drawn substitutes that pass visual gates while showing the wrong design.
- Prefer the node's own `export` PNG (the designer's compositing: gradients, glows,
  overlapping text) over reassembling from raw fills when fidelity matters.
- `download_assets` returns three things: (1) `export` render of the whole node,
  (2) `rawImages` source fills (capped at 20 — `rawImagesTruncated: true` means drill
  into sub-nodes per component), (3) `svgAssets` for icons/logos. URLs are short-lived
  (minutes): curl immediately, verify with `file`, record dimensions, never hotlink.

## 2. When the owner asks to SEE the screen, send the picture first

`MEDIA:/path/to.png` (or the platform's native image send) leads; at most 2–3 lines of
verdict after it. A prose description of what the screenshot shows is not a substitute
for the screenshot. Same for comparisons: send the image(s), then the verdict in
measured terms (what matches the Figma reference, what differs, percent-similar only
when both images were actually inspected).
