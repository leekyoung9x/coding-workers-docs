---
name: unity-headless-build
description: "Use when building Unity headless on a Linux VPS."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [unity, headless, linux, vps, webgl, android, build]
    related_skills: [lead-worker-orchestration]
---

# Unity Headless Build (Linux VPS)

Procedure for getting from bare Ubuntu VPS (no GPU) to repeatable
headless Unity builds driven by agents reading log files. GUI is needed
exactly once (license activation); everything after is CLI.

## 1. Pin the version first

Read `ProjectSettings/ProjectVersion.txt` and install exactly that patch — a
different patch triggers project convert plus a full `Library/` rebuild.
Keep the changeset hash from that file: old patches disappear from
`editors -r`, and installing them requires `--changeset <hash>`.
Verify tarballs return HTTP 200 before the long install when in doubt.

## 2. System dependencies

Install the Hub/Editor dependency set for the distro. Package names drift
between Ubuntu releases (e.g. `t64` renames); resolve via apt `Provides:`
rather than forcing old names, and skip obsolete packages (e.g. GConf)
the Editor no longer needs instead of breaking the install over them.

## 3. Install Unity Hub headless

Use the official apt repo, then drive it headless. Two traps:

- The package binary is `unityhub`, not `unity-hub` — provide a wrapper of
  that name if briefs/scripts expect it.
- Running as root without X fails two ways (Electron sandbox refusal, no
  `$DISPLAY`) — wrap every Hub call as
  `xvfb-run -a unityhub --no-sandbox -- --headless <cmd>`.

Verify with `editors --installed`.

## 4. Install Editor + build modules

```bash
xvfb-run -a unityhub --no-sandbox -- --headless install \
  --version <X.Y.Zf1> [--changeset <hash>] \
  --module webgl [android] --childModules
```

Install only the modules the next build needs (WebGL ships Emscripten,
Android ships JDK/SDK/NDK via childModules). iOS Build Support does not
exist on Linux hosts — never attempt iOS player builds on the VPS; keep
the Mac/fastlane lane untouched.

Hub headless `install-modules` can stall forever on newer streams: the
Android module ships as a macOS PKG, so Linux Hub downloads it then sits
at `[Android Build Support] queued for install` with zero active
installers and never progresses. When the queue does not advance within
minutes, abandon Hub for modules and use the new Unity CLI instead
(`unity install-modules -e <X.Y.Zf1> -m android --cm --accept-eula
--non-interactive -y`), which downloads, validates, and reports
`{"status":"installed"}`. Verify `PlaybackEngines/AndroidPlayer/` exists
before wiring any `-buildTarget Android` call. Never hand-diagnose a
module URL by guessing `download.unity3d.com` filename patterns —
WebGL and Android use different installer layouts per stream, so a
guessed URL 404s while the real module is one CLI command away.

## 5. Install location: never under a locked home

Put the Editor where the build user can execute it (e.g. `/opt/Unity`
with symlinks from old paths). Root's home is mode 700, so anything under
`/root` is unusable by the license-owning user even with the binary itself
chmodded open — permission-denied on a `rwxr-xr-x` binary means an
unreadable parent directory, so inspect the whole path, not the file.
Expose one stable path (`/usr/local/bin/unity-editor` symlink) and let
scripts override it via a `UNITY` env var.

## 6. License is per-user — builds run as the activating user

A Hub-activated Personal license belongs to the user who logged in; a
different OS user probing the same Editor gets `No valid Unity Editor
license found`. Run every Unity process (import, check, build) as the
activating user, and probe license state from that user:

```bash
su -s /bin/bash <user> -c '"$UNITY" -batchmode -nographics -quit \
  -projectPath <project> -logFile /tmp/unity-license-probe.log'
grep -inE "No valid|Successfully updated license" /tmp/unity-license-probe.log
```

Never log out of Hub on the build machine — logout returns the Personal
license. Never pass `-serial` tricks for Personal; only Hub login
activates it.

## 7. One canonical build script, not Hub flags memorized

Ship one script (e.g. `build-linux.sh`) with subcommands `import`,
`check` (compile-only), `webgl`, `license`, `version`. Every Unity call
uses `-quit -batchmode -nographics -projectPath <dir> -logFile <file>`,
plus `-buildTarget <X>` and `-executeMethod <Class.Method>` for builds.
Agents read errors from the log file, never stdout. Record per-stage
durations to a history file so progress estimates improve.

- **Multiple Editor versions & explicit path:** When multiple Editor versions exist on the host (e.g. `/opt/Unity/Hub/Editor/6000.0.26f1` and `6000.6.3f1`), never rely on default version fallbacks in scripts. Verify against `ProjectSettings/ProjectVersion.txt` and explicitly pass `UNITY=/opt/Unity/Hub/Editor/<exact-version>/Editor/Unity`. Running an older editor against a project bumped to a newer patch triggers package resolution failures (`com.unity.modules.* cannot be found`) or corrupts the `Library/` cache.
- **DISPLAY environment variable on Linux VPS:** When running batchmode Unity on a Linux VPS with an active X11/xrdp session, Unity Editor may probe the default display and abort with `cannot open display / Error opening default X display. You must have a valid X server running`. Always pass `export DISPLAY=:10` (or wrap with `xvfb-run -a`) when invoking Unity commands under the build user.
- **Unity 6000.6 package API obsolescence:** Upgrading to Unity 6000.6 turns several legacy properties into compile errors (`[Obsolete(..., true)]`). In TextMeshPro/Figma UI packages, replace `TMP_Text.enableWordWrapping = val` with `textComponent.textWrappingMode = val ? TextWrappingModes.Normal : TextWrappingModes.NoWrap`. For unused legacy editor drop handlers (e.g. `DragAndDrop.AddDropHandler`), wrap the class with `#if false ... #endif` or update to `AddDropHandlerV2` to eliminate compile errors.
- **Deliverable target build path & domain alignment:** An isolated diagnostic build folder (e.g. `build/webgl-dev-recovery`) is only an intermediate scratchpad. Always verify the exact directory served by Caddy for the domain the user is inspecting:
  - If the user tests on the public domain (e.g. `https://pokiwar.pokiguard.com/`), Caddy serves `build/webgl` (Brotli release). If updates are only compiled to `build/webgl-fast` (port 8798), the user sees stale code from days ago and reports missing UI elements ("k thấy nút bổ trợ đâu").
  - When building for public/live domains, never inject local dev scripting defines (like `POKI_DEV` hardcoding `API_HOST = 127.0.0.1`): from an external browser, `127.0.0.1` hits the user's local machine, causing instant login/network failure ("Đã xảy ra lỗi!"). Production/live builds must use the clean entry point (`BuildWebGL.Build`) without dev defines.
  - When re-building an existing directory with different compression or uncompressed files, remove stale `.br` / `.gz` artifacts (`rm Build/*.br`) so Caddy/Cloudflare never serve old cached compressed files.

## 8. Scene list is the build content

Unity builds only scenes with `enabled: 1` in
`ProjectSettings/EditorBuildSettings.asset` — unticked scenes ship
nothing even though they exist in source. Before the first build,
reconcile that list against the build entry's scene fallback in
`Assets/Editor/`; a missing screen in the player is a tick problem,
not a bug. Do not change the list without the user's call. For an invisible button, measure artifact identity, active hierarchy, viewport bounds, masks, CanvasGroup alpha, sorting and raycast hits before choosing a fix. Require every HUD control inside the canvas and zero unintended label overlap. UnityEngine.Object overloads `== null` so a destroyed native object normally compares null; C# reference identity and Unity null semantics differ. Do not assume `if (btn != null) return` skips recreation for a destroyed object, or add a redundant null patch as a diagnosis. Prove the lifecycle with an enable/disable/reconnect test on the actual runtime.

## 8b. Nested Canvases and in-game popups (uGUI WebGL)

Treat nested Canvas/scaler/camera interactions as falsifiable hypotheses, not a universal WebGL failure. Inspect actual rootCanvas, render mode, camera, inherited scale, scaler, masks, alpha and graphic geometry in Play Mode and player. Compare with the project's working popup/Stone hierarchy. Test one change at a time and require newly rendered pixels plus structural evidence.
- An exported standalone screen reused as a child modal should follow the verified parent `popupLayer` pattern; remove redundant scaling only when the measured reproduction proves it is the cause.
- Blindly increasing sortingOrder cannot fix clipping, zero geometry or invisible graphics. Preserve the verified parent camera/render mode rather than assuming a new standalone overlay is required.
- For camera/world-space canvases check UI layer against camera cullingMask. Screen-space overlay has different rendering semantics; do not apply camera-culling conclusions indiscriminately.
- **Fullscreen modal scrim/overlay hierarchy:** When a modal frame scales down for `fit-inside` (`s < 1.0`), never place the dark dimming scrim (`Bg_Scrim` / `Bg_Overlay`) inside the scaled design root. If placed inside, the scrim scales down with the modal, leaving an un-darkened gap at the bottom or sides where the underlying game scene/board shines through. Attach the fullscreen scrim directly to the root Canvas (sibling to the scaled design root, stretching `anchorMin = (0, 0), anchorMax = (1, 1)` with negative-offset overscan like `offsetMin = (-120, -120), offsetMax = (120, 120)` to prevent any 1px edge/alpha bleeding, matching the proven Stone/ScreenPet `BackgroundOverscan` pattern in `FIGMANEW_CANVAS_MECHANISM.md`). Ensure the scrim Image has a pure solid Sprite assigned (never `m_Sprite: null` / `fileID: 0` with `m_CullTransparentMesh: 1`, which culls or fails to generate mesh in WebGL, and never assign a tinted/translucent asset like `endless_img_1.png`; fallback to `Sprite.Create(Texture2D.whiteTexture, new Rect(0,0,4,4), new Vector2(0.5f,0.5f))` with `Color(0,0,0,0.95f)` to ensure true dark opacity). If discovered under a prefab child at runtime, reparent it to the unscaled root Canvas (`SetParent(root, false)`).
- **Modal dialog centering vs bottom gap pitfall:** Modal dialogs in game UI must be centered on BOTH axes (`anchorMin = anchorMax = (0.5, 0.5)`, `pivot = (0.5, 0.5)`, `anchoredPosition = (0, 0)` with subtle visual-weight compensation like `y ≈ +5..+8px` if a bottom action button hangs off the frame). Never attempt to fix a visible ground/background gap ("hở bên dưới") by shifting the content panel down to dock against the bottom edge — shifting creates an asymmetric top-heavy layout and triggers direct user rejection ("popup phải căn giữa cả x và y chứ"). The background showing through is solved solely by extending the fullscreen dark scrim (`Bg_Scrim` / `Bg_Overlay`) across the entire Canvas with negative-offset overscan (`offsetMin=(-120, -120), offsetMax=(120, 120)`), never by displacing the centered modal container.
- **Canvas to browser coordinate conversion for Unity WebGL Playwright testing:** Unity uGUI coordinates have origin at the bottom-left ($Y$ points up), whereas browser Playwright mouse events have origin at top-left ($Y$ points down). When reading `RectTransform.GetWorldCorners` $[(x_0, y_0), (x_2, y_2)]$ or local canvas coords, compute browser click points strictly as:
  `page_x = canvas_rect.x + (x_0 + x_2) / 2`
  `page_y = canvas_rect.y + (canvas_rect.height - (y_0 + y_2) / 2)`
  Never guess click coordinates by fuzzy OCR when exact `worldCorners` or canvas dimensions are measurable — approximate clicks miss small HUD buttons (like in-match buttons) by 20–40px, leading to false claims that the button did not respond.
- **Visual evidence rule for UI acceptance:** Never declare PASS, claim completion, or offer speculative architectural choices to the user when a visual defect is reported ("hở bên dưới", "bị che nút"). A green test runner or bounding-box metric alone is meaningless if the human eye rejects the visual composition. Implement the layout correction, run the WebGL build, capture the actual rendered frame, verify with vision, and present the image as proof.
- **WebGL runtime graphic instantiation:** In WebGL players, UI graphics instantiated purely at runtime via C# (`new GameObject(..., typeof(Image))`) without authored prefab components frequently fail to render or cull unexpectedly. Author modal scrims, borders, and backdrops directly into the prefab rather than relying on runtime construction.
- **Development Console auto-popup:** In WebGL Development Builds, any `Debug.LogError` (such as a missing match roomId when opening an in-match panel in an isolated harness) automatically pops up the on-screen Development Console, obscuring bottom action buttons (like "Sử dụng"). Isolated UI harnesses must mock room dependencies (e.g. pre-set `battle_colyseusRoomId = "preview"` in PlayerPrefs) and set `Debug.developerConsoleVisible = false` to prevent debug overlays from corrupting visual acceptance screenshots.
- **Reverse-proxy & Controller path parity:** When adding new API endpoints (e.g. `/api/userPets/skill-books/{userId}`), ensure reverse proxy (Caddy) and ASP.NET Core controller routes match exactly: controllers with `[Route("userPets")]` do not match `/api/userPets` unless both routes (`[Route("userPets")]` and `[Route("api/userPets")]`) or proxy rewrites are defined. Unmatched routes fail with 404/500 and trigger the Unity developer console in-game.
- **Pre-battle room & stale active room traps in E2E automation:** 
  1. *Stale room reconnect:* When automating login into a test client, if the account has an unfinalized active room in DB (`/api/battle/active-room/{userId}`), the client auto-reconnects to it, immediately hitting `idle_timeout` and displaying a "THẤT BẠI!" modal. Automation scripts must click "NHẬN" (at center X, ~54-58% Y) to clear the stale room and return to the main hub before entering a new match.
  2. *Pre-battle lobby step:* In Pokiwar PvE (Chinh phục), selecting an island and clicking "Chiến" enters a Pre-battle Lobby room, NOT the active match board. The script must click the "Bắt đầu" button (at ~55% X, ~70% Y) to launch the Colyseus match and render the 8×8 match board.

## 9. Pipeline order and locks

Order: system check → `import` once (creates `Library/`, tens of minutes)
→ `check` per edit → tests → player build last. Never `rm -rf Library`
(it discards the import cache the whole pipeline depends on) and never
run two Unity processes against one project — serialize with an owned per-project lock. For `another Unity instance is running`, identify the actual lock holder/executable/project/fingerprint first. Do not kill all Editors or match task argv; stop only the owned failed build if required. Remove `Temp/UnityLockfile` only after proving no valid holder remains. A permission/lock issue is not automatically a Unity crash.
IL2CPP player builds (especially Android) can OOM-kill the worker
itself: the kernel kills `dotnet` inside the agent's cgroup and the run
dies with exit 137/SIGTERM and no REPORT. Check `dmesg` for `oom-killer`
before assuming a code failure, keep only one Unity build in flight per
machine, and run long player builds detached (e.g. a systemd unit) so a
killed agent does not take the build down with it.
Serialization covers file-mutating work too, not just Unity processes: a
second worker moving or deleting files under `Assets/` mid-build triggers
reimport and corrupts the running build, so hold cleanup/asset-move briefs
until the build finishes.
Treat repo build scripts calling Editor methods that no longer exist
(renamed/removed build entries) as dead commands: grep `Assets/Editor/`
for the method name before wiring any `-executeMethod` into the script.

## 10. One-time GUI activation via RDP

For the single login session: install `xfce4 xrdp dbus-x11`, write
`exec startxfce4` to the login user's `~/.xsession`, enable xrdp, and
open only port 3389 (never disable the firewall). The RDP user needs a
real password — bypass interactive quality checks non-interactively with
a pre-hashed password (`openssl passwd -6` + `usermod -p`), which sets
the hash directly instead of fighting the dictionary check. Install
Firefox so the Hub OAuth flow has a browser to redirect through; if the
browser-to-Hub handoff stalls, feed the `unityhub://login?...` callback
URL to the running Hub via `xdg-open` under the RDP user's display.
After activation, disconnect (do not log off) and return to headless.

## 11. Platform-incompatible code: stub in game code, never hand-patch the cache

When a package uses APIs missing on the build target (e.g.
`UnityEngine.Microphone` does not exist on WebGL), wrap the game-side
manager in `#if !UNITY_WEBGL` but keep the class shape on the excluded
platform — no-op public methods, default-valued properties, `Instance`
still assigned — so existing callers compile unchanged. Never hand-patch
`Library/PackageCache` and call it fixed: the cache is regenerated on
reinstall/import and the patch silently vanishes. Ship any package-side
fix as a durable `Assets/Editor/` script (preprocess-build hook or
postprocessor) that re-applies automatically after import, and record
the mechanism in the report so a clean clone reproduces it.

Nakama SDK on WebGL: the default 4-arg `new Client(scheme, host, port, key)`
uses `HttpRequestAdapter` (`System.Net.Http`), which traps as wasm
`function signature mismatch` at auth time. Pass
`UnityWebRequestAdapter.Instance` explicitly on `UNITY_WEBGL` (the SDK's own
WebGL sample does this); keep the old constructor on other platforms. A real
`NKSocketState` arity mismatch in the jslib is inert (no call-site) — fix it
durably too, but never mistake it for the auth crash.

Third-party WebSocket jslib plugins fail on WebGL player builds while working in the Editor: the shim resolves callbacks through `getWasmTableEntry`, which newer Editors no longer emit, so `Module.dynCall_*` is never installed and the live page throws `TypeError: Module.dynCall_vi/viii is not a function` on `ws.onopen`/`ws.onmessage` while multiplayer joins time out against a healthy server. Reproduce from the shipped build's console (never the Editor) before touching the server; rewrite the `.jspre` to walk every table API in order (`getWasmTableEntry` → `wasmTable.get` → `Module["wasmTable"].get` → indirect-function-table export → `dynCall_<sig>`), and fix durably via an `Assets/Editor/` hook plus `link.xml` preservation covering the plugin's exact signatures (an entry that misses them changes nothing) — never a hand-patch of `Library/PackageCache`. Re-verify the same console lines are gone on the deployed build.

Committed render-pipeline assets saved by a newer Unity than the build
Editor fail the pipeline's own version validator (an asset newer than
the bundled pipeline can never self-heal, since upgrades only go
forward) — either build with the matching Editor version or ship a
stop-gap that clamps only the in-memory version bookkeeping and is a
no-op when versions already match; never silently re-save the assets
as the fix.

## 12. Serving WebGL: headers, Cloudflare, and self-verification

Unity's Brotli output (`.data.br`, `.js.br`, `.wasm.br`) carries a
`UnityWeb Compressed Content` marker and must be served with
`Content-Encoding: br` plus the matching `Content-Type`
(`application/javascript`, `application/wasm`) — a bare HTTP 200 with
the file body still fails in-browser with `Unable to parse ...`, so a
status-code check alone proves nothing. Caddy shape:

```
root * <build/webgl>
@jsbr path *.js.br
header @jsbr Content-Type application/javascript
header @jsbr Content-Encoding br
@wasmbr path *.wasm.br
header @wasmbr Content-Type application/wasm
header @wasmbr Content-Encoding br
@databr path *.data.br
header @databr Content-Encoding br
@loader path */webgl.loader.js
header @loader Cache-Control "no-cache, no-store, must-revalidate"
@html path *.html /
header @html Cache-Control "no-cache, no-store, must-revalidate"
file_server
```

Do not add `encode gzip zstd` on the same block — re-encoding
already-compressed `.br` output corrupts the stream the loader expects.

- **Cloudflare edge caching of `webgl.loader.js`:** Cloudflare edge caches `webgl.loader.js` with `max-age=14400` (4 hours, `cf-cache-status: HIT`). When a new build is deployed with updated wasm/data sizes, browsers receive the old cached loader which attempts to validate against new binary files, triggering `Invalid binary data file size!` or `wasm streaming compile failed`. In `index.html`, always append a cache-buster query parameter to the script loader: `var loaderUrl = buildUrl + "/webgl.loader.js?v=" + Date.now();` and set `Cache-Control "no-cache, no-store, must-revalidate"` on the server.
- **Truncated Brotli compression (`Invalid binary data file size!`):** Compressing large WebGL data files (`webgl.data` > 200MB) via default Brotli (quality 11) takes 5–8 minutes. If a build script times out or process exits prematurely, `webgl.data.br` is truncated on disk without an explicit error. When the client browser decompresses it, downloaded length is less than expected, throwing `Invalid binary data file size! (offset=X, size=Y, file length=Z)`. Always verify decompression integrity offline before deploying (`node -e 'require("zlib").brotliDecompress(fs.readFileSync("...webgl.data.br"), ...)'`). For fast, stable Brotli compression that avoids timeouts (~2-3s instead of 6m), invoke Unity's native brotli binary directly with quality 5: `"<Editor>/BuildTools/Brotli/linux_x86_64/brotli" --quality 5 -i "<artifacts>/webgl.data" -o "<output>/webgl.data.br" --comment "UnityWeb Compressed Content (brotli)"`.

Behind a Cloudflare proxy (orange cloud), Let's Encrypt HTTP-01 and
TLS-ALPN issuance fail (the challenge returns 403 through the proxy)
— flip the record to grey cloud until Caddy obtains the cert, then
re-enable proxying. Renewals need the same window, or switch issuance
to DNS challenge.

Verify serving yourself before asking the user to open the page: curl
all three `.br` URLs and assert `content-encoding: br` plus the
correct content-types in the response headers, then load the page in a
real browser session and confirm no red banner. The same header rule applies to throwaway test servers: stock `python -m http.server` serves `.gz` without `Content-Encoding: gzip`, so a gzip test build dies at boot with `Unable to parse ...framework.js.gz` — serve test builds with a handler that sets the encoding headers, mirroring the Caddy block. Unity-rendered controls normally expose no DOM inputs; derive non-secret click targets from measured canvas/control maps and use real browser input. Never replay passwords through Playwright `keyboard.type` or tool inputs: use the approved vault-entry workflow on an exact-origin credential surface. Diagnostic auth/session injection is not genuine login E2E. If canvas has no supported secure entry surface, record the blocker and implement an approved dev-only vault-fillable bridge instead of bypassing auth or requesting secrets in chat. A status-200-only
check is the exact failure that ships a broken link to the user. When
the user's browser still shows the old error after a server-side fix,
tell them to retest in incognito or hard-refresh first — the Unity
error page caches aggressively. When trust is low, attach a
screenshot of your own passing load instead of log excerpts.

## 13. Missing runtime assets and Git-LFS pointers

A clean clone can be uncompilable even though CI was green:

- **Gitignored third-party libs**: a rule like `LeanTween/` leaves
  `Assets/LeanTween.meta` tracked but the directory empty — 30+ scripts
  then fail with `LeanTweenType not found`. Restore the library from its
  upstream tag (Framework + Editor only; skip Examples/Tests/Docs) and
  fix `.gitignore` rather than re-adding a vendored copy manually each
  time.
- **Unfetched LFS objects**: a git-hosted package (e.g. LiveKit) stores
  binaries via LFS; without `git-lfs` the UPM cache contains 130-byte
  pointer files and the build fails with thousands of `CS0246/CS0400`.
  Install `git-lfs` on the build machine and re-resolve packages, or
  fetch the 15 objects from the GitHub media endpoint and verify `sha256`
  per file before overwriting the cache. Never commit the pointer blobs.
- **Large Drive zips for legacy assets**: when fonts/images are shipped
  as `Assets.zip`/`raw.zip` on Drive, the default python may have no
  `pip` (uv-venv) — retry auth checks with the Hermes venv python
  (`/usr/local/lib/hermes-agent/venv/bin/python`) which has the Drive
  scope. Copy missing assets with `rsync -a --ignore-existing` (preserve
  `.meta`) and never overwrite existing `.cs`/`ProjectSettings`/`manifest`;
  new files under `.gitignore` will not appear in `git status` but must
  still be counted via `find … | wc -l`. Overlay raw (`raw/overlay/<type>/`)
  may live only inside `raw.zip` while local `raw/overlay/` is empty
  (gitignored) — list zip contents before declaring the input missing, and
extract the overlay subtree when present.

## 14. Pet/Addressables CDN platform split

The player bootstraps `Addressables.LoadContentCatalogAsync` from
`PukiwoConfig.bundleCdnBaseUrl + "/<Platform>/catalog_latest.bin"`.
Building for WebGL while the URL still resolves to
`StandaloneWindows64` loads the wrong compression/format and the login
screen renders without fonts or pet bundles. Fix `ResolveCdnCatalogUrl`
to branch on `Application.platform == RuntimePlatform.WebGLPlayer` and
fall back to the legacy JSON pipeline when no WebGL bundle has been
published yet. Publishing WebGL bundles is a separate step — build them
from `pokiguard_pet_pipeline/builder` (the `WebGL` opt-in mode) and
atomic-deploy only the `WebGL/` folder on the `pukiwo-cdn:9090` host;
never touch the live `StandaloneWindows64/` folder. Verify with
`curl -s -o /dev/null -w "%{http_code}" https://cdn.pokiguard.com/pet-bundles/v1/WebGL/catalog_latest.bin` = 200 before rebuilding the player.

## 15. Addressables batching and stale script refs

Two failure shapes that both look like "build succeeded but the game is broken":

- **Finalize once, not per item.** Building Addressables items one by one with
a finalize per item rewrites the catalog every time — only the last item
survives and every earlier bundle is orphaned. Bake + register all items
first, then run a single finalize so one catalog references everything.
- **Major package upgrades orphan prefab script refs.** A UGUI 1.x → 2.x bump
changes script GUIDs; prefabs saved under the old version keep stale GUIDs
and the player logs `referenced script is missing` on objects that look fine
in source. Hunt them mechanically: extract every `guid:` from the scene,
check each against `.meta` files (project plus `Library/PackageCache`) — a
GUID with no `.meta` anywhere is orphaned. Delete the orphaned prefab and
its scene instance (safe when the instance is inactive and nothing else
references it); leave the living components on the same object untouched.

## 16. Android APK signing: debug key installs, keystore pins identity

A debug (`Development Build`) APK is self-signed and installs fine from a direct download — no custom keystore is needed to ship a testable build. A custom keystore matters only for upgrade continuity: the same key overwrites cleanly, a different key fails with a signature conflict and forces the user to uninstall first (local data lost). Before building a product APK, locate the key that signed the previous release (Player → Publishing Settings → keystore path on that machine); reuse its file + alias, or tell the user one reinstall is required. Sign with `apksigner sign --ks <key.jks> --alias <alias> app.apk` and verify with `apksigner verify`.
