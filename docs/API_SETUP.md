# API and local tool setup

Copy `backend/.env.example` to `backend/.env` only if it does not exist. Edit secrets locally; do not paste them into chat, commits, screenshots, shell arguments or frontend environment variables. Launch the backend from `backend/` so relative DB/storage/config paths resolve consistently. The helper scripts do this automatically.

## Google Gemini

Set `GEMINI_API_KEY` and optionally `GEMINI_MODEL` (default `gemini-3.1-flash-lite`). The maintained `google-genai` SDK sends schema-constrained requests for Terms and ContentFindings. Requests have a timeout and no tools. Use a model available to your account; model availability and quotas may change. Leave contract fixture extraction unchecked and select **Live Gemini** for audio compliance. No separate flag enables Gemini: `DEMO_MODE=true` describes demo personas/payments, not an automatic choice of AI fixtures. Restart the backend after locally editing its environment file.

The original `gemini-2.5-flash-lite` setting returned 404 during live verification on November 6, 2026. Google's [supported-model documentation](https://firebase.google.com/docs/ai-logic/models?api=dev) documents that model's retirement and the 3.1 Flash-Lite replacement. Real extraction and content assessment succeeded with `gemini-3.1-flash-lite`.

The settings screen reports key presence without revealing it or asserting provider success. A real successful result records `gemini:<model>`. A 503 means missing credentials; 502 means provider or structured validation failure. Safe messages preserve upstream HTTP status/category (for example 404 model access or 429 quota); raw provider bodies/URLs/keys are never displayed. No demo result replaces a failed request. Previous evidence is labeled as history and charge eligibility is held until a successful retry.

New successful responses additionally record a `provider_receipt` with service, requested model, returned model/response identifier when actually supplied, completion time and schema-validation status. Historical IDs are not fabricated. Content assessment receives only content rules/transcript/category; administrative obligations are checked against database workflow receipts and the separate artist approval gate. See [COMPLIANCE_RULES.md](COMPLIANCE_RULES.md) for rule provenance, normalization and overlap limits.

Reference: [Gemini structured output documentation](https://ai.google.dev/gemini-api/docs/structured-output), [official Python SDK](https://googleapis.github.io/python-genai/).

## Groq transcription

Set `GROQ_API_KEY`, with `GROQ_WHISPER_MODEL=whisper-large-v3-turbo`. The SDK posts normalized WAV audio and requests `verbose_json` with segment timestamps. Original and normalized uploads are capped at **24 MiB**, conservatively below the documented 25 MB free-tier upload allowance. Audio is limited to 600 seconds, downsampled to mono/16kHz, and only one audio stream is accepted. There is no chunking in this MVP.

Reference: [Groq speech-to-text limitations and request examples](https://console.groq.com/docs/speech-to-text), [Groq transcription API](https://console.groq.com/docs/api-reference#audio-create-transcription). Provider service terms/quotas apply when the owner chooses to make a real request.

## FFmpeg and speech measurement

Both `ffmpeg.exe` and `ffprobe.exe` must be available. This workspace has portable binaries under ignored `tools/ffmpeg-dist/`; the backend helper locates them. Otherwise install system tools or set full paths in backend settings:

```dotenv
FFMPEG_BINARY=C:/path/to/ffmpeg.exe
FFPROBE_BINARY=C:/path/to/ffprobe.exe
```

Real metadata is measured even in fixture mode. WebRTC VAD is a lightweight alternative to Silero that avoids PyTorch/model downloads. Silence and measurement failure are uncertain and cannot be automatically billed. VAD is an estimate, particularly with music/noise; the artist must review actual evidence before approval.

## Payments

Use `PAYMENT_PROVIDER=mock` for local simulation or explicitly select `paypal_sandbox` for actual Sandbox APIs. `PAYPAL_ENVIRONMENT` accepts only `sandbox`; no production host is configurable. Missing PayPal credentials do not block mock startup. The legacy value `paypal` is invalid.

Backend variables: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_SANDBOX_MERCHANT_EMAIL`, `PAYPAL_SANDBOX_BUYER_EMAIL`, optional `PAYPAL_WEBHOOK_ID`. Keep `PAYPAL_ALLOW_DRAFTS=false` and `PAYPAL_ALLOW_SENDING=false` until separately approving the actual action/case. Existing `.env` was not overwritten. OAuth tokens stay in memory, expire early and refresh after authorization failure; errors never expose raw responses/tokens. There is no mock fallback.

Live OAuth and read-only invoice-list access succeeded. Actual draft/send/payment remain unverified pending owner approval and test-account emails. Webhook code is mock-tested, without a public endpoint. Exact commands and manual buyer payment: [PAYPAL_SANDBOX_TESTING.md](PAYPAL_SANDBOX_TESTING.md). APIMatic's installed SDK guidance lacks Invoicing v2; official PayPal documentation supplies those wire contracts.

## Verified live smoke check

On November 6, 2026, `scripts/verify_live_ai.py` called the actual Gemini and Groq adapters with local first-party sample inputs and `use_demo_fixture=False`. Gemini extracted 14 verified contract citations with no unknown fields or review flags. Groq returned a 990-character transcript with 12 timestamp segments. Gemini content assessment also completed and returned a validated findings structure. These are live provider results; the source samples being stored in `fixtures/` does not make the AI responses fixtures.

The script saves only safe aggregate metadata to ignored `backend/storage/live-ai-verification.json`. It never prints keys, raw provider errors, source contract text or the transcript. It does not approve agreements, allocate royalties, create invoices or call a payment provider. To intentionally rerun live calls:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe ..\scripts\verify_live_ai.py
```

`scripts/diagnose_gemini.py` provides fixed-category diagnostics without exposing raw exceptions; `--list-models` performs a read-only model listing. Neither script is part of the offline automated test suite. Live requests use the configured provider account and its quota.

## API route reference

OpenAPI: `http://127.0.0.1:8000/docs`. In the browser, use the same-origin proxy and demo cookie. Direct local API calls use `X-Demo-Persona: artist_demo` or `studio_demo`; this is selectable demo identity, not a security credential.

| Area | Endpoints |
| --- | --- |
| Status | `GET /health`, `GET /api/integrations` |
| Profiles | `GET /api/personas`, `/api/artists`, `/api/studios` |
| Agreements | `GET/POST /api/licenses`, `GET /api/licenses/{id}` |
| Contract | `POST/GET /api/licenses/{id}/contract`, `POST .../extract`, `PUT .../terms`, `POST .../approve` |
| Consent | `GET/POST /api/references` |
| Audio | `GET/POST /api/assets`, `GET /api/assets/{id}`, `GET .../audio`, `POST .../analyze` |
| Compliance | `POST /api/assets/{id}/evaluate`, `PATCH .../campaign` |
| Artist usage review | `POST /api/assets/{id}/authorization` |
| Overlap comparison/resolution | `GET/POST /api/assets/{id}/overlap` |
| Royalties | `GET /api/royalties`, `POST /api/royalties/{id}/decision` |
| Invoicing | `GET /api/royalties/{id}/invoice-preview`, `POST .../invoice`, `GET /api/invoices`, `GET /api/invoices/{id}`, `GET .../status`, `POST .../refresh` |
| Send / simulation | `POST /api/invoices/{id}/send` (separate Sandbox confirmation), `POST .../simulate-payment` (mock only) |
| PayPal | Artist-only `POST /api/paypal/diagnostic` (read-only), verified `POST /api/paypal/webhook` |
| Reporting | `GET /api/analytics`, `GET /api/audit` |
| Fixtures | `GET /api/demo/fixtures/contract`, `GET /api/demo/fixtures/audio` |

Extraction/analysis/evaluation default to `{ "use_demo_fixture": false }`. Analysis/evaluation also support `"reprocess": true` to deliberately refresh matching evidence; requesting a different provider automatically bypasses the old provider's cache. Changing transcription is blocked after financial allocation; use a new agreement/asset for a fresh live run. Fixture compliance cannot assess arbitrary/live transcripts. Fixture flags are explicit development/testing opt-ins, never failure recovery.

Artist usage review takes `{ "identity_confirmed": true, "use_authorized": true, "note": "Describe the evidence reviewed (10+ characters)." }`. It requires the assigned artist and analyzed audio. Review records are bound to actual evidence; checkbox confirmation is not model verification. Reevaluate after saving/revoking review. Contract scope/uncertainty can still hold charges. Positive eligible proposals require a separate artist decision. Legacy entries also require current eligibility before approval or invoice creation.

Overlap POST takes `related_asset_id`, `decision` (`SAME_USAGE`, `SEPARATE_USAGE`, `UNCERTAIN`), a 10+ character note and `expected_review_id` (null for a new pair, latest ID when changing it). Only the assigned artist can save; both analyses must use the same approved agreement/version, and links point toward earlier assets. The response includes comparison evidence, append-only history, canonical usage, unresolved/reconciliation flags and whether workflow checks were refreshed. Repeated identical decisions return the same record. Current content evidence is reused without claiming a fresh AI request; stale/failed provider evidence requires explicit evaluation. No historical invoice is automatically rewritten.

Asset responses include independent `processing_state`, `compliance_state`, `authorization_state`, `royalty_state`, `invoice_state`, derived `workflow_stage` and `next_action`. Royalty responses distinguish `eligible_for_charge` from `approval_current`; a changed eligible report requires explicit renewal of artist charge approval before invoicing. Invoice lists expose `eligible_for_send`. Identical metadata/review saves are no-ops; changed inputs safely make old evidence stale while retaining recorded attestations and overlap history.

Contract review takes full terms, expected version, a required note and optional acknowledgment of unknowns. Payment transitions require a unique `event_key`; replaying the same key for the same operation returns the existing state. Cross-operation reuse returns 409. Uploads use multipart; campaign metadata is a JSON string field. Missing ownership returns 404; wrong role 403; invalid content 422; missing configuration 503; safe provider failures 502; conflicting state/version 409. Full trace and browser testing: [AUDIO_COMPLIANCE_REVIEW.md](AUDIO_COMPLIANCE_REVIEW.md).

## Optional speaker worker

Do not install speaker packages into the core environment. The separate requirements file is `backend/optional-speaker/requirements.txt`. The CLI validates normalized 16kHz mono PCM16 inputs (3–120 seconds), requires audible signal and uses a single CPU thread. Use only consented single-speaker audio. Its model/threshold behavior remains **unverified**; the core feature remains disabled.

In a separately created environment, after explicitly choosing the model's download and memory costs:

```powershell
python backend/optional-speaker/verify.py reference.wav submitted.wav --allow-model-download
```

That command belongs in the optional environment, not the core `.venv`. Subsequent invocations default to offline cache. Production evaluation would need a pinned model revision and domain-specific threshold calibration. [SpeechBrain ECAPA model documentation](https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb) describes the underlying model. No similarity is proof of cloning, license authorization, or legal liability.
