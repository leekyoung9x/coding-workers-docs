# Proactive reporting (Lead watchdog)

Rule learned from production sessions: the user expects the Lead to report
WITHOUT being asked.

- When a worker finishes (background completion notice arrives), verify
  immediately in the SAME turn: check the log tail, run the real check
  (open the public link, log in, screenshot), then report the result.
  Never end a turn with "worker still running, I'll watch it" and then
  go silent until the user asks again.
- If the user sets a reporting interval (e.g. every 5 minutes), keep it:
  check process + log growth + live URL each interval and post a short
  status even when there is no result yet.
- "Done" means verified on the SAME surface the user looks at
  (public link, their phone), with a screenshot attached — never declare
done from local-only green tests while public still shows the old bug.
- If a dispatched brief produces no log growth for ~15+ min (muse) or the
  process is gone with no result file, declare it stuck, kill it, and
  re-dispatch split smaller — don't let it sit for 30 min hoping.
