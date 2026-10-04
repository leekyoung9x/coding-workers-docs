# Which Service Owns the Data (multi-backend repos)

Depth for the question "why is this framework/service here at all?", and for any plan that touches a table
more than one codebase can write. In this project the game backend is .NET microservices over one MySQL schema
while the web app (Next.js) also holds an ORM and 40-odd API routes against the SAME database — so a general
question about the web layer is really a question about ownership.

## 1. When to run this before writing anything

- The owner asks "why is <framework> here?" or, one turn later, "why are BOTH <framework> and <backend service>
  here?" — the second question is the real one and it is about the boundary, not about the framework.
- A plan proposes changing/adding a UI or runtime layer, or a framework rewrite. Count the boundary FIRST; a
  framework decision made without it will be wrong (the incumbent may own nothing the rewrite needs, or everything).
- Any brief whose feature writes rows on an event/economy/progress table (wallet, ledger, daily counter, quest
  progress, item grants) — those are the tables a second writer silently corrupts.
- Before telling the owner a rule/threshold "lives in" a module, confirm the module that actually serves it.

## 2. The three measurements that answer it

```bash
# (a) which services run, and which schema each connects to
docker ps --format '{{.Names}} | {{.Image}} | {{.Ports}}'
docker inspect <ct> --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -i 'ConnectionStrings\|DB_'

# (b) what the web framework forwards instead of handling (proxy/ingress wiring)
grep -n -A12 'rewrites\|routes\|basePath' next.config.* ; grep -rn 'reverse_proxy' <proxy config>

# (c) per-table writer census across BOTH trees — the decisive table
for t in <table1> <table2> ...; do
  printf '%-22s backend=%s  web=%s\n' "$t" \
    "$(grep -rl "$t" <backend-tree> --include=*.cs | wc -l)" \
    "$(grep -rl "$t" <web-tree>/app/api --include=*.ts | wc -l)"
done
```

Render (c) as a table — `table | writers on each side | verdict` — and say which side's count is 0. That single
column is what makes the boundary visible; a prose description of "the web app also has an API layer" is not.

## 3. The rule: one table, one writer

- Classify every shared table by domain, not by who happened to code it first: game/economy/progress
  (wallet, ledger, daily counter, quest progress, item grants) → **backend service owns**; web-only concerns
  (payment order records, notifications, wardrobe/cosmetics, browser-session tables) → **web app owns**.
- Tables with non-zero writers on BOTH sides are the risk surface and are named explicitly in the report — the
  money/progress ones first. Two writers on one ledger means the two flows are not in a transaction together,
  so a rule change on one side silently diverges from the other, and the same bug has to be patched twice.
- **Enforce it mechanically, or it is prose**: a spec/gate that fails when a file under the web API tree names a
  backend-owned table (`grep -rl '<owned-table>' app/api` → must be empty) plus the mirror check that the backend
  does not write the web-owned tables. A rule nobody can run is not a rule.
- The web framework legitimately keeps its own roles — server-rendered pages, SEO/metadata, rewrites, session
  cookies, forms, webhooks. Say which of those it keeps, so "stop querying game tables" does not read as
  "stop being a web server".

## 4. "Do we have to rewrite the game queries?" — no, and say why in measured terms

The expected answer is **not** a rewrite: the owning service already has the query/repository layer for its own
tables (grep its query classes/services first — `grep -rln '<table>' <backend>/**/Queries <backend>/**/Services`
— and the event/economy logic with its daily cap and per-instance idempotency usually already lives there).
What changes is much smaller:

1. Web layer stops issuing its own statements against backend-owned tables.
2. It calls the backend instead — the existing server-to-server channel (header-authenticated, secret read from
   the container env at call time and never printed) where one fits, or one purpose-built endpoint the backend
   adds for the web flow (score + signature in, backend computes the payout, applies the cap, writes the ledger).
3. Web layer keeps writing only the tables it owns.

So the deliverable is "delete duplicated query code + one integration call", not "re-implement the game data
layer". State the size of each half honestly — the second half is what the owner fears.

## 5. Pitfalls

- **Answering the owner's second, sharper question with the same inventory.** After "why is A here?" comes
  "why are A and B both here?" — repeating what A does is how the owner concludes you cannot see the problem.
  Lead with the boundary and the shared schema, then the consequence, then the fix order.
- **Inferring duplication from identical table names alone.** Grep the counts first; a table named on both sides
  can still have exactly one writer (one side reads only). Report the direction of the writes.
- **Planning renderer/UI work while a money table has two writers.** Ownership outranks UI, and the owner says so;
  put the ownership decision earlier in the roadmap than any visual work.
- **Treating a shared database as shared ownership.** It is the opposite: a shared schema is exactly why explicit
  ownership has to be declared and enforced.
- **Quoting a service's name as the answer.** Name the container, the port, the connection string's schema, and
  the tables it owns; "the backend handles it" is not verifiable.

## 6. Owner-facing shape

Number the consequences, name the tables, and give the ordering (ownership → then UI). Where the choice is
his (which side owns a genuinely ambiguous table), present it as an option with cost; where it is only an
engineering blast-radius question, take the conservative option and report what was and was not included.
