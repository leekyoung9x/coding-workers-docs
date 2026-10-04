# Dispatch Reliability — Field Lessons

Read with the main protocol before every dispatch. These are failure modes observed
in production; each rule prevents a repeat.

## 1. Brief written is NOT brief dispatched
- After writing a brief file, launch the worker IN THE SAME TURN and confirm the
  background session started (session_id / pid). Two separate incidents: brief file
  sat for hours because the launch command never ran and nobody verified.
- Report back proactively when a worker completes — same turn, with acceptance
  evidence. Never wait for the user to ask 'done yet?'. The user explicitly demands
  push reporting; polling-by-user is a Lead failure.

## 2. Match launcher, worker type, and effort exactly
- `mini` is mini-SWE-agent (`/root/.local/bin/mini -t "$(cat BRIEF)" -y`) — it is NOT
  a muse `--reasoning-effort` value. `run_muse_worker.sh` accepts only
  none|minimal|low|medium|high|xhigh|max|ultra.
- Keep the brief filename prefix consistent with the launcher (BRIEF_MINI_* → mini,
  BRIEF_MUSE_* → muse). A mismatch silently runs the wrong agent or fails usage.
- Size the effort to the task: one-line CSS/logic fixes go `low` or mini, never `max`.
  A max brief costs 15–25 min of full pipeline (read + fix + tsc + build + vitest +
  playwright + pixel-measure) regardless of fix size.

## 3. Exit codes lie — verify deliverables, not exit status
- mini workers routinely exit 1 (`action was not executed / Aborted`) AFTER completing
  all work. muse workers exit 0 on thin reports. Neither proves anything.
- Acceptance = deliverable exists (route returns 200, file on disk, test counts from
  a fresh run you trigger) + numbers you measured yourself (pixel diff, response
  codes). Never report 'done' from a log tail alone.

## 4. Watchdog hung models by CPU + log, not wall-clock alone
- Hung signature: log stuck at startup warnings for 30+ min while process CPU time
  keeps rising (utime increases across 10s samples, zero log lines). Kill it and
  re-dispatch a SMALLER brief (tool-only or render-only split), not the same brief.
- One transient `transport error / server_error ... retrying` is normal; silence
  after retries is not — check, don't hope.

## 5. Dev-server ownership during worker runs
- Do NOT start/restart Vite (or any port-bound dev server) while a worker runs:
  the worker's own test/build steps fight for the port (EADDRINUSE) and kill/steal
  the server. Verify the server AFTER the worker exits, never during.
- If the server dies mid-run, check `port in use` first — a second live server often
  already serves traffic; starting a third changes nothing.

## 6. Tool-first beats fix-by-hand (the 5-times rule)
- When a ground-truth source exists (Figma REST, DB, API), brief the TOOL to fetch
  it; forbid hand-drawn fallbacks/placeholders/mask in the same brief. Five
  consecutive 'no hand-drawing' rules were all bypassed through 'temporary /
  fallback / placeholder' wording — ban those words in briefs, require
  warn-plus-empty when art is missing.
- When the worker lacks credentials the Lead holds (tokens, MCP), the Lead runs the
  fetch step directly and hands the artifact to the worker — don't brief the worker
  to do something its session provably cannot (verified by env/MCP absence checks).
