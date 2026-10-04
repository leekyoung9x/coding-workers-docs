# Review Briefs and Current-State-First Documents

Depth for two related jobs: (a) dispatching a worker to review a document/spec the owner was handed, and
(b) authoring a standards document that must describe the system as it is BEFORE describing where it moves.

## 1. The failure that motivates both

A green-field architecture document reads as authoritative while describing a system nobody has: a stack the
project does not use, a directory layout that will become the third parallel copy, library versions that are
mutually incompatible, and rules that contradict the existing exporter, naming convention and test gate. The
owner's rejection is not "this is wrong", it is **"write the current state, the current naming, the real source
tree — THEN describe the migration target."** Treat that as a standing rule for every standard/architecture doc
in this project class, and as the shape of the review that precedes it.

## 2. Review-brief rules (worker vs document/spec)

- **Bind the brief to what the source asserts, not to your suspicions.** Every suspected defect you cannot
  quote is a wasted cycle; the reviewer's most valuable output becomes the section refuting you. Correct shape:
  "audit these N sections against the live codebase; every defect must cite the source's own line number;
  every improvement must cite the project path or measured number that motivates it."
- **Require a line number per defect** and, for any claim about an external library/API/version, a named
  verification source plus an honesty label — `VERIFIED`, `INFERRED`, or `CANNOT VERIFY (offline)`. Never let
  "cannot verify" become an invented version or an invented API.
- **Defect floor + omission floor.** "≥ N defects in the document, ≥ N omissions against the repository, ≥ N
  concrete improvements (of which ≥ 3 must carry a code/config snippet)" converts a vague "review this" into a
  countable deliverable you can accept or reject mechanically.
- **A review brief is read-only, and its whitelist is one new report file.** Ban edits/creates/deletes anywhere
  else, git writes, installs, builds, deploys, service restarts, DB writes and test-suite runs. Add the warning
  that sibling workers are writing the same tree, so measured counts may shift mid-run.
- **Demand the same headings you will count**: findings / omissions / improvements / verification table /
  phased plan / risks / reverse questions / verdict. A verdict line ("usable as-is / usable after N fixes /
  needs a rewrite") is what makes the report actionable instead of advisory.
- **Forbid reading images and files over ~100 KB** in a review brief; a document review that opens a minified
  bundle or a 200 KB evidence PNG dies on the request-size limit instead of finishing.

## 3. Current-state-first document layout

Order is the deliverable. A reader must be able to follow it top to bottom without wondering which parts exist:

1. `## 0. How to read this` + the evidence-label convention.
2. `## I. CURRENT STATE` — **descriptive only: no recommendation may appear in this section.** Subsections that
   earn their place every time: stack/runtime; how rendering/output actually works today; the generator/exporter
   and its real output fields; naming convention with measured counts; the real source tree and which copy is
   live; assets; the existing test gate; measured technical debt. Acceptance check: section I contains zero
   occurrences of "should / propose / need to change".
3. `## II. GAPS`, each with a number.
4. `## III. MIGRATION TARGET` — one block per item, six fixed lines: current state (with evidence) / target
   (marked `DOES NOT EXIST YET` where true) / why / work items naming real files / measurable criterion /
   rollback. Ban a target that cannot name the file it will touch.
5. `## IV. Rules` — every engineering rule phrased against the EXISTING naming tokens and JSON fields, never
   against invented ones.
6. `## V. Phases & risks` — per phase: files touched, measurable criterion, rollback.
7. `## VI. Evidence appendix` (command → result) and `## VII. Reverse challenges for the Lead`.

- **Mandatory labels** to demand in the body: `[EVIDENCE: <cmd> → <result>]`, `[DOES NOT EXIST YET]`,
  `[CANNOT VERIFY]`. They make fabrication visible instead of plausible.
- **Count the evidence lines as acceptance** (`grep -c '\[EVIDENCE'`): a document claiming a current state
  without evidence lines is a green-field document wearing section headers — the same defect the owner just
  rejected, one layer down.
- **Architecture decisions that change cost belong to the owner.** Where the realistic options are materially
  different (keep the existing renderer / add the new engine only where it pays / replace the whole UI layer),
  the document states all options with cost and consequence and is forbidden to pick one. Same for which of two
  parallel source trees survives.

## 4. Field techniques for mapping an existing tree

Cheap commands, run by the Lead as brief input, that turn "the current state" from prose into measurement:

- **Naming census from the real export** — load the exported JSON in a script and `Counter` the first token of
  every node name, plus `node type` distribution. Print ~20 lines, never the file. The counts are the argument:
  a conventional token appearing in 4 of 464 nodes proves the feature the document mandates is unused; a token
  the old convention document never lists proves the convention is already out of date.
- **Which source tree the build really compiles** — the generated type declarations are authoritative and small:
  grep the import path inside `.next/types/**/<route>/page.ts`; if it is absent, read the framework's route
  manifest. Then confirm in the RUNNING container (`docker exec <ct> grep -rl -F <marker> /app/.next`), because
  "the host tree looks like X" is not "the container serves X".
- **Dead code proof** — `grep -rn <dir> <candidate-roots>` returning empty, plus zero markers from that copy in
  the build output, is the pair that proves a subtree ships nowhere. Two weakened forms are not enough on their
  own: "no import found" and "looks unused" are hypotheses; "no import + no build marker" is a finding.
- **Two parallel copies: compare token sets, not line counts.** Strip comments from both files, take the
  identifier sets, and diff — then check which side's unique identifiers appear in the build. The interesting
  answer is usually that the copies implement *different mechanisms* (one an image-copy optimisation, one a
  render-state hook), not that one is a newer version of the other; saying "old vs new" mis-describes the system
  and mis-aims the dedup work.
- **Version from build markers, never from a bare `grep -o`** — a minified bundle carries version strings inside
  deprecation messages for many releases at once, so a naive grep reports several versions and the wrong one.
  Find the module's own version constant (for a pixi-style bundle, the assignment next to its init marker) and
  report the string with its surrounding context.
- **Library compatibility is a peer-dependency question** — read `peerDependencies` of every proposed package and
  compare against the version the project actually ships; a runtime requiring a newer major than the vendored
  copy is a blocking finding, not a detail. Check the licences too: a permissive-looking package can be
  "no charge" and a runtime can require a paid editor.

## 5. Anti-patterns to name in the report

- Documents that quote a stack the repo does not use (`vite` in a Next.js project), or that mandate a directory
  layout while the repo already carries two parallel copies of it — the target becomes copy number three.
- Sample code that omits the parameters which make the example work (anchor, the second axis on resize,
  the slice margins of the very component the section is about). Audit the document's code blocks as code.
- A rule that contradicts the section above it: check every rule the document mandates against the document's
  own data model, and require the reviewed document to state a single source of truth when an older internal
  convention already exists (grep the new tokens in the old convention file — a count of 0 means the two
  standards cannot both be followed).

## 6. Proving a read-only review stayed read-only on a shared tree

When several workers write one tree, `find -newermt <dispatch time>` cannot attribute anything — it returns
every sibling's files, so it certifies nothing. Attribute by the two facts that are unambiguous:

1. **Immutable baseline hash**: hash the artefact under review before dispatch and re-hash after. Unchanged
   proves the review did not touch its own source, regardless of who else is writing.
2. **Window inventory with a name column**: list every file created/modified inside the run window and read it
   as a list; once the one whitelisted file is removed, every remaining path must belong to a sibling worker you
   can name (`pgrep -af <worker-binary>` gives their briefs). Print that residue in the report.

- Also confirm the worker process is gone before accepting (`ps -eo pid,etime,args | grep <brief-name>`): a
  worker still running after its report can rewrite what you just verified.
- If the review brief changes a number, re-measure it yourself for the three or four most load-bearing facts
  (the build's own declarations, the running container's bundle, library peer ranges from the registry). The
  rest can stay as cited claims — but say which ones you re-measured and which you did not.
