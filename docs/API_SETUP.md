# API and local tool setup

Copy `backend/.env.example` to `backend/.env` only if it does not exist. Edit secrets locally; do not paste them into chat, commits, screenshots, shell arguments or frontend environment variables. Launch the backend from `backend/` so relative DB/storage/config paths resolve consistently. The helper scripts do this automatically.

## Google Gemini

Set `GEMINI_API_KEY` and optionally `GEMINI_MODEL` (default `gemini-3.1-flash-lite`). The maintained `google-genai` SDK sends schema-constrained requests for Terms and ContentFindings. Requests have a timeout and no tools. Use a model available to your account; model availability and quotas may change. Leave fixture checkboxes unchecked for real calls.

The original `gemini-2.5-flash-lite` setting returned 404 during live verification on November 6, 2026. Google's [supported-model documentation](https://firebase.google.com/docs/ai-logic/models?api=dev) documents that model's retirement and the 3.1 Flash-Lite replacement. Real extraction and content assessment succeeded with `gemini-3.1-flash-lite`.

The settings screen reports key presence without revealing it or asserting provider success. A real successful result records `gemini:<model>`. A 503 means missing credentials; 502 means provider or structured validation failure. No demo result replaces a failed request.

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

Keep `PAYMENT_PROVIDER=mock` and `DEMO_MODE=true`. PayPal credentials are unnecessary and intentionally unused. Setting `paypal` refuses startup with a clear deferred-integration error. Do not attempt authentication until the owner restores account access and explicitly authorizes implementation.

Future required work: OAuth, Invoicing v2 draft/send/status, provider idempotency, verified webhook signatures, event deduplication, reconciliation, sandbox end-to-end test. Mock success is not evidence of PayPal API integration.

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
| Royalties | `GET /api/royalties`, `POST /api/royalties/{id}/decision` |
| Invoicing | `POST /api/royalties/{id}/invoice`, `GET /api/invoices`, `GET /api/invoices/{id}`, `GET .../status` |
| Simulation | `POST /api/invoices/{id}/send`, `POST .../simulate-payment` |
| Reporting | `GET /api/analytics`, `GET /api/audit` |
| Fixtures | `GET /api/demo/fixtures/contract`, `GET /api/demo/fixtures/audio` |

Extraction/analysis/evaluation take `{ "use_demo_fixture": false }`. Contract review takes full terms, expected version, a required note and optional acknowledgment of unknowns. Payment transitions require a unique `event_key`; replaying the same key for the same operation returns the existing state. Cross-operation reuse returns 409. Uploads use multipart; campaign metadata is a JSON string field. Missing ownership returns 404; wrong role 403; invalid content 422; missing configuration 503; safe provider failures 502; conflicting state/version 409.

## Optional speaker worker

Do not install speaker packages into the core environment. The separate requirements file is `backend/optional-speaker/requirements.txt`. The CLI validates normalized 16kHz mono PCM16 inputs (3–120 seconds), requires audible signal and uses a single CPU thread. Use only consented single-speaker audio. Its model/threshold behavior remains **unverified**; the core feature remains disabled.

In a separately created environment, after explicitly choosing the model's download and memory costs:

```powershell
python backend/optional-speaker/verify.py reference.wav submitted.wav --allow-model-download
```

That command belongs in the optional environment, not the core `.venv`. Subsequent invocations default to offline cache. Production evaluation would need a pinned model revision and domain-specific threshold calibration. [SpeechBrain ECAPA model documentation](https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb) describes the underlying model. No similarity is proof of cloning, license authorization, or legal liability.
