# Weekly Event Settle + Gift Pipeline (brief rules)

Use when the brief involves event rewards, leaderboard settle, or scheduled distribution.

1. Gift-only distribution: route every gift-mappable reward through the gift pipeline (PENDING gift + UNIQUE ledger + event log + shared ref `<event>:<period>:top<rank>`). Never write directly to player inventories or wallets on the settle path — direct writes create copies nothing reads plus double-credit when the gift is later claimed. Require the worker to grep-prove zero direct writes on the settle path.
2. Freeze the scoring metric in the brief: name the exact column or source plus the formula (current value minus period snapshot). Forbid proxy metrics (win counts, derived aggregates) unless explicitly approved — a worker left alone substitutes whatever is easiest to query.
3. Freeze content: list exact reward numbers and tiers in the brief and forbid inventing quests, items, or tiers. New content needs user approval before it is added.
4. Keep one-shot exceptions one-shot: a late first-period start (or any period exception) is a data fix for that period only, marked as such in code comments. Never change the recurring job schedule to implement it.
5. Prefer in-process settlers over external cron when claiming requires auth: if the settle endpoint needs a login session behind bot protection, run the settler as a BackgroundService inside the game server (poll loop, idempotent DB guard) instead of cron plus a cookie file. Never hardcode secrets in the repo.
6. Require blocker escalation in every prod brief: when the worker finds a correctness violation or a dirty prod tree, it stops and presents options (fix-first, safe-subset, or explicit risk acceptance) instead of porting as-is.
7. Verify cover art against real game assets: AI-generated covers drift (wrong boss, wrong colors) — compare the render with the actual item/pet icons or CDN art and confirm palette and subject before shipping. For image generation through the gateway, use the image endpoint with SSE accept header (never the chat path) and vision-check the decoded result.
