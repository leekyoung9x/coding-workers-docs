# Unity WebGL automation that tests the product

## Three layers, separate verdicts

1. EditMode/unit: production DTO rules, prefabs/bindings, cost/cooldown/state logic; no fake alternative UI. Test asset references and qualifying fixtures.
2. PlayMode/integration: instantiate the production panel under its actual canvas/hierarchy and exercise Unity EventSystem input, close/reopen, reconnect and viewport changes. Test real local API/Colyseus messages/DB effects on seeded accounts with recovery cleanup. Editor render is layout evidence only, never player/browser E2E.
3. Browser/WebGL E2E: same dev build identity, actual authenticated user path, real Playwright clicks, response/state changes and modal-specific screenshots/video. Player may differ from Editor, so PlayMode cannot replace this layer.

### Phase separation: Visual layout vs Full player E2E
Validating UI/visual layout in an isolated diagnostic route (`?pokidiagreal` or standalone test scene) is a valid, user-approved first phase to verify modal geometry, anchor bounds, scaling (fit-inside Figma 1440x720) and overlay coverage before running the full player flow.
However, jumping directly into game panels without lobby/room creation triggers missing-room `Debug.LogError` calls. In Unity WebGL Development Builds, any `LogError` causes the on-screen Development Console to automatically pop up, which overlaps action buttons (e.g. 'Sử dụng') and breaks overlay continuity.
- In visual diagnostic passes: suppress the on-screen console popup (`Debug.developerConsoleVisible = false` or clean release build) while pre-populating required room mock state (e.g. `PlayerPrefs.SetString("battle_colyseusRoomId", "preview")`) and keeping console error capture active in the test harness. Ensure fullscreen scrims use a valid sprite (fallback to `Texture2D.whiteTexture`) so WebGL renders the dimming layer.
- When evaluating visual layout fit: distinguish aspect-ratio slack from broken layouts. A centered modal splits margin evenly, leaving a gap below bottom action buttons; if the scrim is translucent (`alpha <= 0.8`), bright ground/water textures bleed through, appearing as an unfitted layout ("hở bên dưới"). Tests must verify whether the modal is expected to be bottom-anchored or centered on an opaque/deeply-dimmed backdrop.
- In full player E2E passes: require the real authenticated flow (login -> lobby -> match creation -> action), ensuring real rooms exist and zero `LogError` occurs, so the console never triggers naturally.

Run cheap gates first and build the player once per source/config hash. Reuse browser/assets carefully; do not reuse stale task/game state. Keep a full login case each suite, pin account/build/env when reusing a genuinely authenticated session. Measure timings before setting deadlines; never invent load-time ETA.

## Read-only bridge instead of OCR navigation

Add a dev-only read-only snapshot, not a command backdoor: run/build/frame id, scene/panel, viewport/canvas rect, projected control bounds, active/visible/interactable and GraphicRaycaster top hit, slot/code/detail text, costs and request/WS verdict counters. Sample from production components actually drawing, not an independently invented debug model.

Derive canvas-relative click coordinates from the snapshot, then use actual browser mouse/keyboard events. OpenPopup/direct SendMessage-to-handler/forced state are diagnostic or unit-only, excluded from E2E certification; invoking engine SendMessage hooks (e.g. `Btn_ChinhPhuc` click) on a live E2E run must fail or mark the step `DIAGNOSTIC_HOOK_USED` and block dependent gates. Mutation disabling a button must fail the path. Geometry/state alone cannot prove rendering: pair with pixels and transport outcome.

Use OCR/templates as supporting evidence or recovery diagnosis, not blind text search/repeated Giftcode or login taps. A lone HUD word Bổ trợ does not identify the modal.

## Evidence and negative controls

Bind trace/PNG/result to fresh run_id and exact source/config/build hash. Evidence paths in cases.json must be stat-verified on disk (`os.path.isfile` and `os.path.getsize > 0`); nonexistent paths must fail closed. Text/cost ink thresholds must require meaningful floors (e.g. `ink >= 0.04`), never `> 0.0` which passes on single-pixel noise. Capture modal-specific regions at measured conditions across several frames; verify five slots, header, detail, Use/Close, full overlay continuity (row-by-row pixel scan showing no gaps or tears) and no unintended clipping or console overlay covering buttons. Capture close/reopen too. Whole-board pixel delta, filesize and darkness individually are insufficient.

Never auto-update golden screenshots in a failed run. Baseline approval is independent of the author; edited baselines alone cannot green a release. Test known bad board PNGs and hidden/disabled/cropped/zero-scale mutations. Sample editor frames may pass only UNIT/layout.

Release gate: ran == required count, zero required skip/missing, zero console/pageerror/unhandled errors, matching build/env and no forbidden destinations. Success/refusal paths assert actual resource/selection/response behavior. Seed qualifying dev fixtures, never change game content to green tests.

Block production BEFORE requests, including localhost ports hosting live services. Localhost alone is not an allowlist. Cover redirects, service workers and WebSockets at the transport boundary. DB/API schema/hash checks supplement, not replace, visible UI proof.

## Limits

Harness self-test counts certify only exercised controls, not game flows. Report unit/integration/browser counts separately and explicit not-run blockers. Read-only bridge, caching and PlayMode tests remain proposed until exercised on real artifacts. No approach eliminates every regression; failure injection and independent verification constrain false confidence.
