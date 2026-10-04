# Auditing and Re-briefing a Browser Mini-Game Build

Use when the owner rejects a shipped mini-game / canvas game with a complaint of the shape "the games are all the
same", "I cannot do anything in it", "the art is just coloured dots", or "why didn't you use <reference>". The
deliverable is not reassurance — it is a measured audit plus a re-brief whose acceptance criteria make each of
those complaints mechanically checkable.

## 1. Verify the owner's complaint in the source before conceding OR denying it

Run the audit yourself (grep-level facts are brief INPUT, not deep recon) and quote the lines back. Four probes
settle the usual complaints in one pass:

| Complaint | Probe |
|---|---|
| "all games are the same game" | Read the game registry: count distinct **factory functions** vs entries. Three keys calling one `makeXGame(...)` under different labels IS one game. |
| "no real art / just coloured dots" | Count `Sprite` instantiations vs `Graphics` draws; count `Assets.load` calls; list the art directory that exists and is unused. |
| "I cannot click / drag anything" | Check `eventMode` is set per OBJECT (not only on the stage) and that each interactive object sets its own `hitArea`. |
| "no assets were generated" | Search the repo for any generated-art pipeline or cached output; absence is the finding. |

Report the finding as the probe result, not as an opinion — the owner's complaint is usually exactly right, and
saying so with the line number is what buys the re-brief its credibility.

## 2. Re-brief: separate the mechanisms, then gate them

- **One gameplay mechanism per game, one file per game, and a ban on sharing a gameplay function.** A falling-object
  loop may exist in exactly ONE game; the others must name a different mechanism (rhythm/combo on a fixed beat grid,
  aim-and-shoot with a trayectory, side-scroll dodge with an obstacle pattern, tile grid with swap/resolve). State
  the ban on reuse explicitly, or the cheapest implementation wins again.
- **Require real image assets loaded through the engine's asset loader**, and ban `Graphics` primitives for the
  primary game objects. If a generative-image tool is the intended source, the brief must name it AND carry a stop
  rule: if the tool is unavailable (no key/quota), STOP and report — do not raster placeholder shapes and then
  record the job as done. A worker that does exactly that will disclose it honestly, but only the brief's stop rule
  makes it visible before the report.
- **Interaction acceptance must be per game**: click/drag through the real page and assert the score changed from a
  known baseline (paste before → after per game), on desktop AND mobile. Coordinate events to the OBJECT with its
  own `hitArea`, and convert pointer coordinates through the element's `getBoundingClientRect()` — a CSS-scaled
  canvas makes raw pointer coords miss every target, which reads as "buttons do nothing".
- **Prove N games are N mechanisms in the acceptance**, not just N labels: N distinct files, N distinct factory
  functions, and one sentence per game naming its mechanism.

## 3. Grounding: run the reference research as its own parallel job

When the owner names an external showcase as the benchmark, a sentence in the implementation brief is not enough
(see the SKILL.md rule). Give the researcher a docs-only whitelist and a required artifact containing: a floor
count of concrete referenced projects each with its own URL, what technique is borrowed from each, the specific
module/file it will be applied to in THIS codebase, and an explicit "closed source, cannot inspect" where true.
Run it beside the build worker; fold its output into the next implementation brief.

## 3b. Pacing and scoring audit ("the games are too easy" / "I can just die and still get paid")

A mini-game can be mechanically correct, visually fine, and still be worthless because its **payout curve rewards
no skill**. Audit both halves before accepting it, and measure rather than opine.

**Difficulty ramp.** Read each game's constants and state the ramp as numbers before judging it:

```bash
grep -n 'diff\|spawn\|interval\|SPEED\|window\|elapsed' <game_dir>/*.ts
```

The recurring defect is a ramp that is too shallow and too slow: a normaliser like `diff = min(1, elapsed / 60)`
with a floor such as `0.7 - diff * 0.35` needs a full minute to reach maximum difficulty and never gets fast — so
an expert maxes the top payout band within seconds on every game. Required shape for a re-brief: reach maximum
difficulty in ~15–20s, lower the floor substantially, and add a second scaling variable (hazard spawn ratio, hit
window tightening, moving/smaller targets, limited ammo with reload) so difficulty does not hinge on one constant.

**Payout dead band.** Render the payout as a table against the score scale: if the top rung is `score >= 80` on a
`0..100` scale, then 80 and 100 pay identically and the honest description is "aim for the threshold, then stop" —
which the owner will summarise as "playing is pointless, you can even die immediately". Either add a top rung that
pays more, or make the payout continuous in the score. Present this as an owner decision with the resulting
per-day totals; the ladder is not the worker's to re-price.

**Zero-input payment.** A session is paid on a client-reported score inside a duration window (`>= MIN_DURATION_S`,
`<= MAX_DURATION_S`). That combination pays a perfect score for doing nothing — an idle player who never touches
the controls, or dies immediately, still clears the top band. Close it with three checks, all inside the signature
so the client cannot alter them: a **minimum real-interaction count** (no interactions ⇒ 0 payout even with a
perfect score), a **bounded duration window** (min raised well above a single frame, max cut from minutes to a few),
and a **physical ceiling on score-per-second** chosen loosely enough not to punish genuine play.

**Acceptance must be three simulated player profiles, before AND after**: expert (~0.25 s reaction), slow (~0.8 s),
and idle (zero input, full duration). Paste the before/after table per game. The idle profile paying `0` and the
expert profile no longer trivially clearing the top band are the two numbers that prove the fix; a report claiming
"difficulty increased" without that table is not evidence. Add the screenshots, since the owner judges those first.

## 4. Deploy proof (a mini-game repeatedly gets reported deployed while it is not)

- `docker inspect <container> --format '{{.State.StartedAt}}'` newer than the last build, AND the new asset
  answering through the public route: `curl -sI <domain>/<asset>.png` → `200 image/png`.
- "The route returns 200" is not "the game is reachable": count links from the page a player actually lands on
  (`grep -c '<new-route>' <event-page>`), and check the event is not admin-gated. Report built / deployed /
  findable as three separate claims, and say which one you verified.

## 5. Report shape

One screenshot per game delivered as chat media, the probe table from §1 as numbers, the per-game interaction
baseline→after, and a plain statement of what is still missing (missing art pipeline, missing entry point, missing
per-object hit areas). The owner judges the screenshot first, so never let a summary stand in for the images.
