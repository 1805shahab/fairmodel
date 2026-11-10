# FairModel experience refinement

This milestone implements the latest attached UI/HCI brief on the existing application. It does not change backend services, APIs, financial rules, schema, provider adapters or original runtime records. Source preservation: ignored `.tmp/experience-before-20261110T234913`. Backend/API contract hash manifest: `.tmp/experience-protected.json` (37 files).

## What changed

- Public `/`: original editorial introduction, sound-inspired SVG explicitly labeled as illustration, keyboard-operated five-stage product walkthrough, and links into the real application. It contains supported-feature descriptions, not fabricated case results. `/dashboard` remains the single working workspace; `/control-room` redirects there. In-app branding keeps users in the workspace.
- Recording details: actual VAD intervals, position/keyboard/touch seeking, playback speed, native media error feedback, and current transcript segment highlighting. Timestamp seeking is retained. No fabricated waveform, autoplay, biometric result or speech measurement. Restricted cases open the compliance review first; unrelated holds remain visible.
- Uploads: shared file drop area, native accessible chooser, replacement, required-file behavior, format/size feedback, and honest request-in-progress copy. This is indeterminate feedback, not claimed byte progress. Real file validation and processing remain on the backend.
- Dashboard: existing database-derived KPIs link to supporting records. Review queue and currency-separated finance remain authoritative.
- Analytics: four desktop KPI columns, two at intermediate widths, one on narrow phones. Counts by royalty state filter the ledger, with currency selection, clear-filter recovery and actual AG Grid quick search/CSV export. All-record currency totals stay labeled separately from row filters. No browser-side authoritative money calculation.
- Shared motion: restrained hover/press, panel/notification entry, once-only public hero entrance. Motion has a reduced-motion alternative. No GSAP, Three.js, new package, remote font, continuous animation or rolling financial values was added.

Other functional contract, compliance, overlap, identity, royalty, invoice, audit and integration screens retain the preceding redesign and existing controls. This increment improves the highest-value gaps rather than rewriting them.

## Task and HCI review

These are developer/automated walkthroughs, not external user research or a WCAG certification.

| Task | Existing working path and improvement | Heuristics |
|---|---|---|
| Artist inspects a contract clause | License list → approved version → supporting source clause/PDF; empty/unverified quotations remain excluded | Recognition, evidence visibility, consistent terms, contextual help |
| Studio submits and understands audio | Assigned agreement → file chooser/drop → declared metadata → explicit analyze action → real speech intervals/transcript | Natural mapping, constraints, status feedback, error prevention and recovery |
| Artist resolves a hold | Visible independent states/next action → compliance, identity or overlap panel → required note and recorded decision | Discoverability, control, feedback, progressive disclosure |
| Artist understands a charge | Recorded royalty → measured speech/allowance/rate/rounding → explicit approval → separate invoice confirmation | Financial hierarchy, consistency, prevention, inspectable evidence |
| Studio identifies payment state | Invoice list → provider notice, actual ID/status/sync/payment history; pending/partial/paid remain distinct | Real-world terminology, visible state, no false success, supported recovery |

Nielsen's ten heuristics are applied through visible pending/error states; familiar licensing language; user-controlled playback/filter/file replacement; consistent shared components; native/backend validation; visible context; keyboard shortcuts/timestamps/grid search; progressive disclosure; actionable errors/retry; and contextual source/provider/setup guidance. Norman's mapping, constraints, signifiers and feedback appear in the native player, timeline legend/position, file chooser and state-filter controls. Financial permissions and confirmation constraints remain on the backend as well as the UI.

## Reference, accessibility and performance limits

The exact “PixelCraft Professional DJ Services Landing Page Template” could not be reliably located by targeted searches. No claim is made to have inspected or copied it. Original typography contrast, sound-inspired linework and a deliberate visual rhythm interpret the owner's description. Taste 2.5.1 guidance informed the work; the existing dynamic Next.js architecture and required truthful disclosures take priority over static-export and decorative marketing prescriptions.

Touch-sized controls, native required inputs/audio, focus-visible rings, tab arrow/Home/End handling, accessible state labels, error/status announcements and reduced motion remain supported. Transcript highlighting does not move focus or auto-scroll. Missing media or speech intervals have explicit alternatives. There has been no comprehensive assistive-technology audit.

No new dependencies or model downloads. The SVG is static; playback position updates occur on native media events, not a continuous rendering loop. Monetary values never animate. AG Grid remains dynamically loaded. No comparative performance benchmark or performance score is claimed.

## Verification

Final code checks (November 11): **173 backend tests passed** (one existing Starlette TestClient deprecation warning), **Ruff passed**, **TypeScript passed**, **ESLint passed**, and the **17-page production Webpack build passed**. All **12 Playwright checks passed in 1.4 minutes** (eleven browser workflows and one retained provider regression) after fixing two test locators: the file alert needed scoping away from Next.js route announcements, and AG Grid needed to be scrolled into view before asserting virtualized cells. No production logic was weakened to satisfy those tests. All 37 protected source/API files match their initial hashes.

Final responsive pass: **76 route/panel checks** at **1440/1024/768/390px**, **zero document overflow or page errors**, **44px native audio controls** at all four widths, and passing mobile focus trap/Escape return. The ignored `.tmp/experience-ui/visual-report.json` records the checks; 47 PNG files capture desktop/mobile states. Four additional visible-ledger captures confirm **10 rendered AG Grid rows at every width** with no page overflow (`ledger-visible.json`). A full-page screenshot can show a blank offscreen grid until its viewport is scrolled into view because of virtualization; the extra captures verify the actual visible state. Inspected images include `landing-1440.png`, `landing-390.png`, `recording-1440.png`, `recording-390.png`, `analytics-1440.png`, `analytics-ledger-390.png`, `studio-1440.png` and `studio-upload-390.png`. They show isolated QA fixture records, not original private case data or actual PayPal transactions.

Automated financial tests mock PayPal and use isolated storage. This UI milestone does not establish a new live AI response, PayPal draft, send, buyer payment or webhook delivery. Previous OAuth/read-only verification remains separate from those untested live financial operations.

Taste's separate final checker returned **GATE: ERROR**: copy was not checked because its browser walk did not obtain the rendered main/section/headline; consistency could not walk 1440/390px; the layout checker timed out. This was a checker execution failure, not a passing audit. Per its instructions, it was not rerun. No check was modified and no waiver was used. The working project Edge/Playwright results and inspected screenshots are separate verification evidence.

## Files and local commands

New components: `recording-player.tsx`, `file-dropzone.tsx`, `product-walkthrough.tsx`; shared style layer `frontend/app/experience.css`. Existing edits: public page/layout; asset detail; dashboard/analytics and upload pages; shared metric/loading/button components; workspace brand navigation; Community grid search; and browser tests. README, PLAN, AGENTS, DESIGN and current workflow/demo/sponsor/testing/architecture guides describe the new entry route. No schema migration or package installation.

From `C:\Users\shaha\OneDrive\Desktop\Work\fairmodel`, use two PowerShell terminals:

```powershell
# Terminal 1: actual Sandbox provider; draft/send flags stay off
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1
```

```powershell
# Terminal 2
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1
```

Open `http://127.0.0.1:3000`, choose Open workspace, or use `http://127.0.0.1:3000/dashboard`. Stop an existing server with Ctrl+C in its own terminal before starting another on the same port. Use `scripts/backend.ps1 -MockPayments` only for explicitly local simulated payments.

```powershell
# Backend regression checks, from repository root
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
.\backend\.venv\Scripts\python.exe -m ruff check backend/app backend/tests

# Frontend checks
$env:PATH=(Resolve-Path '.\tools\node').Path+';'+$env:PATH
Set-Location .\frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

For the isolated browser suite, first run `scripts/qa_backend.py --port 8002` with the backend Python environment, then launch the production frontend on port 3001 with `BACKEND_URL=http://127.0.0.1:8002`. From `frontend`, set `$env:PLAYWRIGHT_BASE_URL='http://127.0.0.1:3001'` and run `npm.cmd run test:e2e`. Existing first-party fixtures are required. See TESTING.md for their setup. This suite deliberately uses fixture AI and mocked Sandbox responses; it is not a command to send actual invoices.
