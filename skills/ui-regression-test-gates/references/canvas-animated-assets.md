# Animated assets (GIF) on a canvas — behaviour and the evidence that proves it

Context: a canvas HUD draws entity icons from a CDN. Some assets are animated GIFs, some 404 (the
fallback must be the static icon), and the page must keep its boot budget. Every rule below came from a
measured failure.

## 1. "It loaded" ≠ "it animates"

`new Image()` with a blob object-URL plus `drawImage` paints frame 1 forever. Observed alongside it:
HTTP 200, no console error, and a debug object reporting `state: "gif"` — while the user reported the
image standing still.

Evidence that distinguishes the two: hash the node's screen region ≥8 times, 100–300ms apart, and require
≥2 distinct hashes together with a code-exposed frame index that changes. Measured: 1/8 distinct before
the fix, 6/8 after. Publish `{frames, animated, frameIndex, fps, draws}` on the debug object so the case
asserts numbers instead of pixels alone.

## 2. Decode frames + per-frame delay yourself

Parsing GIF89a means: Graphic Control Extension (delay, disposal method, transparency), LZW decompression,
de-interlace, then compositing each frame onto its own canvas honouring the disposal method. Index the
frame by elapsed time against the CUMULATIVE delay table.

Do not assume a constant FPS — measured 24 frames with an average delay of ~40ms and non-uniform delays.
A fixed-interval loop drifts against the file's own timing.

## 3. Redraw budget, visibility, and loop lifetime

- Redraw only when the frame index actually changed AND at least ~50ms elapsed since the last draw
  (~20 FPS). Measured 18 draws/s.
- Stop on `document.visibilitychange` → hidden (cancel the rAF) and resume on visible.
- Cancel on unmount, and when switching entity STOP the previous loop before starting the next.
- Expose the live loop count and assert it in a case that opens/closes the panel ≥3 times and switches
  entity: measured 2 ↔ 0 with max 2 and no growth across cycles. Without that case, leaked loops are
  invisible until the fan spins up.

## 4. Keep it out of boot, cache it, time it out

- Fire the fetch AFTER the page reports ready; request timestamps must be later than the ready mark, or the
  boot-budget case (ready ms, boot request count) breaks.
- Cache decoded frames per entity id with in-flight de-duplication. Assert that revisiting an id adds ZERO
  requests (measured `reqA=1 reqB=1` across A→B→A).
- Time out (~5s) to the static fallback rather than hanging the slot.

## 5. Fallback

- The fallback must be a REAL image drawn into the node's box: assert an entry in the image-draw log with
  `w > 0`. A blank slot passes structural checks while the user sees a hole.
- A probed 404 emits exactly ONE console 404 line. Assert that specific count instead of letting the
  console gate fail, and keep the rest of the console gate at zero.
- Expect entities whose animated asset genuinely does not exist on the CDN to take the fallback
  permanently — that is the feature working, so the case should assert `animated=false` plus a static hash
  (no change over ≥5 samples).

## 6. One shared implementation

Extract the decoder + cache into one module and have every slot that shows an entity icon use it — the
main icon, and both slots of a before/after popup. Two hand-rolled copies drift: the popup copy initially
showed static images while the main icon animated, and only the popup case caught it.

Measured popup numbers to expect: before 24 frames, after 13 frames, 5–7 distinct hashes over 8 samples,
`loopsActive` 2 while open and 0 when closed, one request per id even after reopening.
