# Watchdog Cron + Evidence-Only Status (every worker dispatch)

Every worker dispatch (muse/mini/glm/codex/agy) gets a watchdog cron at spawn time — never later, never on request.

## Procedure

1. Spawn the worker, note the start time.
2. Immediately create the cron: `hermes cron create --model <model> --provider <provider> --name "watch-<BRIEF>" --deliver origin "every 5m" "<prompt>"`. Pass model+provider AT CREATION — a job created without them runs under stale config and fails every tick.
3. The watchdog prompt checks, in order: worker process alive (pgrep) → log tail (byte count + last lines) → artifact/report file exists → direct re-measurement of the target state (DB SELECT / HTTP status), never log text alone. Cap the report at ~10 lines.
4. Terminal states: report file exists → report final numbers once; no process + no log change for >10 min + no report → report the stall immediately.
5. Remove the cron when the worker finishes (`hermes cron remove <job-id>`) so it never spams.

## Status answers to the user

- Cite only fresh evidence: process start time vs now, log byte count and whether it moved, last measured numbers. Never infer progress from elapsed time since spawn.
- If the log has not moved for 10–20 min while the process lives, say so plainly, state the next action (kill + respawn with a narrower brief), then execute it in the same turn.

## Pitfalls

- Report completion only after an independent re-measurement matches the worker's claim — self-reports of "done, all numbers verified" have been wrong on the numbers, because the check that produced them is the same one that produced the work.
- Before reporting any compensation/refund complete, verify coverage against the FULL catalog (every tier/lever per group), not just the rows the worker touched — partial-tier payouts pass the worker's own checks and fail the player's.
- A cron created without model/provider cannot be repaired by editing it later; delete and recreate it with both flags from the start.
