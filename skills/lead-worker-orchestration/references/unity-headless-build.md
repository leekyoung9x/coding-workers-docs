# Unity Headless Build (GPU-less VPS) — Lead-side rules

Class: setting up and running Unity Editor batchmode builds on a Linux VPS without GPU, and serving the WebGL output. Proven on Ubuntu 26.04 + Unity 6000.0.26f1 (Hub 3.22.0, module `webgl`).

## 1. License lives per Linux user — run the build as that user

Unity Hub's activated Personal license is stored under the user that clicked through the GUI (`~/.config/unity3d/Unity/licenses/`), NOT system-wide. A probe run as root reports `No valid Unity Editor license found` even when the license is valid for another user.

- Rule: every Unity invocation (import/check/build) MUST run as the licensed user (`su -s /bin/bash <user> -c '...'`). Never run Unity as root.
- The Editor install itself must be reachable by that user: do NOT install under `/root` (mode 750 blocks others). Install to `/opt/Unity` and symlink from both homes.
- Hub is an Electron app: headless CLI needs `xvfb-run -a unityhub --no-sandbox -- --headless <cmd>`. The distro package provides only `/usr/bin/unityhub` (no `unity-hub`); wrap it if briefs reference the other name.
- Old patch versions vanish from `editors -r`; install with the exact `--changeset` from `ProjectSettings/ProjectVersion.txt` after verifying the tarball URL returns HTTP 200.
- After GUI activation: tell the user to disconnect RDP, NEVER log off / log out of Hub (logout returns the Personal license).

## 2. Old Unity version + newer URP assets need a build-time shim, not re-saved assets

When the repo's URP assets were saved by a newer editor than the build machine's, `URPBuildDataValidator` throws `BuildFailedException: ... is not at last version` and URP never upgrades forward. Fix with an `Assets/Editor/` `IPreprocessBuildWithReport` shim (lowest callbackOrder) that clamps only the in-memory serialized version fields to what the running URP expects — a no-op when versions already match. Document it as a stop-gap; the durable fix is building with the editor version the project targets.

## 3. Voice/mic packages die on WebGL — guard, don't hand-patch the cache

`UnityEngine.Microphone` does not exist in the WebGL audio module, so any package calling it (e.g. LiveKit `MicrophoneSource.cs`) fails with `error CS0103`. And `Library/PackageCache/` is wiped on every re-resolve, so a manual edit there is not durable.

- Keep the game class compiling on WebGL as a no-op stub (`#if !UNITY_WEBGL ... #else stub ... #endif`) so callers don't break — never delete the class on WebGL.
- Patch third-party package sources with an `Assets/Editor/` script that re-applies the guard on editor load + before build (idempotent via marker comment), never a one-off cache edit.
- Guard every callsite that references the stubbed types, or WebGL compile still fails at the caller.

## 4. Worker sequencing: never mutate Assets/ while Unity builds

Do not move/delete assets while a build owns the project lock. Verify actual owned Unity executable/project/start fingerprint through the supervisor; `pgrep -f` can select brief text or the monitoring shell. Wait for lock release before cleanup, and never let cleanup start a competing Editor. Preserve active builds and do not kill by a broad argv regex.

## 5. No progress percentages — report position, not %

Unity batchmode logs have no total step count, so any % is fabricated. When asked for progress: report the last log line, process elapsed time, and which phase the log indicates (project open / compile / IL2CPP / brotli compress) — plus the historical duration of that phase when known. Never invent a percentage.

## 6. Serve pre-compressed WebGL correctly, and self-verify before asking the user to test

- Unity emits real brotli (files carry the `UnityWeb Compressed Content (brotli)` marker). The server MUST send `Content-Encoding: br` with correct `Content-Type` per file type (`application/wasm` for `.wasm.br`, `application/javascript` for `.js.br`); without the header the browser reports `Unable to parse Build/*.br`. Verify with `curl -I -H 'Accept-Encoding: br'` + one `--compressed` download that decodes to valid JS — never report success on HTTP 200 alone.
- Behind a CDN proxy, Let's Encrypt HTTP/TLS challenges fail (CDN returns 403 for the challenge path): pause proxying until the certificate is issued, or use DNS challenge.
- After every rebuild: `chmod -R a+rX build/webgl` (build runs as the licensed user; the web server reads as another) before declaring the deploy live.
- Flow: fix headers yourself, curl-verify headers + decoded body, THEN ask the user to hard-refresh. An HTTP-200-only check before asking the user to test is what causes a false `done`.
