# Worker Watchdog and Independent Acceptance

## When to use

Attach a watchdog in the same turn as each worker dispatch. For this recovery workflow cadence is 3 minutes; completion/new-result events request immediate verification instead of waiting for next tick. Use `references/worker-supervision-and-gates.md` as the enforcement contract.

## Procedure

1. Record task/run/attempt, owned PID/PGID or unit, start fingerprint, stage/deadline and exact output paths. Create watchdog with installed CLI schema, explicit model/provider for LLM jobs, workdir, skills and concrete delivery destination. Quote `"every 3m"` as one argument.
2. Cheap no-agent monitoring reads durable supervisor state. Do not discover/kill processes from task text in argv. Heartbeat/CPU/log growth are liveness only; progress needs a verified checkpoint.
3. One tick without progress: inspect stage/child/wait reason and take a documented action. Two unchanged ticks: STALLED, diagnose or controlled stop under ownership/deadline rules. A valid compiler/link child inside its deadline is not killed for quiet logs.
4. New artifact/completion: claim acceptance lock, independently rerun exact tests/measurements on same build/environment, inspect new screenshots for visual claims. Worker exit 0/report PASS only means IMPLEMENTED, never ACCEPTED.
5. Record ran/pass/fail/skip, artifact/hash, failure-cause confidence and next action. Preserve unfinished patches and fixture cleanup. At most two attempts with same unexplained failure signature before BLOCKED and diagnosis, never blind respawn.
6. Pause/transfer per-task watcher after terminal verified verdict; preserve history. Mission controller continues unresolved dependencies until user's whole deliverable is verified or explicitly blocked. Do not remove monitoring just because a report exists.

## Reporting

Report `stage | new verified evidence | blocker | action already taken`, at most ten lines for routine ticks. Say NO_PROGRESS if no checkpoint. Never invent percentages, ETAs or signal senders; SIGTERM/SIGKILL identify signals, not causes.

## CLI and limits

Load current `hermes cron create/edit --help` before changes. Notice syntax: `hermes cron create [options] schedule [prompt]` takes `schedule` and `prompt` as POSITIONAL arguments (e.g. `hermes cron create [flags] "every 3m" "Watchdog prompt"`). Passing `--schedule` or `--message` causes CLI parsing errors (`unrecognized arguments`). Do not hardcode obsolete claims that model/provider pins cannot be edited. No-agent scripts cost no inference; monitor gates suppress unchanged LLM runs. Verify actual scheduler behavior/delivery with a real run. These primitives need tested adapters; they do not automatically own arbitrary dedicated CLIs.

## Verification

Failure-inject wrong child exit, stale PID, cleanup-pattern collision, duplicate dispatch, quiet valid build, heartbeat-only stall, stale PNG, false visual PASS and verifier rejection. A watcher only reporting green text or treating an exited job as alive fails its own acceptance.
