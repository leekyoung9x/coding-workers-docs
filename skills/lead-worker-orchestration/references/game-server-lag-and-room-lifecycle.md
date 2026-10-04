# Game Server Lag, Turn Inflation, and Room Lifecycle (Stateful Multiplayer & Ingress)

Procedures, diagnostic matrices, and architectural safeguards for investigating reports of "game lag", turn delays, socket disconnects, and room lifecycle failures in stateful multiplayer systems (e.g., Colyseus, WebSocket, reverse proxies, and backend microservices).

---

## 1. Fast-Path Lead Triage: Lag Reports (e.g. "Khách kêu lag từ Xpm đến Ypm")

When an owner reports lag over a specific time window:
- **Do NOT begin grepping server logs or SSH probing directly as Lead.**
- **Lead's duty**: Formulate a Numbered Brief pinning the exact time range (convert local time to UTC/ISO timestamp), list the target containers to inspect, specify metrics to extract, and dispatch a dedicated worker (e.g., `muse-code` with `--reasoning-effort max`).

### Standard Brief Extraction Matrix:
1. **Room Engine (`colyseus-server`)**:
   - Total rooms spawned vs rooms with real player turns.
   - Turn cadence: measure median/avg/max turn duration. Compare normal (10–14s) against inflated turns (30–34s).
   - Socket exit codes: count graceful `4000` vs abnormal `1006` vs missing handler kicks (`4002`). Check if drops are concentrated on a single tester/user or systemic.
   - Seat anomalies: scan for multiple seats assigned to the same `userId` (ghost seats).
2. **Reverse Proxy / Edge (`caddy`, `nginx`, Cloudflare)**:
   - WebSocket upstream status: 502 Bad Gateway (upstream offline/restarting), 504 Gateway Timeout.
   - Client connection drops: check Cf-Connecting-Ip and Cloudflare edge location (e.g., HKG vs domestic).
3. **Backend Microservices & Database (`poki-battle`, `poki-identity`, MySQL, etc.)**:
   - P95/P99 latency of S2S endpoints (e.g., `/api/battle/active-room`, `/api/user-active-room`).
   - Active room locks: check if users are trapped in `PLAYING` status for rooms that no longer exist.
4. **Host System Metrics (VPS)**:
   - Load average, RAM/swap usage, I/O wait (`vmstat wa`), disk percent.
   - Kernel warnings: separate cosmetic virtual-driver messages (e.g. QEMU `vblank wait timed out`) from actual OOM or hung-task kernel panics.
   - Clock stability: verify monotonic time vs hard clock steps (`date -s` jumps).

---

## 2. Common Root Causes & Failure Signatures

### A. Turn Inflation via Ghost Seats (~33s Turn Loop)
- **Mechanism**: A client drops connection or reconnects rapidly via `JoinById`. The server's reclaim check `ep.userId === uid && !ep.isConnected` fails because the old half-open socket is still marked `isConnected = true` in memory. The room pushes a new seat instead of reclaiming.
- **The Turn Delay**:
  - Player turn timer: 15s (player idle or app backgrounded).
  - Boss action delay: 2–3s.
  - Boss ACK timeout (`CLIENT_ACK_TIMEOUT`): 15s. The server waits for all connected seats to ACK. Because the ghost seat has no real client running the battle UI, it never sends `boss_done`. The server waits the full 15s timeout before rotating turns.
  - **Total**: ~33s per turn instead of 12–14s.

### B. Indestructible Zombie Rooms
- **Mechanism**: Normal rooms auto-dispose when empty via an `emptyRoomTimeout` (e.g. 300s). But ghost seats maintain `conn: true` at the TCP/heartbeat layer even if the client app is suspended.
- **Consequence**: The empty room timer never triggers. If pet energy is large and boss attack is weak, the room loops for hundreds or thousands of turns (10+ hours), consuming server memory and locking the player's account in database `active_room_id`.

### C. Client Reconnect Gate Mismatch (20s Loading Timeout)
- **Mechanism**: Old client builds often gate their loading screen strictly on `init_state` (`GateTimeoutRoutine` 20s). When a client rejoins a match in progress, the server's reclaim path emits `reconnect_state` but omits `init_state`.
- **Result**: The client receives game state but never unblocks the loading gate, timing out after 20s and returning to lobby, which again queries active-room and loops back into the same zombie room.

### D. Upstream Proxy 502 on Container Restart
- **Mechanism**: PM2 inside a container defaults to `kill_timeout: 1600` (1.6s). If the server initiates a graceful drain (e.g. 600s), PM2 forcibly sends `SIGKILL` after 1.6s. Upstream proxy (Caddy/Nginx) receives connection refused, logging 502 for active WebSocket handshakes.

---

## 3. Mandatory Architectural Safeguards

Every stateful room server implementation must enforce:

1. **Unconditional Reclaim by UserId**:
   Reclaim the seat of the matching `userId` regardless of the current `isConnected` flag. Detach and invalidate any stale session before binding the new connection.
2. **Pre-Battle Seat Deduplication**:
   Immediately before starting battle, scan the player list. Splice any duplicate `userId` entries and re-index seats so 1 user can never occupy > 1 seat.
3. **Skip ACK Timeout for Inactive/Disconnected Seats**:
   Do not block turn rotation for seats marked disconnected or inactive.
4. **Server-Side Zombie Reaper**:
   Track consecutive idle turns. If $N$ consecutive turns (e.g. 6 turns) complete with zero player action (`swap_tile`, `use_card`, or active ACK), the server must immediately invoke `endGame("idle_timeout")` and dispose the room.
5. **Hard Caps on Turn Count and Room Age**:
   Enforce a maximum turn ceiling (e.g. 200 turns) and room lifetime ceiling (e.g. 60 minutes). Terminate runaway loops automatically.
6. **Backward-Compatible State Emission**:
   When reclaiming an active room, emit BOTH `reconnect_state` AND `init_state` (populated with current snapshot data) so older client builds unblock their loading gates.
7. **Idempotent Graceful Leave Route**:
   Expose an authenticated endpoint (e.g. `POST /api/battle/rooms/graceful-leave`) that clears the player's active room in the database when they intentionally quit, preventing lobby reuse traps.
8. **PM2 Kill Timeout Alignment**:
   In `ecosystem.config.js`, set `kill_timeout` to an adequate drain window (e.g. 30000ms) rather than the 1.6s default.
