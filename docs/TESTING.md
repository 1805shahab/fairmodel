# Testing FairModel on Windows

Fish generation: `backend/tests/test_fish_generation.py` uses MessagePack with real HTTPX request serialization against MockTransport, never a real endpoint. It covers the exact free header, audio bytes, validated output, safe failures/no redirects/retries, provider-specific consent, ownership, scope/stale/revoked grants, duplicate intents, preserved migration relationships and the existing authorization/Decimal royalty handoff. `scripts/fish_live_smoke.py` is separately manual and dry-run by default; do not add `--execute` to automated tests. See [free-tier/retention findings and live-test procedure](FISH_AUDIO.md). Normal tests and QA blank `FISH_API_KEY` and disable Fish.

Gemini generation milestone: **209 backend tests** and **26 Edge tests** pass, with Ruff/TypeScript/ESLint and the 21-page production build. `backend/tests/test_voice_generation.py` includes real installed SDK serialization with mocked HTTP, consent/role/version/revocation checks, no hidden retries/fallbacks, no automatic finance, duplicates and generated-audio handoff through manual authorization to USD 30.00 at 45 mocked measured seconds. `frontend/tests/voice-generation.spec.ts` uses synthetic silence and explicit isolated grants; provider generation is intercepted, never a real speaker clone. Eight responsive checks and a real FFmpeg 44.1kHz stereo-to-24kHz mono normalization smoke pass. The live Gemini check retrieved only model metadata; no real consent/replication/generation or PayPal write occurred. See [GEMINI_VOICE_WORKFLOW.md](GEMINI_VOICE_WORKFLOW.md).

## Product upgrade regressions

`backend/tests/test_passports.py` covers ownership/stability/exact contract version, preserved analysis/compliance/authorization history, failed reassessment, campaign correction, simulated labels, review idempotency/permissions, stale approval/canonical usage holds, Decimal preview cases, no-write estimates and migration. `test_paypal.py` also checks the returned mock-HTTP Sandbox ID and partial payment. These do not perform actual financial operations.

`frontend/tests/passport.spec.ts` prepares a fictional first-party fixture only in the isolated mock QA backend, then verifies saved passports, genuine citations, print/PDF output, artist/studio review threads, unchanged invoice/stale approval, no-write estimator amounts, and valid/missing timestamps. Timestamp data is injected into a browser response, not persisted or claimed live. The new suite refuses a non-mock backend. Test PDFs/screenshots stay ignored and private.

Use the isolated backend (`.\backend\.venv\Scripts\python.exe scripts/qa_backend.py --port 8002`), a built frontend launched with `BACKEND_URL=http://127.0.0.1:8002` and `scripts/frontend.ps1 -Production -Port 3001`, then set `$env:PLAYWRIGHT_BASE_URL='http://127.0.0.1:3001'` before `npm.cmd run test:e2e` from `frontend`. QA keys are blanked and records persist across reruns. Do not run mutation suites against the owner's original DB or enable Sandbox writes to satisfy tests. Live provider checks are separate evidence. Final results are in PLAN.md.

## Sandbox integration milestone

Normal tests blank AI/PayPal keys and mock PayPal HTTP. New coverage includes OAuth expiry/failures, draft wire models, current approvals, concurrent/repeated create, timeout reconciliation, send idempotence, partial/pending/paid/refund totals, failed/stale snapshots, signed/replayed/out-of-order webhooks, ownership and additive schema migration. Browser tests now include two Sandbox UI tests with mocked backend responses, alongside the complete local fixture workflow. No automated test creates a live draft or sends email.

```powershell
Push-Location backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app tests optional-speaker
# Explicit read-only live diagnostic; uses existing backend settings.
.\.venv\Scripts\python.exe ..\scripts\paypal_diagnostic.py --capability
Pop-Location
```

Live draft/send helpers require a reviewed amount/recipient and explicit authorization flag; do not include them in normal CI/test scripts. Manual steps and no-write defaults: [PAYPAL_SANDBOX_TESTING.md](PAYPAL_SANDBOX_TESTING.md). Actual OAuth/read-only access succeeded; actual draft/send/payment and live webhook delivery remain unverified. The placeholder Postman collection was parsed locally, not executed in Postman.

Run commands from `C:\Users\shaha\OneDrive\Desktop\Work\fairmodel` unless a block changes location. Keep real keys in the existing backend environment file; never paste them into commands, screenshots, test fixtures or frontend variables. The tests below do not require PayPal or real AI credentials.

## Backend regression checks

Tests automatically use a unique ignored `.tmp/pytest/run-*` directory inside this repository for temporary databases, uploads and pytest's `tmp_path` fixtures. This avoids Windows `PermissionError: [WinError 5]` when an old shared `%TEMP%/pytest-of-shaha` directory is inaccessible. Runs are separate and cleaned up at process exit; no administrator shell, permission changes or deletion of that shared folder is required. An explicitly supplied `--basetemp` is respected; pytest clears that directory, so it must be dedicated test storage, never the runtime database/uploads or repository root. See [pytest temporary-directory documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html#temporary-directory-location-and-retention).

Each test uses the backend's normal working directory, restored afterward, so bundled fixture lookups work consistently. This avoids missing-media skips and fixture-hash errors when pytest is launched from the repository root. The command also works directly from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
```

```powershell
Set-Location 'C:\Users\shaha\OneDrive\Desktop\Work\fairmodel'
Set-Location backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app tests optional-speaker
Set-Location ..
```

Tests override settings before importing the application, blank AI keys and use temporary databases/uploads. They cover deterministic scope/financial examples, schema upgrades and backups, provider redaction/no-fallback paths, source evidence, stale attestations/approvals, permissions, graph contradictions, idempotence, canonical allocation, reconciliation, actual local PDF/audio processing and mock payment transitions. A separate test seeds A/B/C twice and verifies stable IDs/counts. Generate scenarios first if that media integration test reports a skip.

## Frontend checks

```powershell
$env:Path = (Resolve-Path .\tools\node).Path + ';' + $env:Path
Set-Location frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
Set-Location ..
```

Use system Node/npm without the PATH line on a fresh installation. The build uses Webpack because this machine's Application Control policy can block native SWC; the first WASM compilation can take longer. Do not switch back to Turbopack under that policy.

## Safe browser integration testing

Prepare first-party fixtures once:

```powershell
# Only if backend/fixtures/manifest.json is missing:
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-demo.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-scenarios.ps1
```

The stock-TTS generator needs Windows System.Speech for initially missing recordings. It makes no network calls or model downloads. Subsequent scenario runs preserve recordings and verify their hashes. Do not regenerate the base PDF casually; approved contracts retain their own private source copies.

Start the QA backend in terminal 1:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\qa_backend.py
```

It binds to 127.0.0.1:8001, forces empty AI credentials inside the child Python process, and stores only `.tmp/qa/fairmodel.db` and `.tmp/qa/uploads`. The ordinary database and backend environment file are untouched. Fixtures are still explicitly selected by tests; accidental live requests fail honestly.

After the production build, start the QA frontend in terminal 2:

```powershell
$env:BACKEND_URL = 'http://127.0.0.1:8001'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1 -Production -Port 3001
```

Run Edge browser tests in terminal 3:

```powershell
$env:Path = (Resolve-Path .\tools\node).Path + ';' + $env:Path
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:3001'
Set-Location frontend
npm.cmd run test:e2e
Set-Location ..
```

The browser tests exercise full PDF/review/real media/VAD/fixture content/artist approval/simulated settlement, mobile/error recovery, citations, paired playback/overlap decisions, invoice context/search and actual media seeking. Root and former `/control-room` redirects are tested against the single backend-connected workspace, including no automatic payment writes and a guarded Postman download. A separate source-level legacy preview-provider test remains; no fictional preview is routed. Sandbox UI tests mock provider responses and retain explicit confirmations. Browser records are named `Browser ...`; actions target that run's exact record. Test artifacts and QA databases remain isolated/ignored; no live financial operation or original database reset is part of these tests.

Keep enough free disk space for uploads, traces and compilation. HTTP 507 indicates full local storage; free space before retrying. Generated `frontend/.next/cache` can be rebuilt, whereas databases, backups and uploaded media must be preserved. The backend sanitizes storage/database errors and rolls back failed financial/database work.

## Real AI smoke check — separate from mocks/fixtures

With owner-configured Gemini/Groq credentials and authorized first-party inputs:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe ..\scripts\verify_live_ai.py
Set-Location ..
```

This intentionally uses the provider accounts' quota. It prints only sanitized aggregate results and stores a safe report in ignored storage. It performs actual Gemini extraction/content requests and Groq transcription; no approvals, invoices or payments. A failed call is not replaced with a fixture. Key presence is not proof of availability. Fresh real API checks passed on November 9, 2026 after allowing network access: 15 verified Gemini contract citations, live Groq transcription with 12 timestamp segments and completed Gemini content assessment. The overlap/financial milestone is separately verified with deterministic mocks and explicitly labeled fixtures, not falsely presented as a live financial-service test.

For the full live browser workflow, create a new authorized agreement/audio submission, leave extraction fixtures unchecked, select Live Groq/Live Gemini, inspect successful response provenance, record actual artist attestation, resolve related usage, and separately approve any eligible charge. The speaker experiment remains disabled. Mock payments remain simulated; actual Sandbox requires the separate explicit workflow above. See AUDIO_COMPLIANCE_REVIEW.md and COMPLIANCE_RULES.md.
