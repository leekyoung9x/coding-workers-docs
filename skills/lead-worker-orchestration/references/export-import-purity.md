# Export-Import Purity (Figma → Runtime)

Rules for any brief that moves design assets into code. Complements the Lead–Worker role boundary: the Lead scopes and writes briefs, the worker implements.

- Report worker completion unprompted: when a completion notice arrives, verify (log tail + independent check) and report in the same turn — never wait for the user to ask for status.
- Never smuggle house rules beyond the user's order into a brief (e.g. stripping strokes/text styles unasked, inventing 'placeholder' styles): a worker executing a bad brief is the Lead's fault, not the worker's. When the user corrects invented scope, name the exact brief line that introduced it and fix that line.
- Art vs style split: exported ART (panels, pets, icons, backgrounds) renders as PNG at exact coordinates; STYLE (strokes, linear gradients, text outline/shadow) is drawn in code using values measured from the export — never export a PNG just to capture one stroke, and never draw shapes that replace art.
- Ban loophole words in briefs and code: 'temporary / fallback / placeholder / mask-instead / draw-instead'. Missing art = render nothing + one `console.warn` per key + a `THIẾU ART` list with exact node IDs; never draw a substitute.
- Every stroke/gradient number in a brief must cite its measured source (file + pixel range); numbers without a source are rejected at acceptance.
- Worker sessions without design-tool credentials cannot export: the brief must tell the worker to stop at step 1 with a `THIẾU TOKEN` report and zero edits, while the Lead (who holds the credentials) exports directly instead of re-briefing the impossible.
- Acceptance for visual work is pixel comparison against the user's own screenshot, not the worker's self-report: re-open the route, screenshot, and measure before claiming done.