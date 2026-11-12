# FairModel

**Every voice deserves a fair share.** AI voice licensing, explainable compliance, and artist-approved royalties.

Source repository: [1805shahab/fairmodel](https://github.com/1805shahab/fairmodel) (private).

Local full-stack hackathon application: Next.js App Router/React/TypeScript/Tailwind, FastAPI/Python 3.12, SQLAlchemy/SQLite, Gemini (`google-genai`), Groq Whisper, FFmpeg/ffprobe, WebRTC VAD, and AG Grid Community.

Optional **Fish Audio `s2.1-pro-free`** voice generation now sits alongside Gemini, with separate artist consent and explicit studio provider selection. It uses inline reference audio, creates no reusable provider profiles and never switches to a paid model or another provider. Free access has fair-use limits and no DPA/verified zero-retention guarantee. See [setup, official-source findings and manually authorized live test](docs/FISH_AUDIO.md). Fish live generation remains unverified; normal tests use mocked HTTP and synthetic test recordings only.

Current Fish output requests completed MP3, validates frames and FFprobe metadata, then uses strict FFmpeg conversion/final WAV validation. **354 backend tests**, backend Ruff, frontend TypeScript/ESLint and production build pass. Saved job `39e683f43f624ae0ac0f3485d590fd31` completed HTTP but declared near-4GB finite WAV data against only 2,039,500 available data bytes. It remains failed; a placeholder versus incomplete provider output cannot be established. No new live attempt was run. See [the investigation and next owner-run test](docs/FISH_MP3_OUTPUT.md).

Latest Fish response audit: **345 backend tests**, backend Ruff, frontend TypeScript/ESLint and production build pass. Pipeline v4 checks completed HTTP bodies, inspects WAV/MP3 framing and normalizes valid variants with strict local FFmpeg before validating canonical output. Both historical failures remain unchanged; their exact returned format is unknown because response bytes were not retained. No new live request was made. See [findings, integrity limits and the next manual test](docs/FISH_AUDIO_VALIDATION_REPORT.md).

Fish checkpoint: **282 backend tests**, Ruff, frontend TypeScript/ESLint, the 21-page production build and **five focused Edge generation checks** pass. Schema 7 preserves all original fields/rows across 22 tables and uploaded-file hashes; a consistent pre-change backup is recorded in PLAN. No real Fish call or financial operation was performed.

Latest Fish WAV repair: **311 backend tests**, Ruff, frontend TypeScript/ESLint and the production build pass. Valid incoming WAV sample-rate/PCM/float/stream-header variants now undergo inspection and real local normalization rather than being rejected for differing from Gemini's exact output format. Malformed/truncated/non-audio remains blocked; new receipts retain safe format facts and source/output hashes. The owner's failed live response was not retained, so its exact variant and successful live generation remain unverified. No live retry was performed. See [the format repair and next manual test](docs/FISH_AUDIO.md#returned-wav-validation-repair).

RIFF follow-up: **324 backend tests** and frontend checks/build pass. Pipeline v3 validates complete inner chunks before repairing a stale outer length, and recognizes the narrow legacy empty-WAV stream header with explicit uncertainty. Finite truncated data remains blocked. No new live request or historical-job edit; the original header was not retained and remains unknown.

**Payment integration: actual PayPal Sandbox, with explicit local simulation for offline tests.** Sandbox OAuth and read-only Invoicing v2 access succeeded. Draft/send/status/webhook code is implemented and mock-tested; actual draft, send and buyer payment still require separate owner approval and verification. No production endpoint or real-money flow is supported. Historical mock records remain simulated.

November 11 payment checkpoint: the owner created a genuine USD 17.46 Sandbox draft. After explicit owner authorization, its merchant-email typo was reconciled locally using only OAuth/GET, with backup and original-intent audit preservation; the same remote draft is now API-visible as DRAFT. No new remote invoice, sending or payment was performed by the agent. **370 backend tests**, backend/new-script Ruff and frontend typecheck/lint/build pass. Sending and settlement remain unverified; see [Sandbox reconciliation details](docs/PAYPAL_SANDBOX_TESTING.md#errors-and-uncertain-writes).

Earlier product-upgrade verification (November 11): **190 backend tests**, Ruff, TypeScript/ESLint, the **20-page production Webpack build** and **23 Edge Playwright checks** pass. Sixteen responsive checks across four widths report no page overflow or browser errors. New private Voice Usage Passports, interactive evidence, artist/studio review threads and the no-write royalty simulator join the existing workflows. Schema 5 adds evidence/review history; all 17 original tables and 18 private files were preserved and verified against the backup. The working overview retains its actual Three.js rendering and accessible fallback. Browser financial tests use mocks/explicit AI fixtures with real local PDF/media/VAD processing. Fresh actual Sandbox OAuth/read-only access succeeded; actual draft/send/buyer payment remains unverified and requires separate case-specific approval. See [the product upgrade report](docs/PRODUCT_UPGRADE.md), [single-app workflow](docs/APP_WORKFLOW.md), [Sandbox testing](docs/PAYPAL_SANDBOX_TESTING.md) and [sponsor usage](docs/SPONSOR_INTEGRATIONS.md).

## Run on this Windows workspace

Dependencies, portable Node 22, and portable FFmpeg have been installed in ignored local directories. Open **two PowerShell terminals**, each at the repository root:

```powershell
Set-Location 'C:\Users\shaha\OneDrive\Desktop\Work\fairmodel'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1
```

```powershell
Set-Location 'C:\Users\shaha\OneDrive\Desktop\Work\fairmodel'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1
```

Open **http://localhost:3000**. FastAPI OpenAPI: **http://127.0.0.1:8000/docs**. Both processes bind only to loopback. Stop each with Ctrl+C. The process-scoped execution-policy flag allows the checked-in helper; it does not change the machine's policy.

The homepage `/` introduces FairModel and opens the same application at `/dashboard`. The former `/control-room` URL redirects to that workspace; its fictional cinematic preview stays retired. Use **Workspace role** to work as artist or studio in the same database-backed workflow. **Settings & integrations** holds provider status, the read-only PayPal diagnostic and sponsor tools. Audio review includes real VAD intervals, timeline seeking, transcript highlighting and playback speed. Analytics offers linked state/currency/search filters over the actual royalty ledger.

The full-stack workflow is [/dashboard](/dashboard). Use its top-right local role switcher for **Amara Reed / Artist** and **Northstar Studio**. These are fictional demonstration identities, not production authentication.

The working app uses full-width navigation and a searchable **Ctrl+K page launcher**, with graphite/ice surfaces and an ivory financial panel. Its overview combines actual-record review cases, submission objects, unboxed metrics and an interactive Three.js voice sculpture. Drag or use its rotate/pause/reset controls; small screens offer **Explore in 3D**, and reduced motion stops automatic rotation. The artwork is not voice identity or usage evidence. Existing audio review, citations, approvals, overlap, royalties and invoice actions remain connected to the same API. No fictional Control Room store/rates/events are imported. See [DESIGN.md](DESIGN.md) and [the current UI review](docs/SPATIAL_UI_REVIEW.md). Earlier UI reports document previous checkpoints; the standalone Taste checker previously failed to execute and is not claimed as passing.

### One app, actual PayPal Sandbox

The standard `scripts/backend.ps1` launcher now explicitly selects `paypal_sandbox` for this process, using the existing backend credentials. It does not change `.env`. `-PayPalSandbox` remains a supported alias; `-MockPayments` explicitly selects local simulation for offline development. Direct Uvicorn invocation still honors `.env`.

Live OAuth and authenticated read-only Invoicing access were reverified on November 10. Sandbox draft/send/status/webhook code is implemented and tested, but a completed live Sandbox payment has not yet been verified. Draft/send writes stay disabled unless separately enabled after reviewing and authorizing the actual case. Startup and normal automated tests never create/send invoices. See [the single application workflow](docs/APP_WORKFLOW.md) and [Sandbox testing](docs/PAYPAL_SANDBOX_TESTING.md).

APIMatic PayPal 0.4.1 supplies developer guidance; AG Grid Community powers the actual royalty ledger; the guarded Postman collection can be downloaded from Settings. Postman execution and AG Studio are not claimed. Local artist/studio roles remain demonstration access, not production authentication.

### Windows Application Control and Next.js

Development and production builds explicitly use Webpack. Windows Application Control can block Next.js's native SWC compiler (`next-swc.win32-x64-msvc.node`), causing Next.js to load its WebAssembly fallback. Turbopack requires the native compiler; Webpack supports this fallback. The native-binding warning may still appear, while the application starts successfully. The first WebAssembly compilation can take longer than subsequent requests.

Continue using `scripts/frontend.ps1` or `npm.cmd run dev`; both select Webpack automatically. `npm.cmd run build` also selects Webpack. See [Next.js CLI options](https://nextjs.org/docs/app/api-reference/cli/next) for the supported `--webpack` flags.

## Fresh checkout setup

Install Python 3.12, Node.js 22 LTS or newer, and FFmpeg/ffprobe. If desired, install the latter tools yourself with:

```powershell
winget install --id OpenJS.NodeJS.LTS -e --source winget
winget install --id Gyan.FFmpeg -e --source winget
```

Open a new terminal after installing system tools, then:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
Copy-Item backend\.env.example backend\.env
# Optional server-only backend configuration; no API keys are needed for fixtures.
Set-Location frontend
npm.cmd ci
Set-Location ..
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-demo.ps1
```

Do not overwrite an existing `.env`. The lock file contains the verified core and development Python environment. `requirements.txt` and `requirements-dev.txt` remain readable direct dependency definitions. `frontend/package-lock.json` locks npm resolution. Speaker packages are excluded from all core locks.

`create-demo.ps1` generates a first-party PDF and narration using a Windows installed stock TTS voice. The narration is **not the fictional artist's voice**, and no speaker match is claimed. Fixtures and their SHA-256 manifest are local ignored artifacts. Regenerating fixtures changes their hashes: use the newly generated files together. If Windows speech components are unavailable, the app still accepts real user-authorized PDFs/audio with configured providers.

## Complete local demo

For the repeatable judging scenarios (explicit offline AI, real local media measurement, simulated payments):

```powershell
# The base fixtures already exist here. Generate them only if missing using scripts/create-demo.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-scenarios.ps1
Set-Location backend
.\.venv\Scripts\python.exe ..\scripts\seed_demo.py
Set-Location ..
```

This adds one clearly labeled fictional judging agreement and scenarios A/B/C. Repeating it reuses the same records and invoice; it preserves existing contracts, recordings and financial history. A is included usage with no payable invoice; B has a positive artist-approved simulated draft; C is restricted with no invoice. Current local measured speech is 14.88s / 58.77s / 12.57s respectively; B calculates USD 57.54. Generated stock-voice measurements can differ on another machine. See [DEMO_GUIDE.md](docs/DEMO_GUIDE.md), [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) and [TESTING.md](docs/TESTING.md).

See [the three-minute guide](docs/DEMO_GUIDE.md). Download fixtures from **Settings & integrations > Offline testing tools**. Artist: create license → upload sample PDF → explicitly select local fixture extraction → review terms/source quotes → add review note → approve. Studio: submit narration with US / online advertising / English → explicitly select offline transcription → analyze → explicitly select offline compliance → evaluate. The first report holds charges until artist identity/usage review. Artist: record the fixture-only simulated review on the audio page → reevaluate with offline compliance explicitly selected → approve the proposed royalty → create simulated invoice → simulate send. Studio: simulate payment completion. Inspect AG Grid analytics and audit records.

Mock payment screens display **DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED**. Simulation sends no email or funds. Actual Sandbox invoices display **PAYPAL SANDBOX — TEST TRANSACTION — NO REAL MONEY** and never offer simulated completion. Routing follows each stored invoice's provider, including historical mock records.

### PayPal Sandbox

Keep existing credentials backend-only. Configure `PAYPAL_SANDBOX_MERCHANT_EMAIL` and `PAYPAL_SANDBOX_BUYER_EMAIL` locally using distinct business merchant/personal buyer Sandbox accounts. Do not overwrite `.env`. This maps the configured merchant and test buyer; it is not artist merchant onboarding. Initial invoice support is USD only.

```powershell
# Root -> backend: OAuth/read-only capability; no invoice draft or email.
Push-Location backend
.\.venv\Scripts\python.exe ..\scripts\paypal_diagnostic.py --capability
Pop-Location
# Stop the existing backend before starting this replacement.
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1 -PayPalSandbox
```

Financial writes remain disabled. After explicit approval for the reviewed case, separate `-EnableSandboxDrafts` / `-EnableSandboxSending` switches enable those actions for that process. UI confirmations show actual amount/recipient. Follow [PAYPAL_SANDBOX_TESTING.md](docs/PAYPAL_SANDBOX_TESTING.md) for actual draft/send/buyer-payment steps and uncertainty recovery. APIMatic guidance installation is separate from API execution; start a new Codex session for automatic plugin discovery.

For real AI, configure only `backend/.env` with `GEMINI_API_KEY` and `GROQ_API_KEY`, restart the backend, leave contract fixture extraction unchecked, and use **Live Groq Whisper** / **Live Gemini** on the audio page. Both audio selectors default to live independently of saved fixture results. Configured status only indicates key presence, not a successful provider request. Missing keys or provider failures return useful errors without hidden fixture fallback. Real Gemini extraction/content assessment and Groq transcription were reverified on November 9, 2026. The working Gemini default is `gemini-3.1-flash-lite`; the previous 2.5 model returned 404. See [the audio/compliance audit and live testing workflow](docs/AUDIO_COMPLIANCE_REVIEW.md).

Audio processing success does not establish compliance or identity. Optional speaker verification remains disabled. Artist identity and usage attestation is bound to the exact audio/campaign/transcription/approved version; unresolved identity, authorization, scope or uncertainty blocks royalty proposals and approval/invoice creation. Manual confirmation is not biometric or legal proof. Existing historical entries remain visible and must satisfy current eligibility checks before further approval or invoice creation.

## Artist voice to studio advertisement

Artists upload a private reference, approve a licensing PDF, and explicitly grant the assigned studio Gemini voice generation using a separate authentic speaker-consent recording. Studios open **Generate advertisement**, select that version-bound grant, enter script/campaign details, and create a recording for the existing analysis/artist-review/royalty workflow. No consent, biometric identity, compliance or charge approval is inferred from generation. Existing upload workflows remain available.

Generation defaults off. Add `ENABLE_VOICE_GENERATION=true` yourself in `backend/.env` and restart; retain the existing backend-only Gemini key. `GEMINI_VOICE_REPLICATION_MODEL` selects voice creation (default `gemini-3.8-flash-tts`); `GEMINI_TTS_MODEL` selects later synthesis (default `gemini-3.8-flash-lite-tts`). Both appear before generation and in new receipts, with no automatic model fallback. This separates the owner's Flash-Lite replication rejection from synthesis; successful live replication/generation remains unverified. Google replication requires paid-tier access and authentic reference/consent audio. See [the complete Gemini voice setup](docs/GEMINI_VOICE_WORKFLOW.md). Schema 6 adds only grant/generation history after backup; original records remain intact. PayPal write approvals remain separate.

Latest voice-error diagnostic verification: **246 backend tests**, Ruff, frontend TypeScript/ESLint and the 21-page production build pass. New failures identify replication versus synthesis and a sanitized reason category without storing provider bodies or secrets. HTTP 400 alone does not establish a schema problem. A live read-only Voices catalog request and local normalization of the actual reference/consent recordings succeeded; neither proves replication acceptance. The owner will perform the next live test. Saved failed jobs never replay automatically; use **Start a new generation request** deliberately for a new attempt. No live retry or PayPal operation was performed during this fix.

Gemini workflow checkpoint: **209 backend tests**, Ruff, TypeScript/ESLint, 21-page Webpack production build and **26 Edge browser tests** pass. Eight additional artist/studio responsive checks report no overflow or browser errors. Real FFmpeg conversion to 24kHz mono PCM16 was smoke-tested. External generation/provider failures are tested using mocked HTTP; the read-only model lookup is the only live Gemini call for this addition.

## Checks

Latest financial-condition fix: compliance policy **5**, **231 backend tests**, Ruff and frontend typecheck/lint/production build pass. Supported spoken-duration/proportional/HALF_UP special clauses are enforced deterministically with real citations; speech measurement remains deferred until analysis. Unknown/conflicting rules remain held. Restart the backend and reevaluate older reports before further financial approval; approved terms and historical invoices remain unchanged. See [compliance semantics](docs/COMPLIANCE_RULES.md).

Latest duration-validation fix: **214 backend tests/Ruff**, frontend typecheck/lint/production build and **four relevant Edge generation checks** pass. Errors identify the reference or consent recording and measured duration. References require 10–30 seconds; the separate consent statement does not need to last 30 seconds. Existing longer references remain stored and are marked ineligible for replication. No live voice request or PayPal write was performed.

New tools: **Audio submissions → Passport** traces a recording through its exact approved terms, analysis, compliance, artist decisions and financial history. **Review Center** supports artist concerns/studio responses with financial holds. **Royalty simulator** provides Studio-only, read-only Decimal previews. Print/save passports privately through the browser. Schema 5 adds evidence history/review threads with a consistent pre-upgrade backup. See [the product upgrade guide](docs/PRODUCT_UPGRADE.md).

Landing hydration regression: `frontend/tests/hydration.spec.ts` checks the actual browser console on desktop/mobile and the no-JavaScript fallback. The decorative still is a checked-in SVG; regenerate it only when changing the artwork with `node scripts/generate-voice-still.mjs` from the repository root. Do not generate raw floating-point SVG coordinates during server/browser rendering. See [the verified UI repair](docs/SPATIAL_UI_REVIEW.md#landing-hydration-repair).

Backend (FFmpeg must be on PATH; this workspace's tests also find the portable tools automatically):

Test runs use isolated ignored `.tmp/pytest/run-*` directories, avoiding shared Windows temporary-folder permission errors. Tests use the backend working directory consistently, so the root command `.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q` also runs the complete suite. No administrator shell or Windows permission changes are needed. See [testing instructions](docs/TESTING.md).

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app tests optional-speaker
Set-Location ..
```

Frontend, using this workspace's portable Node:

```powershell
$env:Path = (Resolve-Path .\tools\node).Path + ';' + $env:Path
Set-Location frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
# With both servers running and local fixtures generated; uses installed Microsoft Edge:
npm.cmd run test:e2e
Set-Location ..
```

Use system `node`/`npm.cmd` without the PATH line on a fresh system installation. Browser tests write only to the local demo DB and ignored screenshot/trace folders; they create clearly named demo agreements. Production mode: run `npm.cmd run build`, then `scripts/frontend.ps1 -Production` in place of the dev helper.

## Scope and practical limits

- Private file endpoints and service ownership checks are implemented. Fixed demo identity headers are selectable by anyone who can access the local backend. Production requires real authentication, authorization hardening, request throttling, a retention/deletion policy, and security review.
- Text PDFs only; no OCR. WAV/MP3/M4A, one audio track, no video, maximum 24 MiB and 600 seconds. Limits are deliberately conservative for Groq free-tier uploads.
- WebRTC VAD measures estimated speech separately from total recording length. Music, noise, and multiple speakers can reduce accuracy. Unavailable/empty measurements require review; total duration is never silently billed as speech.
- Content classification is advisory. Possible AI-detected prohibition requires review. Explicit declared out-of-scope usage is restricted. Neither outcome creates an invoice.
- Medium comparisons use documented canonical equivalents (for example online advertising / online commercial advertisements) while preserving TV, podcast and other distribution boundaries. Unknown semantic variants require review. US/United States and explicit prohibited-category synonyms are normalized. Geographic distribution/publication cannot be proven from audio. See [compliance rules](docs/COMPLIANCE_RULES.md).
- Active contract versions and allocated usage are immutable. Create a new agreement for changed contract terms. Metadata on held/restricted submissions can be corrected and reevaluated before a royalty exists. Resolving disputed content findings is a manual process outside automatic charging in this MVP.
- Cumulative allowance is reserved by permitted evaluations in transaction order, including zero-charge entries. Rejected charges do not erase consumed usage. Currency totals stay separate. The royalty engine supports USD/EUR/GBP with half-up cent rounding; the initial actual Sandbox invoice adapter accepts USD only.
- SQLite schema v4 retains append-only overlap reviews/royalty approvals and adds provider metadata, durable payment operations and webhook receipts. An existing database receives a consistent SQLite backup under ignored `backend/backups/` before upgrade. No existing tables/approved contracts/financial records are rewritten. Compliance policy v4 adds canonical usage and stable review binding. No destructive reset is provided.
- Processing is synchronous with visible loading/errors and explicit retry, optimized for local use. SQLite serializes transactions to prevent double allocations. A production job queue is outside this MVP.
- Optional ECAPA-TDNN worker is isolated and not connected to core decisions. Its input/failure paths are tested; actual model inference/download is unverified and deliberately not performed on this laptop.
- Exact file/decoded-audio duplicates and substantial transcript-overlap signals require artist review. Same usage links to the earliest canonical record without a second allocation; explicitly separate usage follows approved billing rules; uncertain/stale decisions stay held. Conflicting historical allocations and longer edits need reconciliation. Transcript overlap is conservative and is not proof of audio or speaker identity.

Audio detail pages display independent processing, compliance, manual authorization, royalty and provider-specific invoice states. Identical review/metadata saves and unchanged provider receipt timestamps do not repeatedly invalidate valid decisions. Fresh evidence-bound artist charge approval is required immediately before invoicing; legacy approvals without that proof require renewal. See [PayPal integration readiness](docs/PAYPAL_INTEGRATION_READINESS.md) for the remaining actual Sandbox financial verification.

Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Provider setup: [docs/API_SETUP.md](docs/API_SETUP.md). Progress: [PLAN.md](PLAN.md). Submission status: [docs/HACKATHON_SUBMISSION.md](docs/HACKATHON_SUBMISSION.md).
