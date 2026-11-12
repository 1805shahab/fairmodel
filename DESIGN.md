# FairModel product design

## Current direction: recording-studio ledger — November 12

Spacing refinement: page/header/footer share a 1440px content frame and responsive 48/32/24/16px gutters. Single forms use the available width, while studio generation pairs the form with bounded, keyboard-scrollable history on desktop when records exist; empty-history pages use the full-width form. The public five-stage explainer uses a native sticky scroll narrative with stable viewport space; click/keyboard navigation remains, and reduced-motion/short screens use a static compact view. Shared public and workspace footers use actual app directories and explicit demo/test labels.

The latest owner brief supersedes the graphite/ice visual palette below. The frontend now uses warm paper, deep ink and restrained vermilion, with intentionally designed light/dark tokens, Instrument Serif display type, Geist UI type and JetBrains Mono financial figures. One top-navigation workspace, the existing role/context logic and all existing workflows remain. Historical CSS provides layout structure but references the shared semantic palette in `frontend/app/ledger-theme.css`, exposed through Tailwind configuration.

Contract review pairs editable terms with verified source evidence, a mobile view switch and an explicit whole-version activation summary. Audio/compliance keeps processing, AI interpretation, deterministic evidence and artist decisions separate. AG Grid Community uses a ledger theme, a pinned exact amount column and a read-only detail dialog. Invoices visibly identify their provider and await confirmation until the backend reports settlement. The sculpture remains optional interactive art, with the required non-verification caption.

370 backend tests, 33 browser tests, TypeScript/ESLint and production build pass. Both-theme axe scans, responsive/state captures and 1080p review artifacts are recorded in [the audit and verification report](docs/LEDGER_UI_REDESIGN.md). No backend, API contracts, provider integrations, environment configuration or runtime records were changed. Earlier palette directions are historical.

## Current direction: spatial voice-rights studio — November 11

The owner explicitly rejected the previous retained sidebar, repeated light/teal dashboard and overly restrained motion. The visual direction below supersedes that treatment while retaining the same routes, data and safeguards. The primary app has no sidebar DOM: full-width module navigation and a Ctrl+K searchable page launcher replace it. The overview is an asymmetric composition with large editorial type, an interactive sculptural voice object, unboxed record counts, a review desk and an ivory financial panel. Recent submissions use actual saved records, not invented waveform/feed decoration.

New tokens in `stage-theme.css`: graphite canvas #0d1119, surface #151d29, ice accent #94ddff, text #edf2f8, muted #a6b2c4, border #2b3749; the financial panel uses warm ivory #e9e6df. Semantic review/error/satisfied colors remain distinct. These tokens and dark AG Grid styling carry through the real application and public entry.

`voice-sculpture.tsx` and the lazy `voice-stage.tsx` render a genuine Three.js object: multiple closed harmonic tube geometries lit with cool and warm directional lights. Users can drag, rotate by keyboard/buttons, pause/play and reset. It is generative art, clearly labeled as neither voiceprint nor measurement. It reads no audio and no identity/financial data. This is an explicit 3D request; no downloadable model, HDR texture, external asset or new package is required. Existing Three.js core is used directly, with no postprocessing or extra React 3D framework in the render path.

Rendering is capped to 30 updates/second with pixel ratio capped at 1.5 (1 on explicitly enabled mobile). Offscreen/hidden-tab work pauses; pause renders on demand; unmount disposes geometry/material/renderer/context. Small screens initially use a deterministic SVG still and can explicitly enable 3D. Reduced motion disables automatic rotation while retaining manual orientation controls. WebGL failure removes the canvas and explains the static fallback. UI entry/hover/nav feedback supplements the signature 3D interaction; money and compliance conclusions never animate into invented values.

Frontend source was preserved before this work in ignored `.tmp/spatial-before-20261111T003131`. Existing backend/API contracts, database and provider logic remain protected. Current verification is recorded in PLAN.md; historical checks below do not prove this new visual build. Taste guidance is used for hierarchy, motion/fallbacks and visual review; its prior standalone browser checker failed to execute, and that earlier gate is not being represented as a pass or rerun.

Current routing update (November 10, latest brief): `/` is the public introduction to the same working `/dashboard`. The owner explicitly requested this landing page; it supersedes the previous root redirect. `/control-room` still redirects to `/dashboard`; its fictional preview remains retired. Artist/studio roles share the working UI. Standard backend startup selects actual PayPal Sandbox with default-off writes; local simulation requires `-MockPayments`. Historical descriptions below record earlier milestones. See docs/APP_WORKFLOW.md.

## Human-centered experience refinement

Software: AI voice licensing and artist-approved royalties. Main action: Open workspace. Preserve the established navy/neutral/teal tokens and local typography; original editorial Georgia italics are limited to public headlines. No new font fetch, motion library, GSAP or Three.js. Existing dynamic API routing is retained.

Public composition: one hero at desktop screen height with editorial type and an original sound-inspired SVG illustration, followed by a user-operated five-stage workflow and a trust section. The illustration explicitly states that it is not voice analysis. No invented case, transaction, number, provider success, testimonial, or decorative waveform is presented as evidence. The exact PixelCraft Professional DJ Services template could not be reliably identified in targeted searches; the owner's described rhythm, type contrast and interactive storytelling informed an original composition. No third-party template asset or layout was copied.

Audio: actual stored VAD intervals form a timeline; total duration and speech duration remain separate. Range input provides keyboard/touch seeking; native audio controls remain. Time events highlight the current timestamp segment without autoplay, automatic scrolling or fabricated timing. Speed changes the native player. Missing intervals remain explicitly unavailable. Manual identity is never called biometric verification.

Analytics: four equal desktop KPI columns, two at intermediate widths and one on narrow phones; one caption per currency, amounts directly from the API. State bars represent counts of stored royalty entries and filter the Community grid. Currency filtering affects counts/rows, not the all-record currency-separated totals. Search and CSV use the actual filtered grid. No financial aggregation is recalculated in JavaScript.

Motion: 150ms hover/focus feedback, 200ms panel/notification entry, 700ms once-only public hero entrance. Transform/opacity only for movement; no continuous scene, autoplay, rolling balances, artificial AI progress, scroll-jacking or animation over financial rows. Reduced motion removes these transitions and animations. Explicit long-running request feedback remains readable without a spinner.

HCI: system status (real pending/error/provider labels), matching language (speech versus recording), control/recovery (native playback, file replacement, clear filters and retry), consistency (same shell/tokens/actions), prevention (native required input and existing backend safeguards), recognition (visible evidence categories and next action), efficiency (timestamp seeking and ledger search), hierarchy (urgent status before details), actionable errors and contextual guidance. These are design decisions and developer/automated task checks, not a claim of external user research or audited WCAG certification. All existing approval confirmations and backend permissions remain in force.

## Audit and scope — November 10, 2026

The working App Router routes use shared workspace context, `useData`/`useAction`, role-scoped API proxying, native audio, source citations, and AG Grid Community. The separate `/control-room` is a fictional preview and remains separate. Existing source changes were copied to ignored `.tmp/premium-ui-before-20261110T184423` before this work. Backend, API routes, API client and shared data contracts are hash-protected for this change.

Problems: horizontal navigation competes with content; audio review is one long column; payment instructions precede every invoice; repeated source and financial information interrupts review; dashboard decoration occupies useful review space; status semantics need to distinguish processing, authorization and payment.

## Direction and system

Use a navy navigation rail, warm neutral canvas, white work surfaces and teal actions. Semantic blue means processing/information, amber means incomplete/review, red means restricted/error, green means satisfied/approved. Color never replaces a written status. Financial numbers use tabular figures. No decorative charts, generated events, invented metrics or gradients in the workspace. Voice: calm and precise; name the state, evidence and next action before making a product claim. No company facts or testimonials are invented.

Tokens live in `frontend/app/workspace-theme.css`: ink #172b36, muted #52646d, canvas #f5f6f5, surface #ffffff, line #dce3e1, accent #08786c, navigation #13272c. Spacing follows 4/8/12/16/24/32/48px; radii 6/10/14px. Existing locally available Segoe UI with sans-serif fallback avoids network fonts and extra installation; body 15px, labels 13px, page titles 28–32px. Use visible focus rings and 44px controls.

The accessible design-taste-frontend 2.5.1 skill informed copy, equal alignment, typography and consistency. Its proposed white/blue fintech palette is adapted to the owner's navy/teal brief. Its marketing-only full-height sections, mandatory decorative moments, font downloads and static export do not apply to this compact authenticated-style dynamic application. Preserve required fixture and test-payment disclosures even where marketing copy checks discourage sample labels. The product's established name and all claims come from existing app behavior, not invented company facts.

## Page structures

- Shell: desktop sidebar, page-context top bar, one persona switcher, mobile menu with Escape/focus recovery, skip link.
- Overview: role-specific metrics, next-action queue, recent submissions, actual licensing and currency-separated financial summaries.
- Recording: persistent player, independent states and next action; keyboard-operated tabs for overview, transcript, compliance, identity, overlap, royalties and source evidence. Hidden panels remain mounted so switching tabs preserves entered notes. Timestamp buttons seek the actual media.
- Compliance: conclusion and next action first; satisfied, violated and unresolved conditions; advisory AI findings separated from deterministic/workflow evidence. Source text is verified and never fabricated.
- Finance: compact provider-labeled invoice cases, separate send/refresh/payment actions, exact existing backend amounts and historic state. No financial actions run merely for visual testing.
- Contracts: actual parties, validity, version and allowance in lists; grouped review terms and collapsible source evidence. Immutable approved versions remain immutable.
- Supporting screens share the same tokens, field styles, error recovery and tables.

## Components and accessibility

Keep shared loading/error/empty/form/action components. Add controlled keyboard tabs and compact metric/section primitives where reused. Native details provide accessible evidence expansion. No theme toggle or new dependency. Sidebar collapses below 1100px; columns stack below 760px. Tables and tab strips have deliberate internal scrolling; the page must not overflow at 390px. Honor reduced motion, preserve visible labels, and keep review warnings outside tabs.

## Verification

Backend regression checks: 173 tests passed and Ruff passed. All 36 protected backend/API files match their pre-redesign hashes. Final TypeScript/lint, 16-page production build and eight Edge regressions passed. Browser coverage includes role restrictions, contract citations, current review actions, actual timestamp seeking against byte-range media, note preservation, overlap choices, invoice context/search and mocked Sandbox confirmations/status. Responsive screenshots covered 68 route/panel/viewport cases with no page overflow/errors and passing mobile focus handling. See docs/UI_REDESIGN_REPORT.md and ignored `.tmp/premium-ui/` screenshots. Automated provider tests use mocks or explicitly selected fixtures, never live financial writes. UI tests do not establish live PayPal settlement or biometric identity.

The skill's attempted standalone screenshot/checker could not connect to its browser reliably. Its final result was `GATE: ERROR`: consistency could not walk 1440/390px, layout check timed out and copy was not inspected. No waiver or checker modification was used, and the failed gate is not rerun. Use the project's Edge/Playwright screenshots and functional/responsive checks for the actual UI evidence; this is not a Taste gate pass. Marketing screen-height/decorative-moment requirements are intentionally not imposed on compact workflow pages.
