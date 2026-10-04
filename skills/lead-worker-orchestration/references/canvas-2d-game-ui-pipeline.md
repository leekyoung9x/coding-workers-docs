# Canvas 2D Game UI Pipeline (Figma to Canvas)

Guidelines and rules for rendering mobile/web game user interfaces in HTML5 Canvas 2D from Figma design specifications.

---

## 1. Separation of Vector Shapes vs Raster Images

A common failure mode in Figma-to-Canvas export pipelines is mistaking rich raster game assets for procedural shapes (or vice versa):
1. **Exporter Bug (Solid Placeholder Squares)**: When an export plugin outputs 1-color solid placeholder PNGs (e.g., single-color rectangles for buttons and nameplates), the root cause is typically in the exporter plugin (such as calling `node.exportAsync` on raw leaf primitives inside hidden groups or missing instance assets), NOT an instruction to replace game art with procedural code shapes.
2. **Game Art Identity**: Stylized RPG UI buttons (`Btn_Evolution_Primary`), nameplates (`Bg_Name`), and headers are often high-resolution textures (1.5MB+ PNGs with bevels, metal textures, and inner glows) crafted by artists. Do NOT hand-code them as plain `roundRect` + `ctx.fill()` unless verified that Figma itself defines them as pure vector solids. Always verify with Figma MCP (`get_design_context` asset URLs) before altering rendering strategy.

### Categorization Rules

| Component Type | Rendering Strategy | Key Attributes |
| :--- | :--- | :--- |
| **Vector Shapes (Khối hình học)** | **Native Canvas Path**<br>`roundRectPath()` + `fill()` + `stroke()` | `cornerRadii: [tl, tr, br, bl]`<br>`fills: [{ type: "SOLID", color }]`<br>`strokes`, `strokeWeight` |
| **Raster Assets (Ảnh đồ họa)** | **Image Blit**<br>`ctx.drawImage()` with aspect ratio containment | `imagePath` / `imageById`<br>Real PNG source with diverse colors |

### A. Vector Shapes with Corner Radii (Khối bo góc thật sự)
- **Targets**: True procedural layout shapes: progress bar tracks (`Bg_Track`), progress fills (`Img_Fill`), simple dividers (`Divider_Line`), and untextured solid background overlays (`Bg_Overlay`).
- **Implementation**:
  - Only apply when Figma actually defines the element as a solid/gradient vector primitive without artist texture slices.
  - Export `cornerRadii` from Figma (e.g. `[10, 10, 10, 10]` for pill-shaped progress bars).
  - Use `ctx.roundRect(x, y, w, h, [tl, tr, br, bl])` with fallback to native arc/bezier routines.
  - Apply `SOLID` color fills and strokes with appropriate opacity.
  - ⚠️ **Critical Trap**: Buttons (`Btn_*`), Nameplates (`Bg_Name`), Level badges (`Bg_Level`), and Header banners (`Bg_Header`) in game UIs are almost always **Raster Assets (Section B)** textured by artists, even if they have rounded corners. NEVER unilaterally set `imageRef = null` on buttons or nameplates to force procedural code rendering — that turns rich textured game art into flat, crude placeholder slabs ("toàn tự vẽ"). Always inspect the raw export `.zip` or Figma MCP before altering their asset classification.

### B. Raster Images (Ảnh sprite & icon phức tạp)
- **Targets**: Character/pet sprites, monster portraits, particle/aura effects (`Img_Aura`), item icons (gems, evolution materials, currency), and ornate decorative frames (`Bg_Main` ornate borders).
- **Implementation**:
  - Maintain true 1:1 image assets or contain within the bounding box:
    ```typescript
    const scale = Math.min(node.width / naturalWidth, node.height / naturalHeight);
    const dw = naturalWidth * scale;
    const dh = naturalHeight * scale;
    const dx = node.absX + (node.width - dw) / 2;
    const dy = node.absY + (node.height - dh) / 2;
    ctx.drawImage(img, dx, dy, dw, dh);
    ```
  - Bind dynamic assets by entity ID (e.g. `currentPet.iconUrl`) via `imageById` mapping rather than hardcoding static mock identifiers.

---

## 2. High-DPI & Retina Display Handling (DPR 2+)

1. **Offscreen Buffer Sizing**:
   - An offscreen canvas must match the backing display resolution:
     `offscreen.width = designWidth * dpr`, `offscreen.height = designHeight * dpr`.
   - Never draw to a 1x design canvas and let CSS or browser interpolation upscale it to 2x; doing so blurs text and glyph contours.
2. **Final Blit Smoothing**:
   - Set `targetCtx.imageSmoothingEnabled = false` when transferring 1:1 between matching scale buffers to avoid anti-aliasing blur on crisp pixel boundaries.

---

## 3. Text Stroke & Glyph Counter Integrity

- **Figma vs Canvas Stroke Alignment**:
  - Figma `strokeAlign = OUTSIDE` expands stroke strictly outward.
  - Canvas `ctx.strokeText()` centers the stroke on glyph vector outlines. A heavy `lineWidth` will bleed into inner loops ("counters") of letters like `a`, `o`, `e`, making text illegible.
- **Rules**:
  - Scale text stroke width strictly in proportion to font size (e.g. `lineWidth = fontSize * factor`, typically factor ~0.08–0.12), keyed by font size in ONE named layout table (e.g. `whiteStrokeScaleByFontSize`) instead of scattered literals. Emulating Figma `strokeAlign = OUTSIDE` on a centered Canvas stroke needs `lineWidth ≈ 2 × strokeWeight` (factor ~2.0–2.2), never `lineWidth == strokeWeight`.
  - **Translating a "+N border" request into `lineWidth`**: the Canvas stroke is centered on the glyph outline, so the visible outline only grows by `lineWidth / 2`. Thickening every text border by N design px therefore means `lineWidth += 2N`. Apply it through one named constant (e.g. `strokeWidthBonusPx`) in the shared text-drawing path so the white-fill branch, the normal-fill branch, and any mirrored renderer copies stay in sync, and expose the per-node effective `lineWidth` plus outward px so a test asserts the delta numerically instead of someone eyeballing a screenshot. A later request to change the amount ("+1 now, not +2") **replaces** that constant measured against the ORIGINAL baseline — `bonus = 2 × N`, never `current + N`. Write the target as "outward = baseline + 1" in the brief, have the worker recompute from the baseline, and update the test's expected numbers to the recomputed values: neither leave the assertion at the previous amount nor relax it to whatever the code now emits.
  - **Mirrored module copies**: this codebase keeps duplicate renderer files (e.g. `src/lib/canvas-renderer.ts` and `lib/canvas-renderer.ts`). Detect them in the whitelist step with `diff src/lib/<m>.ts lib/<m>.ts`; a worker patching only one copy leaves the served bundle unchanged and the fix appears to do nothing.
  - Use 2x supersampling for text rendering passes when dark outlines are required around white glyphs, then downsample cleanly.

---

## 4. Quantitative Acceptance Testing

Never rely solely on structural node tests (e.g. `drawnIds.includes(...)` or DOM presence); a canvas can pass structural assertions while displaying empty black or solid red boxes.

### Mandatory Test Measurements
1. **Delta on Modal Transition**:
   - Measure pixel delta at the center of the modal when transitioning between open and closed:
     `diff(A, B) = |Ar - Br| + |Ag - Bg| + |Ab - Bb| >= 60`.
2. **Color Palette Diversity (Anti-Placeholder Gate)**:
   - Sample rendered pixels across the component region into a color set:
     ```typescript
     const colors = new Set<string>();
     for (let i = 0; i < imgData.length; i += 4) {
       colors.add(`${imgData[i]},${imgData[i+1]},${imgData[i+2]}`);
     }
     expect(colors.size).toBeGreaterThan(10000); // Proves real texture/sprite presence
     ```
   - Placeholder 1-color squares yield `< 10` unique colors, catching export defects automatically.

### Render-State Test Hooks (prerequisite for functional specs)

A canvas UI has no DOM, so a functional assertion has nothing to read. Before behaviour tests can be written, require the worker to publish a test hook on `window` (e.g. `window.__POC__`), refreshed on every repaint, carrying measurable state — never a bare boolean flag:

- dynamic image draws: `imageDraws: [{ nodeId, x, y, w, h, natW, natH }]` — proves sprite identity and placement changed;
- text geometry per node: `textLines`, `textBlocks: { blockTop, blockBottom, rasterTop, rasterBottom }`, `drawnTextStrings` — proves wrap count, overflow, and that no characters were dropped;
- transient UI state with timing: `petLoading` plus a DOM `data-testid` overlay element — makes show/hide latency measurable;
- interaction/window state: `pets`, `cellUserPetIds`, `scrollIndex`, `maxScroll` — makes paging and clamp behaviour assertable.

Rules: expose the values the renderer actually used (post-normalization, post-fallback), not the raw design JSON; and pair every pixel-flavoured claim with a non-pixel witness — the source DB row, the `nodes.json` entry, or a request count. That pairing is what upgrades a screenshot spec into a functional testcase.

### Independent Live Probe (Lead-side verification)

A worker's own red/green output does not verify anything. Reproduce the state yourself in one throwaway script:
1. Mint a session the way the app does — read the signing secret from the deployed `.env` and sign the same claims (e.g. `jose` `new SignJWT({ userId, user }).setProtectedHeader({ alg: 'HS256' })` with `SESSION_SECRET`).
2. Inject it into a headless context for the origin actually served (`ctx.addCookies([{ name: 'poki_session', value: token, domain: '127.0.0.1', path: '/', httpOnly: true, secure: false }])`).
3. Navigate the raw data route (`?raw=1&data=1`), `waitForFunction(() => window.__POC__?.ready === true)`, then read the render hook AND query the source DB row for the same entity in the same script, and print both.
   This catches what a spec can mask: the drawn string must equal the DB field by strict equality (equal length alone hides truncation), the image draw's natural size must belong to the pet actually selected, and a stroke/geometry value must match the brief's arithmetic.
4. Canvas screenshots: derive the sampling scale from the canvas box before treating design coordinates as clip coordinates — `scale = rect.width / canvas.attributeWidth` — because a CSS-scaled canvas makes the two diverge.

### Verifying a PRODUCTION web deploy (after enabling a feature live)

Same minted-session method, three adjustments that otherwise produce a false "it is broken":

- Read `SESSION_SECRET` from the **deployed prod container**, not the repo `.env`
  (`docker inspect <prod-ct> --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^SESSION_SECRET='`).
  Mint the cookie with the prod admin user id looked up in the prod DB (`SELECT id,user FROM users WHERE is_admin=1`).
- Request the **container port directly** (`http://127.0.0.1:<port>/<route>`) with the cookie, not the public
domain. A fronted domain (Cloudflare/CDN) can serve a cached or challenge page and makes the result
uninterpretable.
- A guest request returning the site's login/home shell for a gated route is **expected**, not a regression —
  do not report it as "event not live". The verdict comes from the authenticated request: strip tags from the
  HTML and assert the feature's own strings are present (feature name, its tabs, its live badge) and that the
  "not open yet" string is absent. Check a public listing route separately to confirm discoverability.

Report the distinction explicitly: what was proven from the authenticated render, and which write-path links
still rest on code reading because they could not be exercised without touching production data.

### Test-runner environment prerequisite

Browser suites need a large temp filesystem. Check `df -h /tmp` before and during a long run: a full temp dir makes chromium abort every test with `ERR_INSUFFICIENT_RESOURCES`, which reads exactly like a code regression. If the space is held by data of unknown provenance, move it aside intact instead of deleting it, and report to the user what was moved and where.

---

## 5. Viewport Coordinate Bounds & Viewport Clipping

- **Negative Coordinate Offsets in Figma**: In Figma, modal popups or dialogs are sometimes positioned relative to the root artboard with negative coordinates (e.g. `Popup_Evolution y = -26`, header banner `Bg_Header y = -26`, main frame `Bg_Main y = -7`). In Figma these bleed beyond the artboard boundaries visually without disappearing.
- **Canvas Viewport Clip (`ctx.clip()`)**: The HTML5 Canvas renderer strictly enforces the design canvas bounds (`dw = 1440, dh = 720`) via `ctx.rect(0, 0, dw, dh); ctx.clip()`. Consequently, any node with `y < 0` has its top edge cropped abruptly at the viewport boundary (clipping title banners and decorative headers).
- **Remedy**:
  - Calculate the outer extent of the popup component tree.
  - Apply an explicit vertical offset or vertical centering shift (`y_offset = Math.max(0, -popup.minY)` or `(dh - popup.totalHeight) / 2`) during node flattening or rendering so all child elements sit completely within `0 <= y && y + height <= dh`.

---

## 6. Popup Auto-Fit & Overflow Normalization in Loaders

To prevent recurring manual edits to `nodes.json` across artist re-exports, implement normalization directly within the document parser/loader (`figma-loader-v2.ts`):
- **Functional Normalization (`normalizePopupOverflow`)**:
  - Scan the loaded node list for container nodes matching `/^Popup_/i` (e.g. `Popup_Evolution`, `Popup_PetSort`).
  - Calculate the bounding box of the popup tree (`minY`, `maxY = minY + totalHeight`).
  - If `minY < 0`, compute delta `offsetY = -minY` (or center within `designHeight` if `totalHeight <= designHeight`).
  - Traverse all descendant nodes in the popup subtree and adjust their `y` coordinates: `node.y += offsetY`, `node.absY += offsetY`.
- **Zero Manual Overhead**: Artists can re-export and unpack new `.zip` bundles directly into `public/` without requiring developers to hand-edit coordinates or patch raw JSON files.

---

## 7. Vietnamese Typography & Baseline Alignment in Canvas

A frequent visual regression in localized game canvas interfaces is staggered or jumping characters ("chữ cái chữ trên chữ dưới"):

### Root Cause
1. **Malformed Composite Glyphs**: Stylized display fonts (such as `FC Lilita One`) often have incomplete Vietnamese support. Designers or font tools frequently shrink accented characters (e.g. `Ề`, `Ệ`, `Ê`, `Ỉ`, `Ố`) down to ~65% cap-height to fit diacritics within the standard Latin glyph bounding box, making them appear tiny, thin, and misaligned.
2. **Fallback Font Baseline Jitter**: When a character is entirely missing from the primary display font, browsers fall back to generic system fonts (`sans-serif`, `Arial`). Because the fallback font has mismatched metrics, font bounding box ascent, and stroke weight, accented characters jump vertically relative to unaccented characters.

### Architecture & Fix
- **Vietnamese-Safe Font Stack**: Pair stylized Latin display fonts with a high-quality, bold Vietnamese display font (such as `Baloo 2 ExtraBold`) that provides native, full-height accented glyphs:
  ```typescript
  const POC_FONT_STACK_VN = '"Baloo 2", "FC Lilita One", "Arial Black", Impact, system-ui, sans-serif';
  ```
- **Dynamic Font Switching**: Check text strings for Vietnamese diacritics (`/[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i`) before rendering:
  ```typescript
  tctx.font = hasVietnamese(text) ? `800 ${size}px ${POC_FONT_STACK_VN}` : `${size}px ${POC_FONT_STACK}`;
  ```
- **Alphabetic Baseline with Bounding Box Metrics**: Set `tctx.textBaseline = "alphabetic"` and calculate baseline position using `fontBoundingBoxAscent` / `fontBoundingBoxDescent` to ensure every glyph in the line shares a uniform horizontal baseline.
- **Quantitative Baseline Spec**: Author Playwright regression tests measuring bottom pixel coordinates (`y` bound) across individual accented and unaccented characters to mathematically prove zero baseline drift.

---

## 8. Node Name Binding Mismatches Across PoC Versions

When maintaining multiple PoC iterations (`poc`, `poc2`), `nodes.json` exports may rename semantic nodes between versions (e.g. `Animation_CurrentPet` → `Img_CurrentPet`). Binding code that hardcodes exact node names without fallback will silently produce `null` IDs, causing dynamic image/text updates to fail without runtime errors.

- **Always use fallback chains** in binding lookups:
  ```typescript
  const big = byName(doc, "Img_CurrentPet") || byName(doc, "Animation_CurrentPet");
  ```
- **Symptom**: A pet's icon/sprite never updates when selecting different pets, even though `detail.iconUrl` changes. The `bigPetId = null` because the binding function searches for a node name that doesn't exist in the newer export.

## 9. Raw Mode Conventions (`?raw=1` vs `?raw=1&data=1`)

Canvas PoC routes support two distinct raw modes:
- **`?raw=1`**: Pure static Figma layout preview. No player data loaded, no API calls. Login gate is bypassed.
- **`?raw=1&data=1`**: Hybrid mode — loads real player data AND exports `__POC_RAW__` for pixel measurement. Login gate applies (requires session). Use when tests need to measure data-driven rendering AND raw pixel snapshots in the same spec.

When authoring test helpers like `loadLoggedInRaw`, check which mode the test actually needs. A test that measures data-driven features (sort order, per-pet stats) needs `?raw=1&data=1`, not bare `?raw=1`.

## 10. Canvas Loading Performance & Multi-Tier Asset Streaming

A major performance bottleneck on mobile/web game canvas views is blocking the initial render until every asset in the exported document is downloaded:

### Root Causes of Slow Canvas Boot
1. **Unbounded Concurrent Fetch Requests (Connection Starvation)**: Firing `Promise.all(images.map(preloadImage))` for 100+ raw raster slices immediately upon mount floods the browser connection pool (limited to 6 concurrent HTTP/1.1 sockets per host) and causes head-of-line blocking.
2. **Preloading Hidden Subtrees**: Over 60% of exported slice images belong to hidden modal dialogs, non-default tabs, or collapsed popups (`Popup_Evolution`, `Popup_PetSort`). Downloading them before rendering the primary screen keeps the user staring at a blank screen or loading spinner.
3. **Sequential Initialization Waterfalls**: Awaiting `nodes.json` ➔ awaiting `images.json` ➔ awaiting `loadPocFont()` ➔ awaiting dynamic player state sequentially extends the critical path to interactive (`__POC__.ready`).

### Best Practices & Architecture
- **Tiered Asset Preloading**:
  - **Tier 1 (Initial Paint / Immediate)**: Preload only assets visible on the initial root screen (`Screen_*`) and run `loadPocFont()` in parallel with document fetching via `Promise.all()`. Paint the canvas and flip `ready = true` as soon as Tier 1 completes.
  - **Tier 2 (Background / On-Demand)**: Stream popup images in the background with a concurrency-bounded worker queue (concurrency 4–6) or initiate preloading on hover/click trigger of the popup opening button.
- **Asset Caching & Immutability**: Configure HTTP caching (`Cache-Control: public, max-age=31536000, immutable`) on `/game/poc2/images/*` and font files so subsequent canvas mounts resolve synchronously from memory/disk cache.

---

## 11. Wrapped Text Clipped by a Node-Sized Offscreen Canvas

Symptom: a pet/skill description renders 1–2 lines fine, but from 3 lines up the last line is cut mid-glyph or disappears entirely — while the code still reports the wrapped line count as 4. Do not "fix" this by clamping lines to the node height.

### Root cause
The text block is rendered through a temporary (usually 2x supersampling) canvas allocated with the exact dimensions of the design node box. Figma auto-height text nodes export a height that matches the artist's short placeholder copy, not runtime copy. Canvas 2D hard-clips every drawing operation outside the bitmap, so wrapped lines past the node bottom are silently discarded after the layout code has already produced them.

### Fix pattern
1. Measure the wrapped block first (`measureText` per line, sum line heights) OR size the temporary canvas to the union of the node box and the produced block (`coverTop = min(node.y, block.top)`, `coverBottom = max(node.y + node.h, block.bottom)`).
2. Blit the temporary bitmap back at the block's real top offset, not at the node box top.
3. Publish `blockTop / blockBottom / rasterTop / rasterBottom` for the node via the render-state hook.

### Acceptance criteria (numeric, not visual)
- `textLines >= 3` for a long source string, and `rasterBottom >= blockBottom` (nothing was clipped away).
- `blockBottom > nodeBox.bottom` — asserting the overflow actually happens proves the fix covers the failing case rather than the copy happening to fit.
- **Exact-match witness**: compare the drawn string against the source field read straight from the DB row (e.g. `"Mô tả chi tiết: " + pets.des`) with strict equality. Length comparison alone hides truncation; a 191-character source producing a 207-character drawn string is the correct result, and any mismatch means characters were dropped.
- Also assert the overflowed text does not collide with the next section heading, measured in the same numeric space.

---

## 12. Labels That Wrap Only After a Font Substitution — Honour `textAutoResize`, Never Auto-Shrink

Symptom: a one-line label from the design ("Nguyên liệu tiêu hao", a button caption, a stat label) renders as two lines on canvas, breaking the last word — while the design shows one line. It appears only for some strings, and only after the Vietnamese-safe font substitution in §7.

### Root cause
1. The design tool sized the text node's box for the ORIGINAL display font. Swapping in a wider fallback (a full-height Vietnamese font measures ~7–9% wider than the stylized Latin display font) makes the same string exceed a box the designer correctly sized. Measure both fonts at the design size against the box width to prove this: original fits, substitute overflows ⇒ the exporter is correct and the renderer is at fault.
2. The renderer wrapped on "string wider than box" without consulting the node's auto-resize mode.

### Fix pattern — use the design tool's own semantics
- A node exported with a FIXED box (`textAutoResize` = `NONE` or `WIDTH_AND_HEIGHT`) must render on **exactly one line** — never wrap it; let it overflow horizontally inside its parent. Only `HEIGHT` (grow downward) wraps.
- Apply this as ONE rule in the shared text path, driven by the node's exported mode, not by a per-node id list and not by the node's height heuristic.

### Rejected alternatives (state why, so nobody re-litigates)
- **Auto-fit / horizontal scale to fit**: the design tool has no such behaviour; scaling the string distorts pixel parity. Reject.
- **Reverting to the original display font**: re-breaks the diacritic glyphs (§7). Reject.
- **Mixing fonts per script**: they have mismatched metrics and break the shared baseline (§7). Reject.

### Acceptance criteria (numeric)
- Sweep **every** TEXT node on the live canvas, on desktop AND mobile viewports: each node whose source string contains no `\n` must report exactly one line; a node with `\n` must report the split count.
- For a node that legitimately overflows its box, assert nothing was truncated (the raster right edge reaches the measured text end, tolerance ~2px) and that the node was drawn once.
- Record, alongside the fix, how many nodes overflow and the top offenders — the number is the scope of the font-substitution debt, and it is what tells a future session whether the pipeline or one label is broken.
- This rule strictly PRECEDES any "clamp lines to node height" patch: clamping hides real copy.

---

## 13. Eligibility-Gated Dialogs — Condition From Real Config, Denial Must Be Visible

A button that opens a dialog unconditionally will open it for entities the feature does not support. The fix is not a hardcoded id list.

- **Source the condition from the feature's own config table** (a `source_id -> target_id` mapping table, a requirements table, a rule row), not from a boolean column that is set to `1` for every row — a column that is always truthy looks plausible and silently admits everything. Verify the table actually discriminates (count distinct values / rows) before briefing it as the source of truth, and have the worker expose the resolved decision plus its reason (`eligible`, `targetId`, `reason: no-config | target-missing | ok`) on the render-state hook.
- **The denial branch must be visible to the user, and it must be the SAME surface as the success branch's feedback.** A handler that only writes a message into the debug hook renders nothing: the user clicks and sees a dead button. Require a real DOM node with a `data-testid` (a toast with `role="status"`, `pointer-events: none`), assert its text and that it stays on screen long enough to read (≥500ms), and place it so it shows in every display mode — a `position: fixed` toast survives fullscreen, a panel-anchored one does not.
- **When the gate denies, fire nothing else**: assert zero asset requests for the dialog's own sprites, so a hidden-but-mounted dialog cannot quietly fetch and animate.
- **Gate the button's presence on display mode too**: a control rendered behind a `&& !isFull` style condition simply disappears in the mode the user is in, which reads as "the button does nothing". Sweep every display mode (windowed, fullscreen, mobile portrait with the 90° rotation) in the acceptance case.
Follows the §13 lifecycle, scoped to the dialog being open — `loopsActive` returns to 0 when it closes, and reopening resumes from cache without new requests.

---

## 14. Animated Sprites (GIF) on a Canvas Scene

A canvas does not animate a GIF. Drawing an `<img>` of a `.gif`, or drawing a single decoded frame each repaint, displays the FIRST frame forever — every "image present at the right position and size" assertion passes while the user sees a still. Treat animated sprites as four separate requirements: decode, schedule, lifecycle, fallback.

### Decode (see also §13 for the dialog-scoped case)
- Parse all frames plus their **per-frame delays** (GIF89a graphic control extensions), and composite frames correctly (disposal method, transparency, interlacing). Do not assume a uniform FPS or take only frame 0.
- Fetch the bytes yourself (`fetch`, check the HTTP status, decode to a blob/object URL or `ImageBitmap`) so a non-200 is a value you can branch on, and so the canvas is not tainted. A plain `<img>` gives you no status and no frame list.
- Keep the parser in ONE shared module used by every sprite location (e.g. the combat-power portrait and the evolution dialog's before/after slots). Two copies drift, and the second location silently keeps the still-frame bug after the first is fixed.

### Schedule
- Pick the current frame from elapsed time (`(now - t0) % totalMs`) walking the delay table, in an infinite loop; never assume frames are evenly spaced.
- **Cap the redraw rate**: only repaint when the frame actually changed AND at least ~50ms elapsed (~20 fps). A canvas scene is usually repainted whole, so an uncapped loop multiplies full-scene cost; measure and report the per-repaint cost rather than asserting it is cheap.

### Lifecycle (leak-proofing — assert it, don't assume)
- Exactly one running loop per VISIBLE sprite. Cancel on unmount, cancel when the document goes hidden (`visibilitychange`), and stop the previous loop before starting the new one when the sprite's entity changes.
- Publish `loopsActive` and a per-sprite draw counter on the render-state hook, then have the test open/close the containing surface several times: `loopsActive` must return to 0 when closed and must not grow across cycles.

### Fallback & budget
- On 404 / network / decode failure / timeout, draw the node's existing static icon in the SAME box (no layout shift, no blank) and publish `state = "fallback"` plus the reason and the HTTP status. A remote sprite service will be missing entries for some real ids — expect 404 as a normal branch, and assert the fallback actually drew (non-zero draw dimensions), not merely that no error was thrown.
- Cache decoded sprites by entity id and dedupe in-flight fetches; revisiting an entity must not re-request (count requests per URL in the test).
- Keep animated assets OUT of the boot batch — request only after the scene reports ready — so boot-time budgets do not regress when animation is added.

### Remote sprite CDN (verify the contract yourself before briefing)
- Probe the URL pattern with two `curl`s before writing the brief: one id known to exist (`200 image/gif`) and one nonsense id (expect `404`, often a JSON error body). That pair IS the fallback branch the brief can specify numerically; "if it 404s then fall back" is untestable until you have seen the 404.
- Assume entries are huge (a single sprite can be >1 MB). Therefore: cache decoded sprites by entity id, fetch only after the scene reports ready, never put them in the boot batch, and bound the wait (a few seconds) before falling back so a slow entry cannot hang the view.
- The id in the URL is the entity's design id (from the entity table), not the per-user instance id — assert which one the URL uses, since both exist and the wrong one 404s for everyone.
- Some real entities will be missing from the CDN. That is a normal branch, not a bug: the fallback must draw at the SAME box (no layout shift) and publish the HTTP status so the test asserts the branch that ran — including a `data-testid`-visible notification when the request fails in a user-facing way.

### Acceptance criteria (the part that actually catches a still frame)
- Sample the sprite's own canvas region repeatedly ~100–300ms apart and require **≥2 distinct hashes**, plus a frame index that changes between samples. "Image drawn" and "state = animated" prove nothing on their own.
- Record the hashes and the frame-index samples in the test log so a later flake is diagnosable.
- Assert the inverse too: a one-frame sprite must report `animated === false` and keep a constant hash (no loop started).
- When such a case fails only inside a multi-file batch but passes alone, treat it as flake: convert the fixed sampling window into bounded poll-until polling (deadline ~5–8s) — never drop the distinct-hash requirement or downgrade to a boolean flag.
