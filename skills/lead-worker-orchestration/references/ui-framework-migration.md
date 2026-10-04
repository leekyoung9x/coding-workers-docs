# Migrating a Hand-Written Front End to a Real Component Library (no downtime)

Use when the owner rejects the existing UI ("the UI is unwatchable", "I don't want your glued-together
components") and wants a professional component library in. The migration is a **multi-phase parallel run**,
not a rewrite-and-swap.

## 1. What the owner is actually asking for

Two different requests get conflated, and choosing the wrong one wastes the whole budget:

- *Make it not ugly cheaply* → a CSS-only framework (Pico/Bootstrap-CSS) restyled over the existing vanilla JS.
- *"I don't want to keep using your hand-made components"* → a **component library** (Ant Design, MUI, Mantine,
  shadcn/ui): ready DataGrid, Form, Modal/Confirm, Notification, Upload, responsive layout.

Signals for the second: the owner is frustrated by the *components themselves* ("why is the sidebar a turd
when the library docs have a beautiful one"), the existing code uses browser-native `confirm()`/`alert()`, and
there are components referenced but never defined. A price-first recommendation argues for the CSS framework and
reads as ignoring the request — once the owner says "use the library", the cost table is no longer the
question; the question is *how to get there without breaking what runs today*.

Library selection inputs that actually decide it (score these, not vibes): which of the app's concrete needs the
library ships (`DataGrid` with sort/filter/pagination, `Modal.confirm`, `Upload`, dark theme, DatePicker,
Badge); licence; stars **with the date measured**; years of releases / version count (the owner's phrase for
maturity is "refined over many versions"); and whether the DataGrid's advanced tier is paid. Reject anything
whose "grid/confirm/upload" you would have to assemble yourself — that recreates exactly the hand-made
component problem being escaped.

## 2. Parallel-run shape (this is what makes it safe)

- Build the new front end to a **static subpath** served by the SAME container: `outDir` → `public/v2`, Vite
  `base: '/v2/'`, old UI untouched at `/`. One container, one reverse-proxy route, **no proxy edit**, rollback =
  delete the directory. Choose this over a second container/port or a subdomain — both require touching the
  reverse proxy that serves the live product, which is the single worst thing to modify for a UI experiment.
- The server change is a handful of lines: serve the subpath's assets plus an SPA fallback for paths under it, and
  leave every API route, auth check and the existing `*` fallback for `/` exactly as they are. If the container's
  `Dockerfile` already `COPY`s the static directory, output inside it means **no Dockerfile change at all**.
- Reuse the existing auth: same token/secret storage key the old UI writes, so the owner is not asked to log in
  again, and a `403` returns to the credential prompt instead of a blank page. Never hard-code the secret.
- Ship the built output in the repo (do not build on the production host) and keep it out of `.gitignore`.

## 3. Numbers to produce before the owner commits

Earlier feasibility reports will honestly say "bundle size not measured". Once one phase builds, measure and
publish: total output size, **JS gzip**, and CSS size. A component-library admin bundle lands in the hundreds of
KB gzip (Ant Design 5 + ProComponents measured ≈614 KB gzip, ~1.9 MB raw, 458 B CSS); the owner deserves that
number before agreeing to migrate 20+ screens, and code-splitting per tab is the obvious mitigation to offer.

## 4. Component-library-first rules (these become acceptance criteria)

State them in the brief as prohibitions, because a worker's default instinct is to "make it look right" with
hand-rolled CSS on top of the library:

- Use the library's components **as shipped**. No new CSS files, no `<style>`, no CSS modules beyond a minimal
  `html/body` reset (count the lines and report them; >1 file or >60 lines means customising).
- Theme through the library's own mechanism (e.g. Ant Design `ConfigProvider` + `theme.darkAlgorithm`), never by
  setting colour tokens by hand.
- Status colours come from the library's **preset palette** (`<Tag color="red|gold|blue|green|default">`), never
  computed ad-hoc hex. Map the *value* to a preset name; do not style from a hex string the API returns.
- **No row-fill, no animation.** Represent state with a badge/tag inside the column so the eye reads one column
  vertically; filling the whole row by state and adding pulse/blink effects is what the owner calls eye-strain.
  The only permitted motion is a short hover transition and the library's own loading state, and it must respect
  `prefers-reduced-motion`.
- Responsive comes from the library's grid/breakpoints and its collapsible sider — not from hand-written media
  queries.
- Use the library's documented layout pattern, not a rough approximation: when the owner points at the docs'
  Header–Sider + Breadcrumb shell and says the current sidebar is ugly, the brief must require that pattern
  (nested `items` menu with groups, `Breadcrumb`, collapsible sider with icons) rather than basic `<Sider>` +
  hand padding.
- If a requirement genuinely cannot be met without custom CSS, the worker **stops and reports**, it does not
  improvise. Customisation is a later phase the owner opts into.

## 5. Acceptance: proving it is really the library, and that nothing broke

- **Element-class census** is the evidence, not a screenshot alone: count `document.querySelectorAll('[class*="ant-"]')`
  and assert the library's characteristic classes are present (`ant-table`, `ant-tag`, `ant-menu`, `ant-layout-sider`,
  `ant-breadcrumb`, `ant-modal` while a dialog is open). Assert the count of the project's own custom class prefix
  (e.g. `[class^="v2-"]`) is **0** — a non-zero count is the wrapped-in-library tell.
- Assert pill colour by the library's class (`ant-tag-red` and friends), and assert the `<tr>` background is the
  library default — that is the machine-checkable form of "no row fill".
- Old-UI parity, per deploy: the old surface's tab/nav count unchanged, its JS byte size unchanged, and its
  feature routes still answering (not 404). Compare **before/after** and paste both numbers.
- Same-tab screenshots of old vs new for the owner to judge; if the two look nearly identical, say so and name the
  missing library pieces instead of declaring success.
- Non-interference on the production host: game containers' `StartedAt` unchanged, public game URL still `200`,
  live data table `COUNT(*)` unchanged.

## 6. Filter / list UI acceptance (the bug the owner will hit first)

A filter UI that can legitimately return nothing must never render an empty table with no explanation — the owner
reads that as lost data ("I opened the waiting-for-sign-off filter and there's nothing there"). Require:

- A summary line showing **X / total** plus the active filter values ("Hiển thị 5 / 36 dòng · đang lọc: Trạng thái=CHỜ CHỐT").
- On zero rows: the library's empty state plus the reason and a **Clear filters** control. Best form: state the
  intersection is empty *and* show each filter's own count ("GẤP has 8 rows, all ĐANG CHẠY; CHỜ CHỐT has 5 rows,
  all THƯỜNG") — that one line converts "my data vanished" into "my filters exclude each other".
- A one-click preset for the owner's real question ("Cần chốt") rather than making them combine dropdowns.
- Before writing the fix, verify the API: fetch with each filter separately and with the combination, so "0 rows"
  is known to be correct data rather than assumed to be a bug.
