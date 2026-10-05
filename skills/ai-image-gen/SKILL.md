---
name: ai-image-gen
description: Generate images via 9Router text-to-image for Hermes and AI.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [image-generation, 9router, text-to-image, cdn]
    related_skills: []
---

# AI Image Generation via 9Router

Generate images with `cx/gpt-image-2.5-sunburst` through the local 9Router
text-to-media endpoint, then upload to CDN. Used for game icons, skill icons,
and event art.

## When to Use

- User asks to generate/redraw game icons, skill icons, or event images.
- Any worker brief needs AI-generated PNG art.
- Don't use for: code tasks, non-image media, or when the user supplies art.

## Prerequisites

- 9Router running on `http://127.0.0.1:20127` (local) or
  `https://router.cutes1tg.online` (remote).
- Key in `$HERMES_CUSTOM_ROUTER_CUTES1TG_ONLINE_API_KEY` (from `/root/.hermes/.env`);
  never print it, never write it into docs.
- Model: `cx/gpt-image-2.5-sunburst`.

## How to Run

Call through the `terminal` tool with curl (Cloudflare blocks Python urllib,
so never use urllib/requests against the public URL; local 127.0.0.1 needs no
special User-Agent):

```bash
curl -s -m 300 -X POST http://127.0.0.1:20127/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -H "Accept: text/event-stream" \
  --data-binary @payload.json -o out.sse
```

Payload: `{"model":"cx/gpt-image-2.5-sunburst","prompt":"...","n":1,
"size":"auto","quality":"auto","background":"auto","output_format":"png"}`.
Response is SSE; extract `"b64_json":"..."` and base64-decode to PNG.
Reference script: `/poki/ops/m149-gen-icons.py` (batch + SPEC prompts).

## Procedure

1. Write the prompt: subject centered, style keywords (gaming icon / square
   framed skill slot + rarity border color), `no text`, background rule
   (transparent for item icons, dark framed background for skill icons), size.
2. Generate via curl above; decode b64 to PNG. Completion: file exists and
   `file` reports PNG with alpha (or opaque for framed skills).
3. Verify with `vision_analyze`: subject centered, no text, readable at 48px.
4. Upload to CDN via admin API (same path, same filename to overwrite) and
   bump `?v=` in DB `icon_url`; backup the DB rows + sha256 first.
5. Verify: CDN URL returns HTTP 200 with matching byte size; page shows 0
   broken images.

## Pitfalls

- `xq/gpt-image-2.5-sunburst` is DEAD on XQAPI ("model not found"); always use
  the `cx/` prefix via 9Router, never call XQAPI directly.
- Image models don't answer on `/v1/chat/completions` (capability mismatch) —
  use `/v1/images/generations`.
- 9Router needs the model in `MODEL_ROUTES_JSON` (xq-inject) or it returns
  `No live route`; it resolves `xq-inject` via /etc/hosts — restart the
  9router service after hosts changes.
- Cloudflare caches old bytes ~4h: always change `?v=` on overwrite, never
  test the bare URL.
- Keep icon taxonomy apart: `item-icons/v1/` (bag, transparent) vs
  `skill-effect-icons/v1/` (in-battle, framed). Never mix them.

## Verification

- CDN URL: HTTP 200, byte size matches local file.
- `vision_analyze`: centered subject, no text, fits its slot style.
- DB `icon_url` carries the new `?v=`; backup + rollback SQL on disk.
