# Sending images (screenshots, renders) into the Discord chat

A reply that only says "đã chụp" or prints a file path shows the owner **nothing**. When the owner
asks to see a picture, the image must arrive as a Discord attachment, and you must confirm it did.

## The only form that attaches a file

Put a bare `MEDIA:` directive on its own line in the final reply:

```
MEDIA:/root/.hermes/cache/screenshots/pvp_arena.png
```

- Absolute path, no quotes, no spaces, one file per line. Images, audio and video all work.
- Do NOT use `![alt](file:///...)`, a bare path, or a `SHOT:` string from a tool: Discord shows them as
  plain text, the owner sees no image (observed).
- Put at most 2–3 lines of text with it. The image leads, the verdict follows.

## Where the file must live (this is what silently fails)

The gateway only delivers files under allowed roots. A path outside them is dropped and the owner
gets a ❌ reaction with **no message at all**. Gateway log (`~/.hermes/logs/gateway.log`) shows:

```
WARNING Skipping MEDIA directive path (denied by the delivery policy): <path>
ERROR   [Discord] response_delivery_dropped: non-empty response ... produced no delivered message
```

Always save screenshots to **`/root/.hermes/cache/screenshots/`** (create it with `mkdir -p`) and send
from there. Anything under `~/.hermes/cache/` is allowed. `~/.config/browser-harness/tmp/` is allowed
only when listed in `gateway.media_delivery_allow_dirs` of `~/.hermes/config.yaml`; do not rely on it.

Recipe after a browser/Unity screenshot:

```bash
mkdir -p /root/.hermes/cache/screenshots
cp "<path the tool printed>" /root/.hermes/cache/screenshots/<task>_<what>.png
ls -l /root/.hermes/cache/screenshots/<task>_<what>.png   # must exist and be > 10 KB
```

## Check the picture is real before sending

A 3 KB PNG is almost always blank or an error page. Check size and that it is not a single colour; if it
is, re-take the shot instead of sending it:

```bash
python3 - <<'PY'
from PIL import Image
im = Image.open("/root/.hermes/cache/screenshots/<file>.png").convert("RGB")
cols = im.getcolors(maxcolors=1 << 20)
print(im.size, "distinct colours:", len(cols) if cols else ">1M")   # < ~20 colours = blank
PY
```

## Verify delivery, do not assume it

After the reply, a missing image shows up in the gateway log, not in your tool output:

```bash
grep -E "Skipping MEDIA|response_delivery_dropped" /root/.hermes/logs/gateway.log | tail -3
```

If either line mentions your path, the owner did not get the image. Copy it into
`/root/.hermes/cache/screenshots/` and resend. Never answer "đã gửi" while the log says dropped; when the
owner says they cannot see it, check this log first instead of resending the same path.

## Do not end the turn with only a tool call or only `MEDIA:`

Reply text that consists solely of a `MEDIA:` line which gets dropped leaves an empty reply. Always add one
sentence of text next to the image so the message is delivered even if the attachment is refused.
