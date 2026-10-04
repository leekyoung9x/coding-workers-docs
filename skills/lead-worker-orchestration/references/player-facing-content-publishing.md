# Player-Facing Content Publishing (news / how-to / patch notes on the product site)

Depth for the step after drafting player-facing copy: getting it live on the official site and proving it
renders. Complements the copywriting rules in SKILL.md (no dev jargon, canonical in-game names).

## 1. Recon the CMS before writing anything

Do not assume an admin UI is the path, and do not assume the content format. Settle four facts first:

```sql
DESCRIBE <articles_table>;                       -- columns, lengths, nullability
SELECT id, slug, <category_col>, is_published, published_at
  FROM <articles_table> ORDER BY id DESC LIMIT 10;   -- how existing posts look
SELECT id, <title_col>, CHAR_LENGTH(<content_col>) FROM <articles_table> ORDER BY id DESC LIMIT 5;
```

Also grep the app source for how it reads that table (`src/lib/<articles>.ts`, the detail route): it reveals
- **the content format** — Markdown vs HTML vs plain text (this decides whether you escape or author headings),
- **valid category values** (an enum map in code, not free text),
- **what "published" actually means** — usually `is_published=1` AND a non-null `published_at`, since listing
  pages sort by `published_at DESC`,
- **whether the admin API requires a session** — if it does, direct INSERT is the correct path for an agent.

Match the existing rows for every field you are unsure about (e.g. if all current posts leave `cover_url` NULL)
rather than inventing a value such as a CDN URL for an image that does not exist.

## 2. Derive every number in the article from the live DB, never from the plan doc

Plan documents drift from the shipped configuration. Before writing, query the live config and use exactly
those values: reward tiers, shop prices and limits, per-day caps, recipe requirements, unlock conditions.
Any figure you cannot confirm with a query is **omitted** from the article — an absent detail costs nothing;
a wrong number generates support tickets and erodes trust.

Useful shape for the "how to earn" section:

```sql
SELECT <tier_col>, <requirement_col>, <reward_json_col> FROM <tier_table> WHERE <feature_key>='<f>' ORDER BY <tier_col>;
SELECT <name_col>, <price_col>, <limit_type_col>, <limit_qty_col> FROM <shop_table> WHERE <feature_key>='<f>';
```

Caps and reset rules usually live in application code, not the DB — grep the handler module for the cap
constant and the period rollover before stating "per day" or "resets at".

## 3. Never document a flow you know is broken

A how-to that sends players into a flow whose progress is not recorded is worse than no article. Check the
flow's own progress rows for real users first (`references/live-event-data-integrity-audit.md` §1): if a step
produces zero rows for everyone who performed it, the article omits it or labels it under repair, and the
report states which item was withheld and why. Re-check this immediately before publishing, because a fix may
have shipped in between.

## 4. Insert directly, idempotently, with a backup

- **Backup first**: `mysqldump --skip-lock-tables <db> <articles_table>` into a timestamped dir, print `ls -la`.
- **Slug is the idempotency key** (it is UNIQUE): check `SELECT COUNT(*) ... WHERE slug=?` before inserting, or
  use `INSERT ... ON DUPLICATE KEY UPDATE`. A re-run must not create a second copy of the same article.
- Set `is_published=1` and `published_at=NOW()` explicitly; leaving `published_at` NULL hides the post from
  listings even though the row exists.
- Rollback is two deletes by slug — write the exact statements into the report.

## 5. Stage-2 gate: prove it renders on the live site

A row in the CMS is not a published article. Verify through the running app, from inside its container so the
check does not depend on external DNS or CDN state:

```bash
docker exec <web_ct> wget -qO- --timeout=10 http://127.0.0.1:<port>/<list-route> | head -c 500
# no rendering rules are proven by the list page alone — fetch each detail route and grep for strings that
# only exist if the markup was actually rendered (a heading from the body, not just the title field)
docker exec <web_ct> wget -qO- --timeout=10 http://127.0.0.1:<port>/<list-route>/<slug> | grep -c '<distinctive body text>'
```

Then confirm the home page still returns 200 (a malformed article can break a shared layout), and that the
listing count grew by exactly the number of posts you inserted.

## 6. Report

Include per article: slug, inserted id, category, character count, `is_published`/`published_at`, the live-render
command output verbatim, the list of DB values quoted in the copy (so the Lead can spot-check a few against the
live DB), which items were withheld due to known bugs, and the backup path plus the two rollback deletes.
