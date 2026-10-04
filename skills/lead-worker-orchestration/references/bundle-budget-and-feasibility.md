# Feasibility Questions and Bundle Budgets

When the owner asks "is this feasible, any problems?" about a stack/library/architecture change, the answer
is a set of measured numbers plus the caveats that would flip the verdict — never a judgement, and never the
vendor's marketing size. Same discipline when a brief must carry a bundle budget.

## 1. Size the candidates yourself before agreeing to anything

```bash
gzip -c -9 <file> | wc -c                  # transfer cost of a JS bundle you already have
npm pack <pkg>@<ver> --silent && tar xzf <pkg>-<ver>.tgz -C /tmp/probe   # size real dist files pre-install
ls /tmp/probe/package/dist/ && du -b /tmp/probe/package/dist/*
```

Typical measured shapes (2026-era, use your own numbers): the PixiJS v8 core bundle is ~682 KB raw / ~185 KB
gzip — i.e. **one runtime engine alone can exceed a 150 KB-gzip initial-JS budget**. GSAP core is ~73 KB raw /
~28 KB gzip. A Pixi layout helper package is only a few KB — its weight is entirely in the `yoga-layout` peer.

Rules:
- **Read `peerDependencies` before quoting a size.** The number you can measure is often not the number that
  ships; the expensive peer may be a WASM/native module you cannot size without installing it. Say which figures
  are still unmeasured rather than presenting a partial total as the cost.
- Never quote a npm "unpackedSize" or a dev-build chunk as transfer cost — state the measure you used.
- Compatibility gates belong in the verdict: a runtime whose peer requires `pixi.js >= 8.16` cannot ship on a
  repo pinned to 8.9.2, so "upgrade the engine to one version first" is a prerequisite, not a footnote.
- **A peer range that excludes your major version is a SUBSTITUTION decision, not a version bump**: an emitter
  package carrying `peerDependencies: {'@pixi/core': '>=6.0.4 <8.0.0'}` can never run on v8, while the engine's
  own core already exports `ParticleContainer` — so the correct stack entry is the core API plus a hand-written
  emitter, and only a verified v8-compatible fork is admissible otherwise. Sweep the installed typings for the
  capability before adding a package: `grep -c '<ClassName>' <pkg>/dist/*.d.ts`.
- **Pin the renderer backend for a CPU-only / software test target**: the engine's autodetect prefers the newest
  backend (`RendererPreference = 'webgl' | 'webgpu' | 'canvas'`), and a software rasteriser (SwiftShader) makes
  WebGPU a blank-frame or glacially-slow risk. Set `preference: 'webgl'` (or `['webgl','canvas']`) at the single
  place the renderer is created — never per scene.
- **Size a layout helper by its peer, and check its load path**: the helper package itself is a few KB gzip while
  its layout engine peer ships a WASM base64-embedded in one file (~120 KB raw / ~50 KB gzip). Read the package
  `exports` map: a `./load` subpath that fetches `.wasm` at runtime turns a self-contained bundle into a request
  that 404s behind a CDN — pick the embedded variant deliberately.
- **Align the toolchain's peer ranges before freezing it**: a test runner whose peer is `vite ^6.4 || ^7 || ^8`
  fixes the floor for the build tool, so the build/Vite/test trio must be chosen together, not one at a time.

## 2. Measure prod, never the working tree

- A `.next` directory with **no `BUILD_ID`** and a pile of `*.hot-update.js` is a **dev build**: its catch-all
  `main-app.js` can be multi-MB and every per-route figure derived from it is fiction. Check first:
  `ls .next/BUILD_ID` and `find .next -name '*hot-update*' | wc -l`.
- Take production chunks from the **running container** (`docker exec <ct> ls -la /app/.next/static/chunks/…`,
  `docker exec <ct> cat /app/.next/BUILD_ID`) or after a real `next build`.
- Enumerate what a route actually loads from `.next/app-build-manifest.json` (`pages["/route"]` → file list);
  gzip the route's own chunks and report them separately from the shared framework chunks.
- Prove a library is **not** in the client bundle with a marker sweep, not by reading imports:
  `grep -rl '<lib marker>' .next/static/chunks` → 0 lines means it is genuinely lazy/absent. (Pick a marker
  that survives minification: an exported class name or property key, never a local variable.)

## 3. When a dependency exceeds the budget, lazy-load it behind the boundary

If the engine alone blows the initial-JS budget, the only internally consistent design is that it never enters
an initial route chunk — it is fetched when the canvas/scene mounts. **Look for the in-repo precedent first**:
this codebase already had a `loadX()` that appends `<script src=PIXI_CDN>` on demand, which is exactly why the
marker sweep found zero engine code in any prod chunk while the engine still rendered the game. Adopting an
existing pattern costs nothing and is provable; inventing a bundler config costs days.

A budget is only usable if the brief/standard defines all three of: **what counts as "initial"** (the route's own
initial chunks vs the shared framework chunks), **the measuring command**, and **the fail threshold**.

## 5. Framing a greenfield-vs-incremental decision (three scenarios, never two)

A binary "keep the current stack vs rewrite" question hides the option that usually wins: **build the new stack
in parallel and migrate one surface at a time, leaving the incumbent untouched**. Offer all three and let the
owner choose:

| Scenario | Shape | Correct when |
|---|---|---|
| A0 | keep the incumbent, upgrade the new renderer inside the existing boundary | the boundary already exists and the migration is local |
| B1 | new stack runs **alongside**, one surface (e.g. the game routes) moves over, the old app keeps serving | the incumbent owns any business surface worth keeping |
| B2 | new stack **replaces** the incumbent | only if the incumbent genuinely has nothing to keep |

Before recommending B2, **count what the incumbent framework owns** and put the counts in the decision table —
API routes, pages, routes that use auth/session, payment endpoints, SEO/metadata/rewrites, and affected test
specs. The decision turns on that count: in practice a "clean" rewrite was carrying dozens of API routes, ~24
business pages, session/mail/SMS/rate-limit libraries, payment integration and a hundred-plus specs, while the
actual game surface was a handful of routes. If a framework (Next.js) is chosen for its server features, say
which of them the new stack loses.

Also require the analysis in the same document to answer: which parts of the incumbent **cannot** be dropped
(SSR/SEO, rewrites, auth, payments), and what is the cheapest path that still reaches the goal. Pair the table
with **named decision gates carrying thresholds** (slice runs on the real CI target; per-route initial-JS growth
under budget; exporter parity within a pixel tolerance; zero regressions in the existing mandatory suite; one
engine version; licenses settled) — a phase may not start until its gate passes.

For a chosen rewrite, the first deliverable is a **vertical slice** (boot → one screen → one small game, with
one panel, one button, one popup motion, one effect, the asset manifest, the exporter and CI all wired), not a
framework built in the abstract: the slice is what proves the pipeline before the rest is migrated.

## 6. Recorded architecture decisions for this project (settled by the owner)

- **Hybrid, not a full renderer rewrite.** The framework shell (Next.js 15 + React DOM) owns app shell, routing,
  and every screen — menus, shop, inventory, settings, forms. The game renderer (PixiJS) lives **inside a
  `GameCanvas` component** and owns match-3, world/game rendering, characters, VFX, and only the HUD that must
  track the game. **The scene manager is scoped to the canvas**; it never governs app-level navigation.
  This also retires the "Vite" error in any older standard document — the stack is Next.js.
- **Animation libraries**: a tween library (GSAP) is approved. A skeletal-animation runtime (Spine) is
  **not** part of the core stack for the first phases; it may only be added when (a) the project actually has
  that kind of animation, (b) its license/editor question is settled, and (c) the engine has been upgraded to
  satisfy the runtime's peer range — and no document may imply the current pin is already compatible.
- **Budget**: per-route initial-JS growth, small (order of ≤150 KB gzip at game load), with heavy/VFX/tooling
  libraries lazy-loaded per scene. A proposal that silently pulls every dependency into the initial bundle is
  rejected even when it matches the reference architecture.
- **Ornament rule** (sibling, not child): decoration nodes must be siblings of the resizable base, never inside
  its stretch region, and may only be repositioned or uniformly scaled per variant — never non-uniformly stretched.
- **Duplicated source trees**: an owner who says "do not conclude this from a report" wants the canonical tree
  established by tracing `next.config`, tsconfig paths, real routes, imports and git history — then the leftover
  tree proposed for deletion, not removed unilaterally.
- **Asset loading is a manager, not a free-for-all** (greenfield target): a scene may not call the engine's asset
  loader directly. Declare an `AssetManifest` (bundle per screen/scene group: core, home, each game, fx) and route
  every load through a manager exposing `preloadCore()` / `preloadScene(id)` / `releaseScene(id)` /
  `prefetchScene(id)` — with an explicit release point, otherwise "lazy" becomes a memory leak.
- **The dev galleries are a contract test surface, not a playground**: every gallery entry needs an automated
  test, but the *class of test* follows the effect — deterministic rendering gets a visual baseline, GPU-sensitive
  or shader-heavy effects get smoke + metrics (duration, emitter count, no crash, no leak) and are explicitly NOT
  compared pixel-by-pixel on a software rasteriser. Demanding a screenshot baseline for every effect is wrong for
  exactly the effects the same document already declared non-deterministic.
- **A target-architecture document is design intent, not schema** — when the owner sends a full reference design
  (component library + motion + effects + exporter + tests), what becomes binding is the small set of orchestration
  interfaces (asset manager, motion presets, effect composer entry points), each pairing a rule with the test class
  that enforces it; measure the rest and report before adopting it verbatim.
