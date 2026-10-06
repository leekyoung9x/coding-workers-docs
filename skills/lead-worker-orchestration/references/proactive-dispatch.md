# Proactive Dispatch + Watchdog Pairing

Applies whenever a worker is the obvious next step after a user request, a completed predecessor, or new evidence (log, screenshot, error).

- Dispatch in the same turn the need becomes clear — never end a turn with a promise to dispatch later, and never wait for the user to ask "did you dispatch yet". A user asking that means the protocol already failed.
- Create the watchdog cron in the same turn as the dispatch, with model/provider/deliver set at creation so it reports without manual repair. A worker without a live watchdog is an incomplete dispatch.
- When blocked on a genuine question (missing credential, ambiguous target, destructive scope), ask immediately instead of dispatching — but asking is the only acceptable alternative to dispatching, never silence.
- Report completion with verifiable artifacts (hashes, live-check output, screenshot MEDIA for UI claims), not with "worker says done" — the watchdog firing without artifacts is a STUCK signal, not progress.
