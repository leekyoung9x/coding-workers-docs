# Cross-VPS Environment Discovery & Bootstrap

When synchronizing or bootstrapping multi-service projects across hosts:

## 1. Do Not Rely Solely on Git Clone
Git repositories only track committed source code. Production environments frequently contain critical untracked state:
- **Compiled binaries**: Pre-built runtime artifacts (e.g. `publish/` directories in .NET/Java/Go repos) ignored in `.gitignore`.
- **Dirty working trees**: Uncommitted bugfixes or configuration tweaks in active developer directories.
- **Persistent uploads & media**: User uploads, storage mounts, or runtime seed data (`uploads/`, `storage/`).

**Procedure:**
1. Inspect the source host's working tree for dirty/untracked files: `git status --short`.
2. Rsync the project directory with exclusions for heavy build artifacts:
   `rsync -avz --exclude='node_modules' --exclude='.next' --exclude='.git' user@host:/path/ /target/`

## 1b. Resolving a dirty working tree on the deploy target

A host that was originally synced by rsync/copy can later acquire a real repo whose worktree carries
uncommitted files from an earlier sync. `git pull --ff-only` then refuses, and a blind `git checkout`
destroys work — this is a legitimate stop condition for a deploy worker, so resolve it deliberately:

0. **Pre-flight probe before authoring the brief**: run `ssh user@target 'git -C /path/to/repo status --porcelain'`
   during Lead recon. Discovering dirty files before dispatching allows Lead to compare hashes and include the
   stash/sync instructions directly in the initial brief, preventing a worker abort and a redundant dispatch cycle.
1. **Compare before touching anything**: `md5sum` each dirty file on the target against the same path on the
   orchestrator host. Identical hashes mean the dirty state is a copy of work you already hold, not divergent
   work — safe to proceed. Divergent hashes mean someone edited on the target: STOP and ask the user.
2. **Back up, then stash**: tar the repo (or at minimum `git diff` + `git status --porcelain` output) into a
   timestamped backup dir on the target, then `git stash push -u -m '<label>'`; print `git stash list`.
3. **Fast-forward**: `git fetch`, then `git pull --ff-only origin <branch>`. A rejected ff-only means real
   divergence — stop rather than forcing a merge on a production host.
4. **Re-sync from the orchestrator instead of popping the stash**: rsync the source tree from the host whose
   worktree you hashed in step 1 (exclude `.git`, `.env*`, `node_modules`, `.next`, test artifacts, images).
   That single rsync restores the previously-dirty files AND the new commits together.
5. **Verify**: re-run the same `md5sum` comparison (previously-dirty files must still match) and grep for a
   symbol that exists only in the new code. Keep the stash as the rollback artifact; never `stash drop` it.

## 1c. Prove the artifact you ship actually contains the change

Publishing the artifact on the orchestrator and rsyncing it to the target is only half the job: the target's
Dockerfile usually just `COPY`s the artifact directory, so a stale or partially-synced artifact deploys
silently and reports success.

- Before shipping: `grep -ac '<new-symbol>' <publish_dir>/<Assembly>.dll` on the orchestrator (expect >= 1).
- After rsync: the same grep against the target path.
- After containers come up: the same grep inside the running container
  (`docker exec <ct> grep -ac '<new-symbol>' /app/<Assembly>.dll`), plus one rendered request that exercises the
  new code path.
- Record the pre-deploy image id of every service you rebuild
  (`docker inspect <ct> --format '{{.Image}}'`) so rollback is a tag change rather than a rebuild.
- Slim runtime images usually ship without `strings`/binutils, so grep the binary directly
  (`grep -ac '<symbol>' <dll>`) instead of piping it through `strings`; an empty `strings` result on a healthy
  binary is a missing-tool artifact, not evidence the code is absent.

## 1d. Deploying to a target that is many commits behind: ship the dependency closure, prove it four ways

A host that has not been synced for a while is not a candidate for a whole-tree replace. Deploy the **dependency
closure of the feature** and prove each boundary:

1. **Enumerate both directions.** `find <dir> -type f | sort` locally and on the host, then diff the lists.
   Strip `\r` from the SSH-captured side first — SSH stdout is CRLF, so `sort`/`comm` treat every host line as
   different and the diff reads as "everything changed": `... | tr -d '\r' > host-files.txt`.
2. **Hash the whole import closure, not just the files you intend to write.** For each file being shipped, resolve
   its imports and `md5sum` them on both sides. Every dependency must be **byte-identical**; a single mismatch means
   that file ships too, and a file that exists on one side only is a hard stop (the build fails, or worse, the
   container runs a half-applied feature).
3. **Classify the host-only hunks before calling it a replace.** `diff local host` and read every `>` line. If each
   host-only hunk is a **stale version of a function the repo already replaces** (an old hardcoded constant, an old
   reward path), a replace is correct and the host-only count is noise. If any hunk is a **feature that exists
   nowhere else**, the brief is a MERGE, never a replace.
4. **Remember the data layer and the code layer are two separate deploys.** A config/recipe row inserted for a
   feature whose code was never deployed is **inert**: the row is present, the API is unchanged, and the feature
   looks broken while every DB check passes. Verify both layers explicitly — the row *and* the symbol in the running
   artifact.

Proof is four numbers, pasted: container `StartedAt` newer than the last build; the new symbol present in the
running container's bundle (`docker exec <ct> grep -rl '<symbol>' /app/.next | wc -l` → `> 0`, or the equivalent
grep against the shipped binary); the public route answering `200`; and the unrelated baselines unchanged (neighbour
`COUNT(*)`, other containers' `StartedAt`). Tag the pre-deploy image **before** rebuilding so rollback is a tag
change, and locate credentials from the project's own access file rather than inventing a path.

## 2. External Docker Networks
Services with `networks: <name>: external: true` fail to start if the network does not exist on the host.
- Always inspect network requirements before `docker compose up`:
  `docker network inspect <net_name> >/dev/null 2>&1 || docker network create <net_name>`

## 3. Service Aliases & Database Hostname Resolution
Multi-container stacks resolve database and internal APIs by container name or network aliases:
- When running containers with `docker run`, specify `--network-alias <alias>` matching the `.env` configuration (e.g. `--network root_poki-net --network-alias mysql`).
- Verify container DNS resolution within the network:
  `docker run --rm --network <net_name> alpine ping -c 1 <alias>`

## 4. Parallel Process Execution in Agent Sessions
Interactive agent shells reject background commands using bare `&`.
- When cloning multiple repositories or running parallel downloads, execute via Python with `concurrent.futures.ThreadPoolExecutor`:
  ```python
  import concurrent.futures, subprocess
  with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
      ex.map(lambda cmd: subprocess.run(cmd, check=True), commands)
  ```
- Alternatively, launch separate background terminal sessions with `terminal(command=..., background=True)`.

## 5. Cloudflare Proxied Domains & Origin TLS (Bypassing 525 Handshake Errors)
When hosting behind Cloudflare Proxy (orange cloud) with SSL mode set to "Full":
- Automatic ACME certificate challenges (HTTP-01 / TLS-ALPN-01) through Caddy frequently fail due to ALPN protocol negotiation incompatibility (`Cannot negotiate ALPN protocol "acme-tls/1"`) or ZeroSSL EAB issues.
- Missing DNS records (e.g. `www.<domain>` without an A/CNAME record) cause NXDOMAIN errors and break ACME batch orders.
- **Remedy**: Generate a persistent self-signed wildcard origin certificate and bind directly in Caddy:
  ```bash
  openssl req -x509 -newkey rsa:2048 -keyout /etc/ssl/<domain>.key -out /etc/ssl/<domain>.crt \
    -days 3650 -nodes -subj "/CN=*.<domain>" \
    -addext "subjectAltName=DNS:*.<domain>,DNS:<domain>"
  chown root:caddy /etc/ssl/<domain>.* && chmod 640 /etc/ssl/<domain>.*
  ```
- In Caddyfile site blocks:
  ```caddyfile
  <domain>, *.<domain> {
      tls /etc/ssl/<domain>.crt /etc/ssl/<domain>.key
      ...
  }
  ```
- Cloudflare "Full" mode accepts the self-signed origin certificate, resolving HTTP 525 errors instantly without waiting on public ACME issuance.
