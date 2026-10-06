---
name: visual-worker-orchestration
description: "Use when a worker builds visuals from MCP or reference art."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
---

# Visual Worker Orchestration

For tasks where a worker builds visual output (game art, animation, Spine rigs)
using a local MCP server and/or a user-supplied reference image.

## 1. Wire local MCP servers before spawning

- Keep `schema_version: 1` in `~/.config/muse/settings.json`; validate with `jq .` after edit.
- Two transports: stdio (`command`, `args`, `env`) for local processes, `streamable_http` (`url`, optional `headers`) for local HTTP servers.
- Set `mode: "optional"` on any server that can be down (missing licensed binary, not yet started) — a `required` server aborts the whole run when it fails.
- Start HTTP servers first with their own env (port, asset root), health-check the endpoint, then spawn the worker pointing at it.
- Chromium running as root refuses to launch without `--no-sandbox`: wrap the browser binary in a script adding the flag and point the server's browser env var at the wrapper (needed for headless preview/GIF/screenshot tools).
- Pass reference art directly: `muse exec ... --image /abs/ref.png` so the worker sees it instead of working from a text description.

## 2. Brief rule: cut, don't redraw

When the user supplies source art, state explicitly in the brief: crop real pixels from the image (record crop coordinates per part in VERIFY.md) and FORBID redrawing approximations. Workers default to hand-drawn shapes and self-report them as sourced — never accept the claim on words alone.
- When the sheet holds several art variants (splash art, parts panel, animation previews), name the exact source panel and the expected body proportions in the brief — workers silently pick the wrong variant (e.g. chibi parts instead of the thin splash hero) and report it as done.
- Persist user-supplied chat attachments into the workspace immediately — attachment URLs expire and re-download fails later; when expired, ask the user to re-upload instead of reconstructing from memory.

## 3. Accept on images, not on self-report

- Inspect the atlas/sprite sheet and an idle-stance screenshot yourself; the screenshot is ground truth.
- Region-attachment orientation bugs (e.g. a weapon held backwards) come from a mismatch between the sprite's drawn orientation in the atlas and the `x/y/rotation` offset in the rig JSON — compare the two, fix the offset, regenerate any embedded asset bundle, re-screenshot idle to confirm.
- Downscale images to ≤640px before sending to `vision_analyze`; full-size sheets time out.
- For one-line data fixes, patch the file directly as Lead instead of spawning another worker round-trip; back up the original first.
- Deliver proof images and demo video as `MEDIA:/absolute/path` lines so the chat renders them as attachments — `file://` markdown image links render as empty frames on the recipient side. Keep media under ~10MB (downscale first) and verify video with `ffprobe` (duration/size) before announcing it.
