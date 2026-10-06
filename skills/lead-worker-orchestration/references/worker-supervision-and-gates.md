# Worker supervision and acceptance enforcement

Use for recurring worker deaths, false PASS, stalled leads, and regressions after repeated dispatches. These are requirements for a tested supervisor/gate, not a claim that writing this document implements them.

## Durable lifecycle

Persist task/run/attempt/environment, source commit plus dirty patch hash, PID/PGID and start fingerprint, model/provider/effort, stage/deadline, last verified checkpoint, child exit, cost cap and artifact hashes. Separate QUEUED/PREFLIGHT/RUNNING/IMPLEMENTED/VERIFYING/ACCEPTED from BLOCKED/FAILED/STALLED. Only an independent verifier certifies ACCEPTED. Preserve partial patches/checkpoints before retry; one writer per shared file and one build lock per Unity project/cache.

## Safe launch and stop

Return the child exit code; a final echo otherwise makes the wrapper exit zero. Test child exits 1 and 137 as negative controls. Do not detach unmanaged children inside tracked background calls. Capture stderr and durable exit records.

Do not kill by matching task text in argv: a brief containing Editor/Unity can cause broad pkill to select its own mini worker. Probe executable/ancestry/start fingerprint and stop only owned processes. Treat signals as signals, not diagnoses; require supervisor/kernel/cgroup evidence before attributing OOM. Two attempts with the same unexplained failure signature trigger BLOCKED and diagnosis.

Preflight brief integrity, workspace, toolchain, license user, disk/build lock, port/headers and a real provider chat request. Observe budget caps; no silent paid-provider fallback.

Enforce task command restrictions at the supported worker environment/tool-execution boundary before launching a subprocess; a safe supervisor does not constrain shell tools issued by its child. Test the actual environment.execute path with a stub executor so forbidden raw signals, broad cleanup loops and destructive commands never run. A lexical command guard is defense-in-depth, not a hostile-code sandbox; report residual bypasses and use OS permissions/isolation for hard boundaries. Reject rather than merely log a forbidden call, and provide tested owned-process helpers for long jobs. Workers attempting detached background executions (`nohup ... &` or raw daemonization) get intercepted by execution guards (`POLICY_REFUSAL[detached_child]`); brief them to use the supervised owned-process adapter (e.g. `wkctl owned-run start --name <job> --command '<cmd>'`) so background work retains ownership markers, PGID lifetime tracking, and clean signal control. Do not respawn a client job that violated the process ban until the guard is exercised.

Command guard regexes must not anchor paths with `^/`: line anchors miss redirection targets (`echo x > /etc/...`, `tee /proc/...`) and tokens in pipelines; scan tokens across the command line. Block `/proc/self/environ` and `/proc/*/environ` uniformly. Relaunching a task in `STALLED` state must require an explicit `--retry` and `--retry-reason`; launchers must not auto-populate a retry reason for stalled tasks. When launching a worker through a wrapper script that replaces its process image (`os.execvpe`), background process trackers may report completion (exit code None); inspect `/proc/<pid>` and start ticks before treating it as dead.

## Progress and immediate verification

Heartbeat proves liveness only. Count verified checkpoints: exact-symptom RED, falsified hypothesis, new compiled artifact, or executed gate. Reading HEAD/startup logs is not progress. On a 3-minute tick without checkpoints inspect stage/child/wait reason. Two unchanged ticks require intervention; respect valid compile/link deadlines. Completion or a new result wakes independent verification immediately.

Use cheap no-agent monitoring for unchanged states and event-gated LLM interpretation with self-contained context. Existing durable queue/cron primitives can help, but external mini/muse need a tested status/ownership adapter; do not assume native Kanban automatically manages those CLIs.

## Red-capable evidence

Use a fresh directory/run_id per run; bind PNG/result/trace timestamps and hashes to the same build/environment. Existing images cannot satisfy a failed later run. Assert real click plus modal-specific render evidence: isOpen, file size and whole animated-canvas differences are insufficient.

Test the tester with disabled entry button, invisible active modal, stale image, failed login, injected console error, missing required case, child failure and forbidden production endpoint; each must fail for the named reason. Separate unit/layout, integration and real authenticated E2E. Sample-data editor renders and diagnostic direct-handler hooks do not certify an entry-point click. In-engine diagnostic callers (e.g. `SendMessage('Btn_ChinhPhuc', 'OnClick')`) are forbidden in live E2E paths; if invoked, the harness must fail or mark the step `DIAGNOSTIC_HOOK_USED` and block dependent gates.

Evidence files listed in test manifests must be stat-verified (`os.path.isfile` and non-zero size); fabricated or missing paths in cases.json must fail closed. Region ink assertions (details, costs) must require meaningful floors (e.g. `ink >= 0.02 - 0.05`), never `> 0.0` which passes on single-pixel noise. Build hash checks must fail closed on unparseable values (treating `None` as a blocker). Modal layout verification must check row-by-row pixel continuity across all edges without gaps, tears, or console overlays obscuring interactive controls.

Preserve real exit status; no test piping through tail without pipefail. Print ran/pass/fail/skip and collected errors. Missing/skipped required tests cannot certify ACCEPTED. Isolate auth/API/WS/DB in dev, block production writes before dispatch, and keep real login in E2E. Build manifests carry source/dirty patch hashes and endpoints.

## Verify the mechanism

Failure-inject worker crash, provider outage, port conflict, stale evidence, process-pattern collision, false visual PASS and restart recovery. Report what the installed mechanism prevented; never describe a proposal as already enforcing it.
