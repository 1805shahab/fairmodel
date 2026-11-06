# FairModel implementation plan

Status: implemented and locally verified MVP, November 6, 2026. Workspace was empty. Python 3.12.10 was available; portable Node 22.23.4 and FFmpeg/ffprobe are now installed in ignored tools folders. The owner has authorized source publication to a private GitHub repository; deployment remains unauthorized.

- [x] Phase 0: inspect workspace; initialize local Git; record boundaries and architecture.
- [x] Phase 1: FastAPI, SQLAlchemy/SQLite schema v1, typed response/request schemas, Next.js navigation.
- [x] Phase 2: private PDF upload, real page extraction, Gemini SDK integration, source quotes, editable review, version checks, immutable approvals. Live extraction and content assessment verified with Gemini 3.1 Flash-Lite.
- [x] Phase 3: real FFmpeg/ffprobe validation/normalization, Groq SDK transcription, WebRTC VAD with uncertainty. Live Groq Whisper transcription verified with real timestamp segments.
- [x] Phase 4: explainable compliance, deterministic Decimal per-asset/cumulative royalties, concurrency and duplicate tests.
- [x] Phase 5: connected Artist/Studio workflows, role restrictions and assigned ownership, recoverable held-submission metadata.
- [x] Phase 6: persistent simulated invoices, artist charge decisions, deduplicated payment events, audit trail.
- [x] Phase 7: professional responsive UI, AG Grid, first-party fixtures, private playback, source-page links and integration tests. Desktop and mobile/error-recovery browser tests pass.
- [ ] Phase 8: isolated optional ECAPA-TDNN CLI and failure/input tests implemented. Actual model inference intentionally unverified; core flag remains disabled. No heavy dependency/model download.
- [x] Phase 9: README, API/architecture guides, three-minute demo, submission status and PowerShell helpers.
- [ ] Deferred: real PayPal Sandbox OAuth, Invoicing v2, verified/idempotent webhooks. Requires explicit user authorization after account access is restored.

## Verification log

- 47 backend Pytest cases pass, including actual PDF parsing and local FFmpeg/VAD media processing, provider error/schema paths, royalty examples, concurrency, cumulative allowances, ownership, version checks, full simulated settlement, secret-input redaction and optional-worker failures. One non-failing upstream Starlette/httpx TestClient deprecation warning remains.
- Backend Ruff lint passes. Source formatted with Ruff/Prettier. TypeScript, ESLint and production Next.js build pass for the final implementation.
- Desktop Microsoft Edge automated browser workflow passes from landing → PDF → extraction fixture → approval → audio playback/analysis → compliance → charge approval → simulated send/payment → real AG Grid ledger.
- Both Microsoft Edge Playwright tests pass (final run: 19.2s): desktop end-to-end workflow; mobile navigation, persisted persona, no horizontal overflow, explicit API error and successful retry recovery. Screenshots are generated in ignored `frontend/test-results/`.
- Live checks passed on November 6, 2026 using owner-configured backend keys and first-party sample inputs, with fixture mode disabled: Gemini contract extraction (14 verified source citations, zero unknown fields/review flags), Groq transcription (990 characters, 12 timestamp segments, 70.052s recording / 58.77s estimated speech), and Gemini content assessment. No database approvals, invoices or payments were performed by these checks. The safe aggregate report is ignored at `backend/storage/live-ai-verification.json`.
- The previous configured Gemini 2.5 Flash-Lite generation request returned 404. Model listing confirmed key access; the supported `gemini-3.1-flash-lite` replacement succeeded. Updated the code default, `.env.example` and only the non-secret model setting in the local `.env`; no key values were displayed or logged.
- Backend lint and all 47 automated tests pass after the model-setting update. Frontend behavior is unchanged; its prior build/browser checks remain applicable. Automated tests continue using mocks/explicit fixtures and are distinct from the actual live smoke checks.
- Speaker model not downloaded/run. PayPal intentionally deferred, not a completed integration. No external financial action occurred.

## Run commands

From the repository root in separate PowerShell terminals:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1
```

Open http://localhost:3000. Full setup and validation commands are in README.md. Local fixture files already exist in this workspace; fresh checkouts generate them with `scripts/create-demo.ps1`.

## Remaining external/optional work

1. Live Gemini/Groq service smoke checks are verified. Run the final manual judging workflow in the browser with fixture checkboxes unchecked; artist approvals remain required.
2. Optional speaker environment/model needs independent CPU/memory/quality validation before any core integration. Uncalibrated similarity must never trigger a royalty.
3. Owner restores PayPal Developer access and explicitly authorizes the deferred real Sandbox API phase before implementation/authentication.
4. Production identity, asynchronous job infrastructure, retention policies and deployment are outside the local demo scope.

## GitHub source publication

The owner explicitly requested creating a GitHub repository and pushing this project. Target: private `1805shahab/fairmodel`, branch `main`. Include source, documentation, dependency lock files, and sanitized environment examples. Exclude actual environment files, uploaded/generated media, databases, virtual environments, build outputs, logs, browser artifacts, and portable local tools. This authorization does not include deployment or the deferred PayPal integration.
