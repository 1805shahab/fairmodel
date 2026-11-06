# FairModel

**Every voice deserves a fair share.** AI voice licensing, explainable compliance, and artist-approved royalties.

Source repository: [1805shahab/fairmodel](https://github.com/1805shahab/fairmodel) (private).

Local full-stack hackathon application: Next.js App Router/React/TypeScript/Tailwind, FastAPI/Python 3.12, SQLAlchemy/SQLite, Gemini (`google-genai`), Groq Whisper, FFmpeg/ffprobe, WebRTC VAD, and AG Grid Community.

**Payments are simulated. No PayPal authentication or API calls are implemented or attempted.** Real PayPal Sandbox integration remains a required final hackathon milestone, deferred until account access is restored and the owner explicitly authorizes it.

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

The landing page opens the workspace. Use the top-right demo persona switcher for **Amara Reed / Artist** and **Northstar Studio**. These are fictional demonstration identities, not production authentication.

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

See [the three-minute guide](docs/DEMO_GUIDE.md). Download fixtures from **Demo & integrations**. Artist: create license → upload sample PDF → explicitly select local fixture extraction → review terms/source quotes → add review note → approve. Studio: submit narration with US / online advertising / English → explicitly select fixture mode → analyze → evaluate. Artist: approve proposed royalty → create simulated invoice → simulate send. Studio: simulate payment completion. Inspect AG Grid analytics and audit records.

Every payment screen displays **DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED**. Simulation sends no email and moves no funds.

For real AI, configure only `backend/.env` with `GEMINI_API_KEY` and `GROQ_API_KEY`, restart the backend, and **leave fixture checkboxes unchecked**. Configured status only indicates key presence, not a successful provider request. Missing keys or provider failures return useful errors without hidden fixture fallback. Real Gemini extraction/content assessment and Groq transcription were successfully smoke-tested with owner-configured credentials on November 6, 2026. The working Gemini default is `gemini-3.1-flash-lite`; the previous 2.5 model returned 404.

## Checks

Backend (FFmpeg must be on PATH; this workspace's tests also find the portable tools automatically):

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
- Scope comparisons are exact, case-insensitive labels. Use canonical metadata such as `US`, `English`, `online advertising`. Geographic distribution/publication cannot be proven from audio.
- Active contract versions and allocated usage are immutable. Create a new agreement for changed contract terms. Metadata on held/restricted submissions can be corrected and reevaluated before a royalty exists. Resolving disputed content findings is a manual process outside automatic charging in this MVP.
- Cumulative allowance is reserved by permitted evaluations in transaction order, including zero-charge entries. Rejected charges do not erase consumed usage. Currency totals stay separate. Supported currencies are USD/EUR/GBP with half-up cent rounding.
- SQLite schema v1 is initialized at startup (`PRAGMA user_version=1`). No destructive reset command or automatic migration is provided. Back up DB/uploads before future migrations.
- Processing is synchronous with visible loading/errors and explicit retry, optimized for local use. SQLite serializes transactions to prevent double allocations. A production job queue is outside this MVP.
- Optional ECAPA-TDNN worker is isolated and not connected to core decisions. Its input/failure paths are tested; actual model inference/download is unverified and deliberately not performed on this laptop.

Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Provider setup: [docs/API_SETUP.md](docs/API_SETUP.md). Progress: [PLAN.md](PLAN.md). Submission status: [docs/HACKATHON_SUBMISSION.md](docs/HACKATHON_SUBMISSION.md).
