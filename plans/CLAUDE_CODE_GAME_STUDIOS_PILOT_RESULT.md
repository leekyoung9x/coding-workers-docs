# [CC] Game Studios — Isolated Pilot Report

**Date:** 2026-10-25
**Classification:** **EXTRA STUDIO PILOT** — an additional, isolated experiment. It does **not**
replace or modify the AB22 tooling work (which remains separate and untouched).
**Verdicts:** `installed: PASS` · `configured: PASS` · `smoke: PASS` · blockers: **none**

---

## 1. What was asked, and what was actually done

| Requirement | Result |
|---|---|
| Clone/pin upstream into an isolated pilot workspace | ✅ pinned at `05ad7c8a` (v1.2.0) |
| Keep vendor reference clean; adaptations in a separate trial copy | ✅ `upstream/vendor` untouched (git status clean), all edits in `trial/` |
| Read README, LICENSE, CLAUDE.md, project.yaml, settings, agents/rules and **ALL** executable hooks before enabling | ✅ 18 hooks / 5,542 lines read, incl. the 2,152-line `yaml-helper.sh` library |
| Record **actual** counts, not marketing counts | ✅ 49 agents, 74 skills, 18 hooks, 35 scripts, 14 rules — counted |
| Inspect for destructive / network / secrets behaviour | ✅ exactly one network call, zero destructive ops, zero secret reads |
| Never overwrite Poki CLAUDE.md / project.yaml or adopt into the live game | ✅ untouched |
| Install as a project-local usable Claude pilot | ✅ discovered and exercised |
| Isolated HOME / CLAUDE_CONFIG_DIR with credential inherited in env, never printed | ✅ `CLAUDE_CONFIG_DIR` is native to CLI 2.1.295; no credential in any artifact |
| If isolated nested run not feasible → mark blocked | ✅ **not blocked** — isolated nested run worked while PID 4119553 was live |
| Agent model selection inherits the current session; report the diff | ✅ 19 agent + 74 skill pins → `inherit`; diff is exactly those 93 lines |
| Minimal document rigor **but** retain mandatory tests and user visual acceptance | ✅ `rigor: minimal` + all five `testing.strict.*: true` (compensating control) |
| Studio creative agents must not invent/modify game content | ✅ banner rule; smoke was read-only |
| No second authoritative task store / no director hierarchy over Hermes | ✅ nothing introduced; Hermes remains lead |
| Clarify 49 agents ≠ 49 workers, and hooks ≠ OS security | ✅ stated in `CLAUDE.md` banner, `PILOT.md`, and here |
| Document Pixi limitations, don't invent support | ✅ `engine.name` left unset; zero Pixi claims |
| Run upstream static/hook tests if safe | ✅ skill-lint on both copies; hooks exercised directly and in-harness |
| Bounded Claude skill/agent discovery + one harmless task in a fixture | ✅ 49 studio agents / 125 slash commands; ran `/project-stage-detect` read-only |
| Validate hook errors and config resolution | ✅ blocking, pass-through, and malformed-input paths all tested |
| No push, no broad kill, no credential logging, no 49-agent launch | ✅ none performed |

---

## 2. Upstream facts (pinned)

| Field | Value |
|---|---|
| Repo | https://github.com/Donchitos/Claude-Code-Game-Studios |
| Commit | `05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418` |
| Subject | Release 1.2.0 — the main path, rebuilt and tested |
| Date | 2026-10-19T13:09:09+11:00 |
| License | **MIT** — Copyright (c) 2026 Donchitos (`upstream/vendor/LICENSE`) |
| Shape | a **project template** (`.claude/` + docs), **not** a global plugin |

### Actual inventory (counted from the clone)

| Kind | Count |
|---|---|
| Agents (`.claude/agents/*.md`) | **49** |
| Skills (`.claude/skills/*/SKILL.md`) | **74** (186 files with references) |
| Hook scripts | **18** |
| Helper scripts | **35** |
| Rule documents | **14** |
| Studio self-test files | 129 |
| Total files (excl. `.git`) | 633 |

---

## 3. Layout

```
/poki/tooling/game-studios-pilot/
├── upstream/vendor/     pristine clone @ 05ad7c8a  (never modified)
├── trial/               adapted, usable pilot copy  ← launch here
├── home/                isolated HOME + CLAUDE_CONFIG_DIR (sessions, no credentials)
├── logs/                raw run logs + pre-adaptation snapshot for the diff
└── bin/set-skill-model.sh

/poki/docs/reports/game-studios-pilot/
├── REPORT.md            this file
├── status.json          machine-readable status
└── evidence/            discovery init, skill-lint, smoke outputs, model diff
```

---

## 4. Security review of the executable surface

### 4.1 Network

**One** outbound call exists in the entire framework: `hooks/update-check.sh`
does `GET https://api.github.com/repos/Donchitos/Claude-Code-Game-Studios/releases/latest`
(curl, 10 s timeout; wget fallback), caching at
`$XDG_CACHE_HOME/claude-code-game-studios/latest-release` once per day.

**Mitigation applied:** `updates.check: false` in the trial's `project.yaml`
(verified resolving to `false`). All other scripts: zero network calls.

### 4.2 Destructive operations

None found. No `rm -rf`, `mkfs`, `dd`, `truncate`, `shred`, or `>/dev/` in any
hook or helper. The shipped deny list additionally blocks ~130 patterns
(recursive `rm`, forced/`-f` `git clean`, `git reset --hard`, forced pushes,
`sudo`, `chmod 777`, PowerShell equivalents). **These were verified as actually
applied by the harness** — the debug log shows
`Adding 130 deny rule(s) to destination 'projectSettings'`.

### 4.3 Secrets

No reads of `.env`, `~/.ssh`, `id_rsa`, `.aws`, `.npmrc`, `netrc`. The deny list
blocks `Read(**/.env*)` and `Edit(**/.env*)`. No credential was printed, copied,
or written into any artifact. The auth probe output contains only token counts
and the model name.

### 4.4 What the hooks can actually refuse

Only **4 of 18** can exit 2 (refuse). Everything else is advisory:

| Hook | Event | Can refuse? |
|---|---|---|
| `validate-read.sh` | PreToolUse:Read | **yes** — whole-file read of a design doc > 40 KB |
| `validate-commit.sh` | PreToolUse:Bash | **yes** — staged data file is invalid JSON / JSON check cannot run |
| `validate-assets.sh` | PostToolUse:Write\|Edit | **yes** — feeds invalid-JSON errors back to the model |
| `validate-push.sh` | PreToolUse:Bash | code path exists; shipped config only **warns** |
| the other 14 | — | no — advisory/logging only |

> **Hooks are not OS security.** Any of these is bypassed by a differently-shaped
> command, a direct file write outside the tool layer, or `--bare`. Treat them as
> guardrails and lint, never as enforcement. The genuinely enforced layer is the
> harness deny list (§4.2), and even that is a permission list, not a sandbox.

### 4.5 Review coverage honesty

Read in full before enabling: all 18 hooks (5,542 lines) and `statusline.sh`.
Exercised in the harness: `SessionStart` (both), `PreToolUse:Read`, `Stop`,
`PostToolUse` (directly). **Not triggered in the smoke** (static review only):
`SubagentStart`, `SubagentStop`, `Notification`, `PreCompact`.

---

## 5. Adaptations (trial copy only)

| # | Adaptation | Diff scope |
|---|---|---|
| A1 | 19 agent `model:` pins → `inherit` (30 already inherit) | 19 lines |
| A2 | 74 skill `model:` pins → `inherit` (66 sonnet, 5 haiku, 3 opus) | 74 lines |
| A3 | `project.yaml`: name, stage Concept, `rigor: minimal`, `automation: collaborative`, `session_state: on` | config |
| A4 | **`testing.strict.{logic,integration,visual,ui,config}: true`** | config |
| A5 | `updates.check: false` | config |
| A6 | `CLAUDE.md` 7-point pilot banner + honest engine line | docs |
| A7 | `PILOT.md` added | new file |
| A8 | `engine.name` deliberately **unset** | config |

**Model-routing diff — the whole of it:**

```
19 agent lines:  model: sonnet|opus  ->  model: inherit
74 skill lines:  model: sonnet|haiku|opus  ->  model: inherit
0 other lines changed  (verified by diffing against logs/pre-adaptation/)
```

No `opus` / `sonnet` / `haiku` pin remains anywhere in `trial/.claude/agents`
or `trial/.claude/skills`. Full list in `evidence/model-diff.txt`.

### A4 is the important one

`modes.rigor: minimal` expands to `qa.level: minimal` — and upstream documents
that level as **waiving test evidence** (`coding-standards.md`: *"Not waived at
`qa.level: minimal` — tests are, the look is not."*). Since Poki requires tests
**and** user visual acceptance to stay mandatory, all five `testing.strict.*`
gates are pinned `true`, which takes precedence over the `qa.level` default.
Verified through upstream's own resolver:

```
qa.level              -> minimal        (from rigor)
testing.strict.logic  -> true
testing.strict.integration -> true
testing.strict.visual -> true
testing.strict.ui     -> true
testing.strict.config -> true
```

This is **minimal document rigor with no relaxation of QA** — exactly the
required shape.

---

## 6. Smoke evidence

### 6.1 Discovery (bounded)

Isolated run with `HOME`/`CLAUDE_CONFIG_DIR` under the pilot; credentials
inherited from the environment (never printed).

| Check | Result |
|---|---|
| Studio agents discovered | **49** |
| Total agents visible | 58 (49 studio + 9 inherited from `/poki/.claude`) |
| Slash commands | 125 |
| Studio skills confirmed | `gate-check`, `project-stage-detect`, `qa-plan`, `scope-check`, `skill-test`, `start`, `team-qa`, `story-done` |
| Model | `thtung-paid` — **unchanged** |
| MCP servers | none |

### 6.2 Functional task (harmless, read-only)

`/project-stage-detect` in the trial — explicitly instructed to decline any write
and spawn no subagent.

- **Result:** success, 13 turns, 79 s, model `thtung-paid`.
- It resolved `rigor: minimal → workflow: minimal, docs.density: terse`.
- It reported configured stage `Concept` vs observed `Concept`, verdict CONCERNS,
  and — notably — **itself flagged the unset `engine.name`** as a deviation it had
  to decide empirically, rather than papering over it.
- **No file was written** (`production/project-stage-report.md` absent — verified).

### 6.3 Hook enforcement proven in-harness

A deliberate 64 KB design doc + an instruction to read it whole:

```
PreToolUse:Read hook error: [.../validate-read.sh]:
Read refused: design/_guardtest.md is 64 KB, over the 40 KB bar ...
```

The refusal reached the model; **no content was delivered**. `SessionStart`
(both hooks) and `Stop` also fired. This is proof the hooks are wired and
effective — not merely present on disk.

### 6.4 Direct hook tests

| Test | Expected | Observed |
|---|---|---|
| `validate-read` unbounded >40 KB | refuse | **exit 2** ✅ |
| `validate-read` bounded (offset+limit) | pass | exit 0 ✅ |
| `validate-read` non-watched path | pass | exit 0 ✅ |
| `validate-read` malformed JSON | fail open | exit 0 ✅ |
| `validate-commit` broken JSON staged | block | **exit 2 BLOCKED** ✅ |
| `validate-commit` valid JSON staged | pass | exit 0 ✅ |
| `validate-assets` broken JSON | report to model | **exit 2** ✅ |
| `validate-push` force-push to main | warn only | exit 0 + warning ✅ |
| `validate-write` project.yaml | advisory | exit 0 ✅ |

### 6.5 Static checks

`skill-lint.sh all` on **both** copies: 74/74 skills, **0** frontmatter
failures, **0** name mismatches. The `check1` rows are **byte-identical** between
vendor and trial — the model rewrites did not disturb any frontmatter.

---

## 7. Conflict review (Matt Pocock / Beads / Superpowers)

- **Matt Pocock skills** — installed separately by AB22 into the shared config.
  This pilot adds no competing copy and no second skill root.
- **Beads** — **not introduced.** No second authoritative task store was created;
  the existing Poki task flow remains the only one.
- **Superpowers** — untouched; nothing here overrides it.
- **Director hierarchy** — `creative-director`, `technical-director`, `producer`
  are **Claude-internal subagent roles**, not a chain of command over Hermes.
  Hermes remains lead; this is stated in the trial's `CLAUDE.md` banner.
- **49 agents ≠ 49 workers** — they are Markdown role prompts, idle until a skill
  spawns one. No 49-agent unattended launch was performed or attempted.

---

## 8. Pixi limitations (stated, not invented)

Poki's client is **PixiJS (TypeScript)**. Upstream supports **Godot / Unity /
Unreal only**:

- `engine.name` enum is exactly `Godot|Unity|Unreal` (`yaml-helper.sh:547`).
- Code-root and test-root rules are per-engine (`src/`, `Assets/`, `Source/<Module>/`).
- Engine-specialist agents exist only for those three engines.
- **Zero** occurrences of "pixi" in the whole repository.

Consequences: `engine.name` is left **unset** (setting any value would misdeclare
the engine and trip engine-reference mismatch warnings). Engine-agnostic skills
(planning, review, QA planning, scope, sprint) are usable with their
engine-specific paths treated as placeholders. **No Pixi support is claimed.**

---

## 9. Known caveats

1. **Project-root ambiguity.** Nested Claude walked upward and also discovered
   `/poki` as a project root, merging 9 `permissions.allow` entries from
   `/poki/.claude/settings.local.json` with the trial's 3. Upstream's hooks are
   project-root-resolved and were proven to run from the trial root, so the
   pilot's behaviour is correct — but the merged allow-list is worth knowing
   about. Nothing in `/poki/.claude` was written.
2. **Hook coverage is partial** (§4.5) — four events were not triggered.
3. **Trust dialog.** In `-p` mode the workspace is untrusted, so
   `permissions.allow` entries are ignored until trust is accepted. For the
   isolated run this was set in the *isolated* `.claude.json` only. Interactive
   first use will prompt normally.
4. **`model: inherit` on skills** is not the upstream-documented use (upstream
   documents `inherit` as agents-only). It is syntactically valid and is what
   removes the tier override; upstream's own `skill-lint` passes all 74 skills.

---

## 10. Rollback

The pilot is self-contained. Nothing outside `/poki/tooling/game-studios-pilot`
and `/poki/docs/reports/game-studios-pilot` was written.

```bash
# Full removal (pilot only)
rm -rf /poki/tooling/game-studios-pilot
rm -rf /poki/docs/reports/game-studios-pilot
```

To keep the evidence but drop the runnable pilot, remove just the trial and home:

```bash
rm -rf /poki/tooling/game-studios-pilot/trial
rm -rf /poki/tooling/game-studios-pilot/home
```

Nothing to undo in `/poki/.claude`, `/root/.claude*`, `/root/.hermes*`, the Poki
`CLAUDE.md`/`project.yaml`, or any application source — none were modified.

---

## 11. Exact launch instructions for the trial

**Interactive (project-local discovery):**

```bash
cd /poki/tooling/game-studios-pilot/trial
claude
```

**Isolated config (recommended while other writers hold the shared config):**

```bash
cd /poki/tooling/game-studios-pilot/trial
HOME=/poki/tooling/game-studios-pilot/home \
CLAUDE_CONFIG_DIR=/poki/tooling/game-studios-pilot/home/.claude \
claude
```

**Non-interactive smoke (safe, read-only):**

```bash
cd /poki/tooling/game-studios-pilot/trial
HOME=/poki/tooling/game-studios-pilot/home \
CLAUDE_CONFIG_DIR=/poki/tooling/game-studios-pilot/home/.claude \
claude -p "/project-stage-detect" \
  --allowedTools "Read,Glob,Grep,Bash(bash .claude/hooks/yaml-helper.sh *)"
```

**Re-run the validation without recreating the installer:**

```bash
cd /poki/tooling/game-studios-pilot/trial
bash .claude/scripts/skill-lint.sh all | head
bash .claude/hooks/yaml-helper.sh resolve_config --keys modes.rigor,qa.level,testing.strict.logic
bash .claude/hooks/detect-gaps.sh
```

> Launching from **inside** `trial/` is what loads its `.claude/` (hooks, deny
> rules, ask-first mode). Started elsewhere, the template itself warns that these
> do not load.

---

## 12. Bottom line

The pilot is **installed, configured and smoke-verified**, and it is honestly
scoped:

- It is an **extra studio pilot**, not a replacement for AB22 and not part of the
  live game.
- Hermes remains lead; the studio is a set of Claude-internal roles.
- Model routing is fully inherited — no hidden cost tier.
- Minimal document rigor, but tests and visual acceptance stay **blocking**.
- No Pixi support is claimed, because there is none.
- Hooks are guardrails, demonstrated working, but never described as security.
