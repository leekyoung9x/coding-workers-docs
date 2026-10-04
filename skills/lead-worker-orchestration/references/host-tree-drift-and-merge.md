# Host-tree drift: diff both directions before any deploy

Scenario: a service runs on a host whose source tree was hand-edited (no git repo there), while a local
repo holds a "clean" copy. A deploy brief that replaces the host tree with the local commit can silently
delete live features — and the mirror-image case, a host lacking repo features, lands a DB fix inert
because the running container still ships the old bundle.

## 1. Cheap pre-brief check (one SSH call)

```bash
wc -l <host tree's main files>          # server.js / app.js / index.html
# compare to the local repo's same files
grep -c 'data-page="<tab>"' <host index.html>   # nav entries
```
A host tree that is `fatal: not a git repository` plus a line-count gap (e.g. host `server.js` 892 vs
local 877, `app.js` 5258 vs 4682) is the signature of two divergent copies.

## 2. Two-sided enumeration, symbol-level (not line counts)

```bash
# host-only and repo-only files
find <host-tree> -type f | sed 's|^<host-tree>/||' | sort > /tmp/host.txt
find <repo-tree> -type f | sed 's|^<repo-tree>/||' | sort > /tmp/repo.txt
comm -23 /tmp/host.txt /tmp/repo.txt    # host-only  ⇒ could be deleted: enumerate and justify each
comm -13 /tmp/host.txt /tmp/repo.txt    # repo-only  ⇒ must also be ported
# function/symbol level, over exported names or a feature grep
comm -23 <(grep -rhoE '^(export )?(async )?function [A-Za-z0-9_]+' <host-tree> | sort -u) \
         <(grep -rhoE '^(export )?(async )?function [A-Za-z0-9_]+' <repo-tree> | sort -u)
```

For every path that exists on only one side, state **whether it is live** and what it does. A host-only
file list can include entire features (two admin tabs with their own `/api/admin/*` route sets), and a
repo-only list can include the fixes the deploy was supposed to ship.

## 3. Decision rule

- Any host-only live feature ⇒ the brief is a **MERGE**, never a replace: the host files are the base,
  add only the new block in a position that cannot collide, and put each host-only feature into the
  acceptance criteria (their routes must not 404, their nav entries must still count 1), with an explicit
  line that trading them away is forbidden.
- Any repo-only feature the target needs ⇒ the deploy carries those fixes too; say so instead of
  presenting the change as one small edit.
- Instruct the worker to **stop rather than proceed** when files disappear under it: halting with
  "this overwrite deletes two live features, here are options A/B" is the gate working.
- Close the loop afterwards: pull the host's final files back, commit them so repo == host, verify zero
  diff — otherwise the same trap fires on the next deploy.

## 4. When the owner says the finding is incomprehensible

"k hiểu m nói gì, đề nghị giải thích kỹ hơn" means the deliverable is an owner-facing write-up, not a
re-run of the diff. Use an analogy (two near-identical copies of the same page, and the build reads the
outer one), name the concrete symptom a player/owner would see ("the page still shows one bench"), list
the files that exist in only one copy with what each does, and finish with two options as choices —
never a raw path list.
