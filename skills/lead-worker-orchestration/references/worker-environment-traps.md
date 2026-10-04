# Environment traps that produce false evidence

Two environment facts this project hits repeatedly. Both look like product bugs until
measured; brief around them instead of debugging through them.

## 1. The worker CLI has no MCP access and no side tokens

A coding worker spawned via `muse exec` cannot call MCP tools and carries no
Figma token, no Figma REST credential, no browser session. A brief that says
"export assets from Figma" (or any MCP-gated source) will come back with a
degraded substitute reported as done — measured: assets cropped from the Lead's
own screenshot shipped as the "export", with the limitation disclosed only in
the log tail.

Rules:
- Pre-fetch every MCP-gated artefact yourself (screenshot, metadata, asset URLs)
  and name exact local paths — with real pixel sizes from `file` — in the brief.
  Figma asset URLs are short-lived: `curl` them into a scratch dir immediately,
  never paste the URLs into the brief.
- Put in the brief: node rects (x/y/w/h), fonts, every visible text string, and
  the provenance the worker must record (`figma-export` with node id vs
  `screenshot-crop`) so a later audit can tell them apart.
- The same applies to any credential the worker cannot hold: name the local file
  or the exact command that resolves it, never the secret itself.

## 2. A visual suite that regenerates its own baseline certifies nothing

A Playwright visual case that writes a fresh baseline on first run and diffs
against it on later runs passes on a blank canvas: route 200, canvas element
present, zero HUD drawn, suite green. The baseline is a mirror of whatever was
there, including nothing.

Rules:
- Pair every screenshot baseline with a structural assertion in the same case:
  drawn child/sprite count above a floor, a non-background pixel sample at a
  known anchor, or the renderer's own node/draw log non-empty.
- When a visual round comes back green but a real open of the page looks wrong,
  re-run with the structural numbers printed before trusting the baseline — and
  treat a regenerated baseline as suspect until the structural proof lands.
- This is the visual counterpart of the unfalsifiable-guard rule in
  `references/acceptance-verification.md` §1: a gate that cannot go red on the
  broken state is decorative, whatever it asserts.

## 4. Figma export PNGs ship with baked-in text and a matte background — inspect before spriting

An export that looks clean at thumbnail size carries two traps, both measured on battle-HUD assets:

- **Baked-in text.** The export bakes labels and values straight into the pixels (`1.0x` on the
  speed button, `00:18` on the timer frame). Drawing a dynamic Text over it produces double text
  (two `ĐANG LƯỢT` lines offset by pixels, `00:0818`). Rule: before overlaying any dynamic text,
  zoom the export and list which strings are already pixels. Dynamic values go only into regions
  verified empty — or replace the baked value in place (same box, same style), never beside it.
- **Matte background.** Figma fills transparent surroundings with a semi-opaque gray (≈ alpha 26)
  instead of alpha 0. Used raw, every icon wears a visible gray box on dark backgrounds. Rule: check
  corner alpha first (`PIL`, four corners); strip near-gray low-alpha pixels (spread < 15, alpha < 60
  → alpha 0) before committing the asset, and re-verify the corners read 0.

Both look like renderer bugs (bad text layout, broken halo) but are source-asset facts — fix the asset,
not the scene code.

## 5. A simple "export then import" request means a minimal pipeline — no framework

When the owner asks to export a screen and import it, the deliverable is: files out of Figma, files into
the client, one scene reading them at the exported coordinates. Do not build a loader framework, a role
mapping, or a refactor around it — the owner reads scaffolding around a two-step ask as not listening.
Missing assets get named placeholders plus a `MISSING_ASSETS.md` list, never hand-drawn substitutes passed
off as the import.

## 6. A killed brief is re-briefed, never hand-finished by the Lead

After stopping a worker mid-task, the temptation is to finish the last mile by hand ("just copy the
files, just patch the scene"). The hand edit bypasses the brief's own acceptance gates (build, unit,
visual spec with structural asserts), and the owner reads it as the Lead abandoning the orchestrator role —
he said so explicitly. Rules: kill → write a narrower brief carrying the already-fetched artefacts as inputs
(exact paths, sizes, provenance) → dispatch again. The Lead's own tool use stays at pre-fetching gated
artefacts and independent verification, never implementation.

A WebGL canvas captured without a preserved drawing buffer comes back solid black even
with a full scene live (measured: 134 nodes / 68 sprites present, centre-pixel sample
non-zero, zero console errors). Never declare a black screen from the image alone: read
the renderer's own live stats and a pixel sample first, and only then judge.

## 7. Figma style numbers for a brief come from REST with a user PAT, never from MCP output

MCP output is lossy for style data: `get_design_context` flattens gradient fills/strokes
to one solid colour, and `get_metadata` can drop strokes/fills entirely — briefing a worker
with MCP numbers makes it paint the wrong style and the blame goes in circles for rounds.

Rules:
- Fetch the true `type` (e.g. `GRADIENT_LINEAR`), `gradientStops` + handles,
  `strokeWeight`/`strokeAlign`, typography, and effects via
  `GET /v1/files/<key>/nodes?ids=<a,b,c>` with a USER-supplied PAT — the Hermes OAuth
  token is `mcp:connect`-scoped and REST returns 403 with it. Batch ids in one request,
  cache the JSON, never print the token to logs, briefs, or chat.
- A node id that returns `null` is stale (the file was restructured) — re-list the tree
  (`?depth=1`, then page/section nodes) and resolve the node by NAME, never retry the dead id.
- The images API often returns empty for a lone COMPONENT variant child — render the parent
  COMPONENT_SET instead and crop the variants out of the one PNG.

## 8. The dev server is shared and hot — verify it before judging a public URL

Worker build/test cycles kill or collide with the dev-server process (EADDRINUSE crash), so a
502/blank public page right after a round usually means the server is down, not the product broken.

Rules:
- After any worker round, `curl` the local port for 200 before reporting; restart on the same
  port if dead. A Vite crash leaves the port held — a second start dies the same way, so confirm
  the old process is gone first.
- A new public domain needs BOTH the reverse-proxy block AND the dev server's allowed-hosts
  entry — a host-block page names the exact missing entry, so fix that instead of re-checking
  DNS/TLS. A 525 behind a proxy with a self-signed origin cert resolves to proxy-vs-origin TLS,
  not to anything the worker changed.

Rules:
- For a shippable image, gate the preserve flag behind a debug query param (e.g. `?shot=1`
  enabling `preserveDrawingBuffer`), off by default since it costs performance — never on
  in production paths or CI baselines.
- A headless screenshot tool that cannot read WebGL pixels is an instrument limit, not
  product evidence; say so in the report instead of sending another black capture.
- This complements §2 above: the structural sprite-count assert is what distinguishes a
  truly blank scene from a broken capture.
