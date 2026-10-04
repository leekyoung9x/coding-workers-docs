# Brief anti-loopholes, watchdog, and completion reporting

Companion to the Lead–Worker protocol: lessons from rounds where correctly-briefed
workers still produced hand-drawn stand-ins, died silently, or finished without the
user being told.

## Ban fallback language in the brief itself

A worker takes the cheapest route to the numbers you wrote. Any permitted escape hatch —
"temporary", "fallback", "placeholder", "mask", "draw it for now", "keep layout with code" —
becomes the delivered product (measured: five consecutive rounds each shipped a hand-drawn
stand-in through exactly such a clause). Write the rule as: missing art = render NOTHING +
one `console.warn` per missing key + a `MISSING ART` list naming the exact Figma nodes.
Forbid the escape words literally in the brief's CẤM/never section, and add a grep-able gate
(e.g. zero hits for the banned words in `src/`, a fixed graphics-object count) so a
stand-in fails acceptance instead of passing it.

## Separate render-style from art replacement in the brief

Strokes, text outlines, and border gradients are render style; panels, characters, icons,
and backgrounds are art. State per item which class it belongs to and where the numbers
come from: style values must cite a measurement from the source art (colour stops, weight,
position), never an invented constant. A worker handed only a fixture with empty style
fields will invent the numbers — so a fixture that lacks a field is itself a defect to fix
(re-export or re-measure), not a licence to guess.

## Never assert a style fact from MCP output alone

Figma MCP (`get_design_context` / `get_metadata`) can drop or simplify style fields:
observed more than once, a Linear gradient stroke reduced to a solid `border-[#...]`,
and raw metadata omitting strokes/fills/effects entirely. The canvas the designer drew
(Appearance panel: Linear, Outside, Weight) is ground truth, never the MCP output.
Cross-check via screenshot of the Appearance panel or the in-Figma Plugin API
(`node.strokes`, which preserves gradient stops) before asserting "solid" / "no stroke",
and never argue a style fact against the design owner from MCP-derived code alone.

## Watchdog silent workers; do not discover death from the user

A worker process can die (timeout, SIGTERM, transport reset) with only a one-line launcher
note. Poll the process table plus the brief log on a timer while anything is dispatched;
when it exits without a result, re-dispatch promptly. The user asking "is it done yet" is
the failure signal — it means the watchdog did not exist.

## Report completion in the same turn, unprompted

The moment a worker's completion notice arrives, verify (re-run the suites, re-measure the
symptom, screenshot) and report changed / verified / left immediately — never end the turn
waiting for the user to ask. A status-only reply with no verification attached reads as a
stall when the work is unfinished.

## Lead never touches code — including one-liners

Even a "trivial" deletion or constant tweak goes into the next brief, not into a direct
edit. Foreground patches by the lead bypass the brief's gates, break the blame trail, and
the user reads them as role violation. When a past lead edit caused the current symptom,
say so by name in the reply and put the revert in the brief.
