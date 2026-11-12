# FairModel

## Every voice deserves a fair share.

**A working AI voice licensing, compliance and royalty platform that keeps the artist in control—from an approved contract to a verified PayPal Sandbox invoice.**

Synthetic speech makes it easy to produce another advertisement. It makes answering the next questions harder: *Was this campaign authorized? Which agreement applies? How much licensed speech was used? Is another royalty owed? Has that invoice actually been paid?*

FairModel connects those decisions in one evidence-led workspace. Artists approve source-backed licensing terms and authorized voice use. Studios submit or generate campaign audio. AI helps extract contract terms and assess spoken content; deterministic rules enforce licensing scope and calculate the money. Human approvals gate invoicing, and PayPal—not a button click—establishes payment status.

Built for **Build What's Next with PayPal and AI**. This repository contains the runnable Next.js/FastAPI application, tests, deployment configuration, fixture generators and setup instructions. It is a functional hackathon application with demo personas, **not production authentication or a legal determination service**.

| Start here | Link |
| --- | --- |
| Source | [github.com/1805shahab/fairmodel](https://github.com/1805shahab/fairmodel) |
| Hosted preview | [fairmodel.onrender.com](https://fairmodel.onrender.com) — owner-deployed, password-protected, temporary storage |
| Run it yourself | [From-scratch Windows setup](#run-from-scratch-windows-powershell) |
| No provider keys? | [Offline judging scenarios](#option-a-offline-demo-no-provider-keys) |
| Real services | [Live AI and PayPal Sandbox](#option-b-live-ai-and-paypal-sandbox) |
| Submission copy and publishing checklist | [Hackathon submission guide](docs/HACKATHON_SUBMISSION.md) |
| License | [MIT](LICENSE); [third-party notices](THIRD_PARTY_NOTICES.md) |

**Judge access:** use the shared hosted-demo login below, or the complete local setup for a reproducible functional build. The Render preview cannot create/send PayPal invoices. A fresh checkout starts with new records; provider secrets, private recordings, databases and previously paid invoices are intentionally excluded. Verify public repository visibility and upload/link the public YouTube video before submission. Adding this README does not publish either.

## Hosted demo login

Open **[https://fairmodel.onrender.com](https://fairmodel.onrender.com)**. When the browser asks for a username and password, enter these **shared demonstration credentials** without quotation marks:

| Field | Value |
| --- | --- |
| Username | `fairmodel` |
| Password | `FULC+58Nr8xWs0APS7lJ7Vow/7o67GrUiAr6BRZ7WfU=` |

These owner-provided details are intentionally published for the temporary judging demo. They are the website entrance login, **not a PayPal account or an AI API key**. Once inside, use the demo-persona switcher to explore Artist and Studio in the same app. This login has not been independently retested as part of this documentation update.

Anyone with this login can access both personas, hosted demo records and enabled AI features. Use only fictional or explicitly authorized demonstration material; do not upload confidential contracts or private recordings to this shared instance. PayPal draft/send remains disabled on the free host. Allow time for Render to wake from inactivity, and remember that records/uploads can disappear on spin-down, restart or redeploy. See [hosting limits](#hosted-preview-and-demo-video).

## What the product does

| Capability | How it works today |
| --- | --- |
| Artist and studio workspace | One application with a clearly marked demo-persona switcher, role-specific views and backend ownership checks. |
| Contract intelligence | Upload a text-based PDF, extract page text, ask Gemini for structured terms, validate genuine source quotations, review/edit and activate an immutable approved version. |
| Consented voice generation | Separate provider-bound artist grants authorize the assigned studio to generate an advertisement. Fish and Gemini are separate adapters; generation never grants final usage or financial approval. |
| Audio analysis | Content/format validation, FFprobe metadata, FFmpeg preprocessing, WebRTC VAD speech intervals, Groq Whisper transcription, playback, timestamps and seeking. |
| Explainable compliance | Combine the exact approved contract version, declared campaign scope, measured audio, advisory Gemini findings, workflow evidence and artist authorization. |
| Overlap resolution | Flag exact files/normalized audio and substantial shared transcript passages; artist decisions record same usage, separate usage or uncertain, with notes and audit history. |
| Deterministic royalties | Python `Decimal`, per-asset or cumulative allowance, proportional additional spoken seconds and final `ROUND_HALF_UP` rounding. No LLM calculates authoritative charges. |
| Artist financial control | Evidence-bound usage attestations and separate charge approvals; changed inputs invalidate dependent decisions. Review holds block financial actions. |
| Genuine Sandbox invoicing | Backend OAuth, PayPal Invoicing v2 draft creation, separate sending, actual hosted invoice links, authoritative status refresh and event history. Mock invoices remain a distinct offline option. |
| Evidence and dispute review | Private Voice Usage Passport, append-only evidence revisions, Review Center threads and audit records. A passport is a workflow record, not a certificate. |
| Analytics | AG Grid Community over actual records: filters, sortable financial columns, invoice/provider context, row details and CSV export. |
| Connected interface | Responsive paper/ink/vermilion design, light/dark themes, keyboard page launcher, source highlights, action-required states and a Three.js sculpture labelled as artwork. |

### Who it is for

- **Independent voice artists:** define permitted use and retain a recorded say over replication, campaign authorization and charges.
- **Studios and advertising teams:** work from approved terms, submit campaign evidence and understand additional permitted usage before requesting an invoice.
- **Rights and operations reviewers:** inspect agreements, transcripts, measurements, decisions and payment events together instead of reconciling separate spreadsheets.
- **Judges and developers:** run repeatable fictional examples, inspect the API and distinguish live provider evidence from explicitly selected fixtures.

FairModel reviews submitted evidence. It does not monitor the internet, prove geographic distribution, establish legal ownership or automatically detect infringement or cloning.

## The end-to-end workflow

```text
Artist reference + licensing PDF
  → Gemini extraction → human review → approved contract version
  → Studio uploads an ad OR generates one under a provider-specific grant
  → FFprobe + FFmpeg + WebRTC VAD + Groq transcription
  → Gemini content observations + deterministic scope/workflow checks
  → Artist identity/use review + overlap resolution where needed
  → Decimal royalty calculation → separate artist charge approval
  → PayPal Sandbox draft → explicit send → buyer pays on PayPal
  → authoritative status refresh → evidence, analytics and audit history
```

Each stage is an application action. Uploading, generating or transcribing a recording does not make it compliant, independently identify its speaker, approve a charge or mark an invoice paid.

### How decisions are made

**Contracts.** `pypdf` extracts real PDF page text. The maintained `google-genai` SDK requests structured terms, validated with Pydantic and checked against supporting text. Missing/ambiguous terms require review; document text is untrusted data, not executable instructions. Activation requires an artist note and whole-version approval. Extracted terms are never automatically approved. Each asset retains its associated approved version.

**Audio.** WAV, MP3 and M4A are validated and decoded locally. Current application limits are 24 MiB and 600 seconds. Analysis normalizes to 16 kHz mono; WebRTC VAD estimates speech activity in 30 ms frames. Groq returns text and available segment timestamps. Total duration and estimated spoken duration remain separate. Unreliable speech measurement creates review rather than silently billing the full recording.

**Compliance.** Documented canonical mappings recognize equivalents such as online advertising and online commercial advertisements while preserving distinctions from television or podcasts. Metadata checks cover dates, territory, language and campaign scope. Recognized administrative obligations use stored workflow events; Gemini is not asked whether a review was spoken aloud. Unknown/mixed clauses, missing citations and uncertain content remain reviewable. Gemini cannot broaden approved permissions or dictate money.

| Status | Meaning |
| --- | --- |
| `COMPLIANT` | Available evidence satisfies applicable terms and mandatory authorization checks; no additional royalty is due. |
| `ADDITIONAL_ROYALTY_DUE` | Usage is eligible and permitted, required evidence is current, and measured additional usage is payable. |
| `NEEDS_REVIEW` | Identity/use authorization, overlap, evidence, interpretation or another requirement is incomplete, uncertain or stale. |
| `RESTRICTED_USAGE` | A substantiated applicable licensing restriction is violated. AI suspicion alone is not conclusive legal evidence. |

**Overlap.** Transcript similarity is possible-reuse evidence, not acoustic fingerprinting. Same-usage decisions link to a canonical usage and prevent duplicate allocation. Separate-usage decisions retain contractual billing semantics; uncertain decisions hold financial actions. Changed evidence can invalidate decisions. Conflicting historical finance is flagged for reconciliation, never silently deleted or rewritten.

**Royalties.** The independent engine calculates:

```text
additional seconds = max(0, accepted spoken seconds − remaining included allowance)
amount = additional seconds × approved per-second rate
```

The engine uses `Decimal` throughout and rounds the final amount to cents with `ROUND_HALF_UP`. Per-asset allowances reset for distinct licensed usages; cumulative allowances account for prior allocated permitted usage. The UI displays backend amounts without recomputing them.

| Accepted spoken seconds | Included seconds | USD per additional second | Additional royalty |
| ---: | ---: | ---: | ---: |
| 20.00 | 30 | 2.00 | $0.00 |
| 23.52 | 30 | 2.00 | $0.00 |
| 30.00 | 30 | 2.00 | $0.00 |
| 45.00 | 30 | 2.00 | $30.00 |
| 58.77 | 30 | 2.00 | $57.54 |

These examples assume additional use is permitted, measurement is accepted and eligibility checks are satisfied. Restricted/unresolved usage cannot become an automatic royalty invoice. Included usage is displayed as no charge, with no payable invoice.

**Payments.** Each invoice retains its provider. `MockPaymentProvider` performs persistent, labelled simulations; `PayPalSandboxProvider` uses actual Sandbox APIs. Creation and sending have separate default-off switches. Before either action, the backend rechecks contract, compliance, authorization, overlap, positive amount and artist approval. Durable operation intents and unique constraints prevent repeat-click duplicates. Unknown outcomes are held for reconciliation, not blindly replayed. Paid status requires authoritative PayPal evidence; sending is not payment confirmation.

## Tools and integrations

| Tool | Use in FairModel | Evidence and boundary |
| --- | --- | --- |
| Google Gemini / `google-genai` | Structured contract extraction and advisory content analysis; configured default `gemini-3.1-flash-lite`. | Live extraction/compliance verified; successful responses retain provenance. Model availability depends on account access. |
| Groq Whisper | Transcription with `whisper-large-v3-turbo`. | Live transcription verified; fixtures are explicitly selected and labelled separately. |
| Fish Audio | Optional reference-conditioned generation with exact requested `s2.1-pro-free`, inline MessagePack audio and artist-reviewed reference transcript. | Saved successful generation demonstrated. No reusable profiles, paid-model/provider fallback or automatic retry. Requested model is recorded; served model is not independently attested. |
| Gemini voice generation | Separate optional replication/TTS adapter with distinct requested replication/synthesis models. | Implemented and mock-tested; prior runtime model-access rejection means successful live replication remains unverified. Upload workflows do not depend on it. |
| FFmpeg / FFprobe | Decode, inspect, normalize and verify audio before asset creation. | Local processing, not an AI identity service. Fish requests completed MP3, validates framing/metadata, then converts and validates 24 kHz mono PCM16 WAV. |
| WebRTC VAD | Local speech intervals and estimated spoken duration. | Not speaker recognition. Silero is not the active VAD implementation. |
| PayPal Developer Platform | Sandbox OAuth and Invoicing v2, sending, hosted payment links and reconciliation. | An owner-completed Sandbox payment has been refreshed and verified paid. No production/real-money flow. |
| APIMatic PayPal Context Plugin 0.4.1 | Developer guidance for authentication, client lifecycle, resilience, errors and transport tests. | Guidance actually read/used. Inspected SDK map lacks Invoicing v2/webhook controllers; those use official REST documentation and HTTPX. Not a runtime payment dependency. |
| AG Grid Community | Actual-record royalty analytics, filtering, financial sorting, row details and CSV export. | Community features only; no AG Studio or Enterprise claim. |
| Postman | Credential-free API collection. | Structurally validated; execution in Postman is not claimed. Mutations are guarded by default. |
| Render | Owner-deployed single-service Docker preview. | Password-protected and ephemeral; PayPal create/send disabled. Local tests do not establish hosted provider availability. |
| Three.js / React Three Fiber | Original generative artwork with lazy loading, fallback and reduced-motion support. | “Artistic rendering of this voice. Not verification evidence.” |

Credentials stay backend-only. `DEMO_MODE=true` supports demo personas; it **does not automatically select AI fixtures**. A configured key proves configuration, not API success. Failed live requests return safe errors and never silently switch to fixtures or another provider.

Fish's free-model designation does not guarantee availability, unlimited usage, a DPA or zero retention. Review [consent/retention findings](docs/FISH_AUDIO.md) and current [Fish provider documentation](https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits) before transferring private references. Provider terms/output rights remain separate from the code license.

### Consented artist-voice generation and video scope

**The application supports generating an advertisement from an artist's consented reference voice through Fish Audio.** The artist uploads their own or an explicitly authorized reference, reviews its transcript, and grants the assigned studio provider-specific replication/processing permission for the approved license version. The studio enters a new script and permitted campaign metadata, then deliberately requests generation. A successful reference-conditioned Fish generation was tested and saved; the owner reported that it reproduced the reference voice. This is not independent biometric verification. Generated recordings still require normal audio analysis, compliance evaluation, artist campaign authorization and royalty review.

**The video's main walkthrough uses an original Windows stock-voice advertisement.** It separately shows the previously saved successful Fish generation and its provenance, without sending the private reference to Fish again. It does not show a fresh voice-cloning request during filming. The stock voice was a filming-material choice, not a replacement for the Fish integration. The new stock-ad USD 56.76 royalty and the separately refreshed earlier paid USD 17.46 Sandbox invoice remain different cases.

The complete copy-ready project story, including this distinction, is in [PROJECT_STORY.md](docs/PROJECT_STORY.md).

## Run from scratch: Windows PowerShell

Windows is the verified development platform. Optional stock-TTS fixture generators use Windows `System.Speech`. Docker, Codex, APIMatic, speaker models and provider keys are **not required** for the offline application.

### 1. Install prerequisites

Install **Git, Python 3.12, Node.js 22 or a compatible newer LTS, and FFmpeg with ffprobe** using their official installers or your package manager. Ensure they are on `PATH`, then open a new terminal:

```powershell
git --version
py -3.12 --version
node --version
npm.cmd --version
ffmpeg -version
ffprobe -version
```

The original laptop's ignored `tools/` folder is not in a clone. Install your own prerequisites. If `py` is unavailable but `python --version` reports Python 3.12, use `python` instead of `py -3.12` below.

### 2. Clone and install locked dependencies

```powershell
git clone https://github.com/1805shahab/fairmodel.git
Set-Location fairmodel

py -3.12 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt

Push-Location frontend
npm.cmd ci
Pop-Location

if (-not (Test-Path -LiteralPath backend/.env)) {
    Copy-Item -LiteralPath backend/.env.example -Destination backend/.env
}
```

Use the lock files and project virtual environment. The Python lock includes core/development tools but excludes optional speaker packages. Never overwrite an existing `.env` or commit credentials. Calling virtual-environment Python directly avoids activation-policy problems.

### 3. Start both servers

Open **two PowerShell terminals at the cloned repository root**. Start with explicit mock payments so no PayPal account is required.

Terminal 1:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1 -MockPayments
```

Terminal 2:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1
```

Open **http://127.0.0.1:3000**, then **Open workspace**. FastAPI schema/explorer: **http://127.0.0.1:8000/docs**. Backend health: **http://127.0.0.1:8000/health**. Keep both terminals running; Ctrl+C stops that terminal's process. Helpers set the correct working directories for configuration/storage paths. Both servers bind to loopback.

Startup initializes/upgrades SQLite and creates the two fictional personas. It does not automatically extract contracts, generate speech or create/send invoices. An empty dashboard on a fresh clone is expected.

**Launcher distinction:** `backend.ps1` without `-MockPayments` explicitly selects `paypal_sandbox` for its process, even when `.env` says `mock`. Draft/send remain off unless explicitly enabled. Direct Uvicorn honors `.env`. The helper never overwrites it.

### 4. Optional production-mode frontend

Stop the frontend before replacing it on the same port:

```powershell
Push-Location frontend
npm.cmd run build
Pop-Location
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1 -Production
```

Dev/build deliberately use **Webpack**. Windows Application Control on the development laptop blocks native SWC; Next.js's WebAssembly fallback works with Webpack, while Turbopack requires native bindings. First compilation can be slower. Do not disable Windows security policy to remove that warning.

## Option A: offline demo, no provider keys

Generate fictional PDF/audio locally, then seed repeatable cases. Run from the repository root in a third terminal:

```powershell
# Once on a fresh checkout; needs installed Windows stock speech support.
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-demo.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-scenarios.ps1

# Select mock explicitly for the seeding process. Sandbox seeding is refused.
$env:PAYMENT_PROVIDER = 'mock'
Push-Location backend
.\.venv\Scripts\python.exe ..\scripts\seed_demo.py
Pop-Location
```

Refresh the workspace and inspect **Judging scenarios — OFFLINE FIXTURES**.

| Scenario | Expected behavior |
| --- | --- |
| A: permitted short ad | Within allowance; `COMPLIANT`, $0 additional royalty, no payable invoice. |
| B: permitted longer ad | Measured additional speech; `ADDITIONAL_ROYALTY_DUE`; scripted **fixture-only** review and a simulated draft. |
| C: prohibited category | Restricted or evidence-dependent review; no automatic invoice. |

Seeding preserves other records and reuses the same bundle on rerun. Generated speech duration can vary between machines; actual measured royalties may differ. Do not force a target amount. Regenerating the base fixture changes its hash; use matching files/manifest together.

To test forms manually, use `backend/fixtures/sample-license.pdf` and `sample-narration.wav`. Explicitly select **Use local demo fixture** for extraction, fixture transcription, and fixture compliance. Complete contract review, studio upload, artist usage review, reevaluation, charge approval and simulated invoice/send/payment. Fixture AI and scripted attestations are not live AI or biometric proof; local PDF/audio/VAD/database processing is real.

If Windows speech generation is unavailable, the application still runs; use your own authorized text PDF/audio with live services. Do not apply fixture responses to arbitrary files or weaken hash checks. See [Demo guide](docs/DEMO_GUIDE.md).

## Option B: live AI and PayPal Sandbox

### Configure services privately

Edit **`backend/.env`** locally. Keep secrets out of frontend variables, shell commands, screenshots, logs and Git. Restart the backend after changes.

| Setting | Required for |
| --- | --- |
| `GEMINI_API_KEY`, optional `GEMINI_MODEL` | Live contract extraction/advisory compliance. Use a supported model available to your account. |
| `GROQ_API_KEY`, `GROQ_WHISPER_MODEL` | Live Whisper transcription. |
| `FISH_API_KEY`, `FISH_TTS_MODEL=s2.1-pro-free` | Optional Fish generation; also set `ENABLE_VOICE_GENERATION=true` and `ENABLE_FISH_GENERATION=true`. |
| `ENABLE_VOICE_GENERATION`, `GEMINI_VOICE_REPLICATION_MODEL`, `GEMINI_TTS_MODEL` | Optional Gemini replication/synthesis with required access/consent. Live success remains unverified. |
| `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_ENVIRONMENT=sandbox` | Sandbox merchant application authentication. |
| `PAYPAL_SANDBOX_MERCHANT_EMAIL`, `PAYPAL_SANDBOX_BUYER_EMAIL` | Distinct business issuer/personal buyer, matching the actual sandbox accounts. |
| `PAYPAL_WEBHOOK_ID` | Optional verified webhook integration; not needed for direct refresh. |
| `PAYPAL_ALLOW_DRAFTS`, `PAYPAL_ALLOW_SENDING` | Separate default-off write controls; local helper switches override them for that process. |
| `DATABASE_URL`, `STORAGE_DIR`, `FFMPEG_BINARY`, `FFPROBE_BINARY` | Local persistence/audio tools; defaults in the example file. |

Keep `DEMO_MODE=true`; disabling it does not enable production authentication and validation refuses that unsupported mode. Core operation requires no PayPal, Fish or optional speaker credentials/packages.

### Artist → studio → review

1. **Artist / Reference voice:** upload your own or an explicitly authorized adult speaker's sample and acknowledge storage/comparison consent. This does not authorize cloning or third-party transfer.
2. **Artist / Voice licenses:** upload a text PDF, leave fixture mode unchecked and run Gemini extraction. Inspect citations, edit/resolve terms, add the review note and activate the version. Scanned-PDF OCR is not implemented.
3. **Optional generation grant:** choose the provider and authorize the assigned studio for that approved version. Fish requires its own transfer/retention/terms consent and reviewed reference transcript; Google permission never authorizes Fish. Recording requirements appear in the form/provider guides.
4. **Studio / Submit audio or Generate advertisement:** select the agreement; provide permitted campaign, territory, medium, language, category and intended-use date. Upload authorized audio or deliberately confirm one generation request with the matching grant. A generated recording starts as `UPLOADED`, without automatic final authorization/charge.
5. **Audio detail:** play it; select **Live Groq Whisper**, analyze and inspect text/timestamps, total duration and VAD speech. Select **Live Gemini** and evaluate. Results show actual provenance; errors remain visible and require a deliberate retry/new request where supported.
6. **Artist review:** inspect audio/clauses/findings, record identity/use attestation with a note, resolve overlap as same/separate/uncertain, and use Review Center for disputes. Reevaluate after resolution. Do not remove restrictions to unblock a case.
7. **Royalties:** inspect the backend calculation. Included usage has no payable invoice. Record a separate charge approval for eligible positive usage. Stale evidence, open cases and unresolved overlap still block invoicing.

Use a distinct original fictional ad for a positive-royalty demo; measure actual speech rather than fabricating 45 seconds. Similar excerpts can correctly trigger review. The Studio estimator previews approved rules without usage/financial/provider writes.

### Genuine PayPal Sandbox payment

Use only sandbox accounts. The configured merchant issues all invoices; arbitrary artist merchant onboarding is outside this MVP. Sandbox invoices currently support USD.

First run the **authentication/read-only diagnostic**, which creates/sends no invoice:

```powershell
Push-Location backend
.\.venv\Scripts\python.exe ..\scripts\paypal_diagnostic.py --capability
Pop-Location
```

For a specifically reviewed positive royalty, stop the old backend and deliberately enable local draft/send:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1 -PayPalSandbox -EnableSandboxDrafts -EnableSandboxSending
```

These switches enable capabilities; startup performs no financial operation.

1. As artist, approve the eligible charge and click **Create / open PayPal Sandbox draft**. Inspect the exact case, issuer, buyer, amount/currency in the confirmation before accepting.
2. Inspect the real returned invoice ID and draft. **Send** is a separate explicit action; confirm the intended sandbox recipient.
3. As studio, open the **actual API-returned hosted invoice link**, log into the personal **Sandbox buyer** on PayPal and manually complete test checkout. FairModel never needs/stores the buyer password. Do not send a separate “Send money” transfer.
4. Return and click **Refresh PayPal status**. Await the authoritative result. Partial/pending/refund states remain distinct. Sending or a paid-named webhook alone cannot establish paid status.
5. Inspect events, outstanding amount and last sync. An uncertain write requires reconciliation, not repeated new invoice creation.

Sandbox: **PAYPAL SANDBOX — TEST TRANSACTION — NO REAL MONEY**. Mock: **DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED**. Neither represents production earnings. Signature verification/replay handling is implemented and mock-tested; public webhook delivery is not verified. Direct refresh needs no tunnel/webhook. See [Sandbox testing/recovery](docs/PAYPAL_SANDBOX_TESTING.md).

## Architecture and repository map

| Layer | Current implementation |
| --- | --- |
| Presentation | Next.js App Router, React, strict TypeScript, Tailwind, Radix, self-hosted fonts, Three.js and AG Grid Community. |
| API boundary | Same-origin `/api/backend/*` proxy forwards the supported demo persona to a fixed backend; private PDF/audio ownership checks. No provider keys in browser code. |
| Domain API | Python 3.12, FastAPI/OpenAPI, Pydantic, SQLAlchemy and modular domain/provider services. |
| Persistence | SQLite, approved immutable versions, evidence revisions, append-only decisions/audit. Money/durations stored as decimal strings. |
| Schema management | Versioned development migrations, currently schema 7, with consistent pre-upgrade backups. No Alembic or reset required. |
| Financial consistency | Serialized write transactions, constraints, evidence-bound approvals and durable provider-operation intents; no silent historical invoice rewrite. |
| Hosting | One Docker service packages Next.js/FastAPI/FFmpeg; API stays loopback-only. Render Free uses isolated temporary storage. |

```text
frontend/app/                 Routes, layouts and same-origin API handlers
frontend/components/          Shared forms, player, ledger, artwork and presentation
frontend/tests/               Edge Playwright workflows and state checks
frontend/public/fonts/        Self-hosted fonts and original OFL notices
backend/app/main.py           Core endpoints/workflow orchestration
backend/app/ai.py             Gemini contract/content and Groq adapters
backend/app/audio.py          Probing, normalization and speech measurement
backend/app/contract_rules.py  Deterministic scope/condition routing
backend/app/royalties.py       Independent Decimal calculation
backend/app/voice_routes.py    Provider-bound grants/generation intents
backend/app/fish_*.py          Fish client, container validation and normalization
backend/app/paypal_*.py        Sandbox OAuth, invoicing, reconciliation, webhooks
backend/app/payments.py        Payment abstraction and mock provider
backend/app/db.py              Persistent entities and relationships
backend/app/migrations.py      Versioned upgrades and SQLite backups
backend/tests/                Domain, API, provider, migration, integrity tests
backend/optional-speaker/      Isolated experimental worker, not core requirements
scripts/                      Launchers, fixture generators, QA and manual smoke tools
deploy/                       Hosted-demo supervisor and tests
postman/                      Guarded credential-free collection
docs/                         Architecture, providers, design, testing and demo
Dockerfile / render.yaml       Single-service temporary Render configuration
```

Defaults store records in `backend/fairmodel.db`, uploads in `backend/storage/` and fixtures in `backend/fixtures/`, all ignored by Git. Back up SQLite consistently **with matching uploaded files**; copying only a live database can miss WAL data. Deleting the DB is not a troubleshooting step. Fresh clones cannot show the owner's private paid invoice without separately authorized data transfer.

## Testing and verification

Normal tests blank provider keys and use isolated databases/media under ignored `.tmp/` with mocked external HTTP. They verify serialization/domain behavior without cloning private voices or sending invoices.

Backend, from the root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests deploy/tests -q
.\backend\.venv\Scripts\python.exe -m ruff check backend deploy
```

Frontend:

```powershell
Push-Location frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
Pop-Location
```

For browser tests, prepare fixtures above and ensure **Microsoft Edge is installed**. Use three terminals; do not run mutation suites against original runtime records.

Terminal 1 — isolated mock API:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\qa_backend.py --port 8001
```

Terminal 2 — previously built frontend:

```powershell
$env:BACKEND_URL = 'http://127.0.0.1:8001'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1 -Production -Port 3001
```

Terminal 3:

```powershell
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:3001'
Push-Location frontend
npm.cmd run test:e2e
Pop-Location
```

QA blanks AI/payment keys, disables generation and keeps its own `.tmp/qa` records. Coverage includes roles, citations, financial examples, scope, stale reviews, overlap, errors, duplicates, payment states and private evidence views. Some media cases require generated fixtures; skips are not proof of audio processing.

**Latest recorded code baseline:** 384 Python tests (370 application + 14 deployment), Ruff, TypeScript/ESLint/build and 38 Edge checks passed during deployment preparation. These are historical verified runs in [PLAN.md](PLAN.md), not guarantees for a new machine. Documentation/media-only work did not rerun every code suite.

**Live evidence from the November 12 recording:**

- Gemini extracted 19 real citations; Groq transcribed the original fictional stock-voice ad.
- FFprobe: 69.613 total seconds; WebRTC VAD: 58.38 spoken seconds. Following explicit fictional-demo artist review, live Gemini plus deterministic rules returned `ADDITIONAL_ROYALTY_DUE`, **USD 56.76**. No invoice was created for this new case.
- Initial live Gemini HTTP 503 stayed visible; a deliberate retry succeeded without fixture fallback.
- A **separate previously owner-paid USD 17.46 Sandbox invoice** was refreshed against PayPal: `PAID`, USD 17.46 paid, zero outstanding. This is not payment for the new USD 56.76 example.
- Fish footage shows an earlier saved successful generation, not a new clone or independent identity proof. Successful live Gemini replication/public webhook delivery remain unverified.

Live smoke tools are separate: `scripts/verify_live_ai.py`, `scripts/paypal_diagnostic.py` and dry-run-first `scripts/fish_live_smoke.py`. Actual AI uses quota/transfers submitted inputs; run only with authorized materials. Never automatically execute live Fish or PayPal financial tests. See [test guide](docs/TESTING.md).

## Hosted preview and demo video

The owner deployed **[fairmodel.onrender.com](https://fairmodel.onrender.com)** and authorized publishing its [shared demo login](#hosted-demo-login) for judges. Provider API keys and PayPal credentials remain private. Check cloud reachability and actual provider operations before judging; local tests do not establish that the host is awake/configured.

The free preview is limited. [Render documents](https://render.com/docs/free) 15-minute idle spin-down, cold starts of about a minute and loss of local filesystem changes on spin-down/restart/redeploy. FairModel uses a fresh temporary cloud DB/uploads and blocks PayPal draft/send there. Configure keys privately before uploading; redeployment discards cloud records. Durable local payment history is not in the image. See [deployment guide](docs/RENDER_DEPLOYMENT.md).

Local delivery includes the **2:59 narrated 1080p demo** (`FairModel-hackathon-demo-NARRATED-1080p.mp4`), the original voiceover-ready edit, a **5:38 extended walkthrough** and narration scripts under ignored `output/video/`. The narrated cut includes the owner's complete 3:11.12 recording, fitted with a pitch-preserving 7.37% speed increase, consistent loudness and retimed picture chapters. No spoken content was cut; a short original stock-ad excerpt plays during the narrator's pause. The film shows actual actions, live AI and the separate earlier Sandbox refresh. Original edits remain unchanged; the extended edit is supplemental, not the required under-three-minute video.

**Public YouTube video: not linked yet.** Review and upload the narrated final, then add its public URL here and to the submission form. A local MP4 does not satisfy the YouTube requirement. Review rights for visible third-party marks/media/participants; no music was added. The setup instructions remain a functional-demo path if the temporary host is unavailable.

## Security, consent and current limitations

- Demo personas/shared hosted password are not production accounts, tenant isolation or legal identity checks. Use fictional/authorized inputs; do not expose the local API as a production service.
- Storage consent, provider-specific replication consent, final campaign authorization and charge approval are separate. Studios cannot submit artist decisions through supported endpoints.
- Manual review is attestation, not biometrics. Optional SpeechBrain ECAPA-TDNN is isolated, uncalibrated and unverified with real inference; core installs download no speaker model. Similarity would not prove cloning, infringement or consent.
- Gemini findings are advisory. Untrusted-data treatment, structured validation and evidence/authority boundaries reduce prompt-injection risk; they do not prove perfect resistance/legal correctness.
- Declared territory/publication is not independently verified. Transcript overlap can miss reuse or flag similar wording; it is not robust acoustic fingerprinting.
- Selected features transfer text/audio to their providers. Provider terms/retention apply; Fish free has no verified zero-retention/DPA guarantee.
- SQLite/local files and synchronous processing suit a small demo. No durable job queue, scanned-PDF OCR, automated production retention, arbitrary merchant onboarding or production PayPal is implemented.
- Code licensing does not grant rights to user uploads, logos, voice models or provider output. Retain dependency/font notices and obtain demo-media permissions.

## Future improvements

| Priority | Improvement | Purpose |
| --- | --- | --- |
| 1 | Real artist/studio authentication, tenant roles and secure sessions | Replace personas before accepting real customers/sensitive contracts. |
| 1 | Durable storage, tested restore and deliberate database migration | Preserve evidence/operation intents across hosting restarts; current SQLite-only settings are not a drop-in Postgres integration. |
| 1 | Durable background audio/AI jobs and explicit retry policy | Improve responsiveness/recovery without duplicate generation or financial writes. |
| 1 | Live webhooks and broader real Sandbox reconciliation verification | Complement manual refresh; exercise pending/partial/refund/out-of-order cases. |
| 2 | Structured ambiguous-clause review, OCR and reviewer assignments | Reduce friction while preserving source evidence/human authority. |
| 2 | Evaluated acoustic fingerprinting and calibrated optional speaker comparison | Improve reuse triage with measured accuracy/privacy safeguards, never equating similarity with permission. |
| 2 | Retention/deletion/export controls, encrypted storage and provider agreements | Make sensitive voice-data handling operationally enforceable. |
| 2 | Merchant onboarding, additional currencies and reviewed refund/settlement flows | Extend the single-merchant USD Sandbox MVP after legal/provider review. |
| 3 | Verified additional generation models and localization | Expand through evaluation, not silent model fallback. |
| 3 | User research, independent accessibility audit and larger-ledger performance tests | Validate beyond automated checks with working artists/studios. |

These are planned directions, not shipped capabilities. The distinction is the connection between source-backed rights, measured usage, human authorization and reconciled payment—not automated legal judgment or an autonomous money-moving agent.

## Troubleshooting

| Symptom | Next step |
| --- | --- |
| Port 3000 will not open | Keep frontend running and wait for ready; keep backend running for API views. |
| `EADDRINUSE` | Check whether the existing app already opens. Stop only the server you own or use `frontend.ps1 -Port 3001`. |
| SWC blocked / slow first compile | Keep supplied Webpack commands; allow initial WASM compilation. |
| FFmpeg unavailable | Verify both binaries on PATH in a new terminal; restart backend. |
| Configured provider fails | Inspect saved safe error; privately check quota/model access/key. Configuration is not API success. |
| New royalty absent | Analyze/evaluate, complete artist/overlap reviews, reevaluate. Unresolved usage correctly has no proposal; included usage has no payable invoice. |
| Sandbox writes disabled | Enable deliberate local switches only for an approved case; free hosted writes remain blocked. |
| Invoice uncertainty/mismatch | Preserve operation/remote ID; verify accounts/evidence and reconcile. Do not delete claims or repeatedly create. |
| Cloud records disappeared | Free hosting is temporary. Git cannot restore excluded private records. Keep durable local evidence. |
| Fixture hash mismatch | Use the exact matching generated bundle; do not loosen validation. |

## Documentation and contributing

- [Architecture](docs/ARCHITECTURE.md), [provider/API setup](docs/API_SETUP.md), local `/docs`
- [Compliance rules/citations](docs/COMPLIANCE_RULES.md)
- [Fish](docs/FISH_AUDIO.md), [MP3 integrity handling](docs/FISH_MP3_OUTPUT.md), [Gemini voice workflow](docs/GEMINI_VOICE_WORKFLOW.md)
- [Sandbox manual testing](docs/PAYPAL_SANDBOX_TESTING.md), [sponsor contributions](docs/SPONSOR_INTEGRATIONS.md)
- [Passports/review threads/estimates](docs/PRODUCT_UPGRADE.md), [design verification](docs/LEDGER_UI_REDESIGN.md)
- [Demo guide](docs/DEMO_GUIDE.md), [testing](docs/TESTING.md), [submission copy/checklist](docs/HACKATHON_SUBMISSION.md)
- [Verified milestones and historical notes](PLAN.md)

Read [AGENTS.md](AGENTS.md) before contributing. Preserve records/approvals, use isolated tests and never commit private media/secrets. Normal development must not trigger live generation, sending or payment. Mock provider tests and separately authorized live verification must be reported distinctly.

First-party source is under the [MIT License](LICENSE). Dependencies/fonts retain their licenses; see [third-party notices](THIRD_PARTY_NOTICES.md). No affiliation, sponsor endorsement, prize eligibility or production security certification is implied.
