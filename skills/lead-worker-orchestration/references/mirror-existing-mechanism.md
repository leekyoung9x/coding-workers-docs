# Mirror the Existing Mechanism for Periodic/System Work

When a new periodic job, settler, reward pipeline, or system hook duplicates
something already running, MIRROR the existing mechanism — never build a
parallel one.

## Procedure

1. Before writing the brief, find the existing analogue: grep the codebase for
   the sibling (e.g. monthly settler when asked for a weekly settler, existing
   gift pipeline when asked for a new reward type).
2. Read its trigger, host binding, idempotency guard, and reward path end to
   end (trigger → config read → gift write → ledger/log → claim path).
3. Write the brief as a diff against that mechanism: same host, same trigger
   shape, same pipeline, same guards — only the schedule key and the reward
   numbers differ.
4. State the existing files to mirror by path in the brief so the worker
   reuses rather than reinvents.

## Pitfalls

- A web-layer cron/API that needs auth cookies dies to login walls (Turnstile,
  session expiry) while an in-process BackgroundService on the same host keeps
  running — prefer the mechanism that needs no external credentials.
- A reward that bypasses the established gift pipeline (direct item writes
  alongside gift rows) double-credits on claim — gift-mappable rewards go
  through gifts PENDING only, never straight to the inventory table.
- Verify a new item tier exists in the source table (SELECT before promising
  quantities) — a reward brief referencing a non-existent level ships nothing.
