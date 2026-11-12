# Artist sample to studio advertisement

FairModel now supports Gemini TTS replication from an explicitly consented artist reference. This is separate from optional speaker verification, final campaign authorization and royalty approval. It does not replace the existing audio-upload workflow. PayPal behavior is unchanged.

## Configure locally

Keep your existing server-only `GEMINI_API_KEY`. Add these settings yourself to `backend/.env`, then restart the backend:

```dotenv
ENABLE_VOICE_GENERATION=true
GEMINI_TTS_MODEL=gemini-3.8-flash-lite-tts
GEMINI_VOICE_REPLICATION_MODEL=gemini-3.8-flash-tts
```

Generation defaults off. No reference or consent audio is sent during startup, migrations, diagnostics or normal tests. Google requires a paid-tier Gemini project for replication; the flag/key presence alone does not verify this access. The installed `google-genai` 2.34.0 supports Voices/Interactions; the readable requirement now requires at least that version. No new package/model download was needed.

Read-only live model metadata returned `models/gemini-3.8-flash-lite-tts` successfully on November 11. The owner's subsequent live replication attempt failed before synthesis; **successful live replication/generation remains unverified**. Model availability does not prove operation support, successful consent verification or sufficient quota.

### Replication model rejected

Saved job `dffb4988852949daab062876521d8a11` records replication-stage HTTP 400 / `INVALID_ARGUMENT` / `MODEL_ACCESS` with Flash-Lite; no asset was created. The safe category was recognized from Google's message wording, not a structured capability flag. Google's guide lists both TTS models as supporting replication, but its replication examples use `gemini-3.8-flash-tts`. The app now has an independent `GEMINI_VOICE_REPLICATION_MODEL` setting, defaulting to Flash, for `voices.create`. `GEMINI_TTS_MODEL` continues selecting the later speech-synthesis model. Both choices appear before the paid-operation confirmation and in new job receipts. This is an explicit configured request path, never an automatic model retry after failure. Flash costs/access can differ; successful operation still needs manual verification.

Restart the backend after updating code/settings, refresh the generation page, and check the two displayed model names. If needed, explicitly set the replication variable above yourself; the app does not overwrite `.env`. Keep the existing grant/recordings. A saved failed request remains failed; **Start a new generation request** then **Generate with licensed artist voice** deliberately starts a new potentially paid attempt. The owner declined an agent-run retry and will test manually. Do not re-record consent, change billing or claim the new model works until an actual provider response establishes the next result.

Official sources: [Gemini voice replication](https://aistudio.google.com/docs/voice-replication), [speech generation](https://aistudio.google.com/docs/speech-generation). Current API contracts and the installed SDK's actual HTTP serialization were checked rather than assuming older prebuilt-only TTS behavior.

## Artist setup

1. Open **Reference voice** as Artist. Upload a clean 10–30 second recording from the adult speaker. Existing storage/comparison consent does not authorize replication.
2. Create a voice license, upload its PDF, run Gemini extraction, review actual source clauses and approve the terms. Preserve any unknowns/review requirements honestly.
3. The same speaker records this separate consent statement clearly, in English, without background music:

   > I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model.

4. Under **Authorize your licensed voice**, select the reference and active agreement, upload that 2–30 second consent recording, confirm adult-speaker rights and transfer to Google, and enter a meaningful permission note. The application records a grant for the assigned studio and exact approved version. This action stores local consent; the provider verifies it when generation is requested.
5. Inspect saved permissions or revoke future generation. Revocation does not delete existing assets/charges/invoices. A revoked grant is not silently reactivated; use a new reference/grant for new permission.

Both clips must be authentic human recordings from the same consenting adult. Local silence/stock-TTS fixtures used by automated tests are **not eligible inputs for actual replication**. Google can reject consent, unsupported audio or insufficient access; FairModel displays a safe error, never substitutes a prebuilt voice or fixture.

## If consent upload reports a duration error

The grant form checks the selected **reference sample first**, then the uploaded **consent recording**. Reference samples must be 10–30 seconds total file duration; consent clips are accepted by FairModel at 2–30 seconds. Neither needs to be exactly 30 seconds. Read only the consent statement naturally; do not add silence. A 45.401-second reference fails even when the separate consent is 30 seconds. Errors now identify the recording and measured duration, and the picker marks out-of-range references while preserving them for their original comparison use. Upload/select a suitable new reference instead of modifying existing private files. This 422 is local validation, not a successful or failed Google replication response.

## Studio creation and the existing pipeline

1. Open **Generate advertisement** (`/dashboard/generate`) through Workspace tools or the upload page.
2. Select a current artist grant. Write an original script (10–4,000 characters), supply campaign name/region/medium/language/category/date, and explicitly confirm provider usage and possible API costs.
3. Deterministic contract scope must be resolved/permitted before generation. Financial examples/preview are not authoritative charges. Supported speech-only/proportional/HALF_UP financial clauses are checked against the deterministic engine instead of being sent to human interpretation. Actual speech measurement is explicitly deferred until audio analysis. Conflicting/unknown qualifications or missing source citations still require review rather than broadening the license. See [COMPLIANCE_RULES.md](COMPLIANCE_RULES.md).
4. FairModel normalizes both source clips to 24kHz mono PCM16. Gemini Voices receives both clips with `type=replicated, store=false`; the returned ephemeral key is used only in memory for a single Interactions TTS call. No voice key or credential is persisted or returned to the frontend. The application does not create a persistent Google voice profile.
5. A complete valid WAV is checked before creating a submission. The asset retains the exact license version and campaign, a generation audit receipt and genuine output hash. Its stage is **Uploaded**. Script text is not treated as a transcript or speech measurement.
6. On the resulting recording page, run live Groq analysis (FFprobe/WebRTC VAD measure actual durations), then live Gemini compliance. The artist must separately review the final voice/campaign, resolve overlap/other holds and authorize usage. Permitted excess speech uses the existing Decimal royalty engine. Charge approval and each Sandbox invoice action remain separate.

Text length does not guarantee any spoken duration or invoice amount. A different or unverified voice never authorizes an automatic charge. Provider consent acceptance does not constitute independent FairModel identity verification or a legal determination.

## Persistence, retries and privacy

### Provider errors and diagnosis

An HTTP 400 alone does not prove an API schema defect; it can also represent consent, model/access or audio rejection. Earlier generic errors did not retain the stage or provider reason, so historical failures cannot be retroactively diagnosed from those messages alone. New failures distinguish `voice_replication` from `speech_synthesis`, retain safe allowlisted categories/status/request-field names in the failed job receipt, and expose no raw provider messages or sensitive response bodies. A category inferred from recognized message wording is identified as such; unknown reasons stay `INVALID_REQUEST_UNSPECIFIED`. A synthesis-stage failure records prior replication acceptance separately and never claims finished speech or independent identity verification.

Inspect the saved job error/history before starting another operation. Clicking Generate again with the same request key retrieves the existing failed job. **Start a new generation request** deliberately requests another provider operation and can consume paid Gemini quota; use it after addressing the reported issue. No automatic retry, recording substitution or prebuilt-voice fallback occurs. Read-only model/catalog access and local WAV validation do not prove successful replication. The original private reference and consent files remain unchanged.

### Stored grants and generation intents

Schema 6 adds only `voice_generation_grants` and `speech_generations`. The consistent pre-change backup is `backend/backups/fairmodel-before-gemini-tts-20261111T064818687119Z.db`; migration also backs up older databases. All 20 original tables compared unchanged after migration; integrity and foreign keys pass. Existing uploads, contract versions, reviews and finance remain intact.

Grants are ownership/version bound; the studio cannot create/revoke artist grants or retrieve private reference/consent audio. The artist can play their own reference through an ownership-checked endpoint. Consent clips remain private. Demo roles still are local demonstration access, not production authentication.

Generation saves a unique studio/request-key intent before HTTP and releases the SQLite writer lock. Repeated identical requests retrieve that job; conflicting inputs reject reused keys. Revocation/version/file changes are rechecked after the provider returns. A failed output creates no asset/allocation/invoice. Identical output bytes reuse an existing asset only for the same campaign; conflicting campaign metadata requires review.

The installed SDK's generated endpoint retry mapping attempted an extra POST despite its minimum retry setting; a public HTTPX request hook now blocks replay before transmission. Regression tests verify exactly one transmitted operation on HTTP 403/429/503 and network failure. Interactions automatic continuation is disabled and incomplete output is rejected. Provider errors expose only safe status/category, not response bodies, transcripts or credentials. No fixture fallback exists for generation.

A process crash may leave a RUNNING job whose remote result is unknown. Retrying its key does not start another operation. Inspect history; deliberately starting a new request is a separate potential provider charge. No durable background worker or automatic provider-result recovery is claimed. A completed remote operation can consume provider quota even if output later fails validation or the grant is revoked; FairModel issues no automatic royalty for that failure.

Final verification: **209 backend tests**, Ruff, TypeScript/ESLint, the 21-page Webpack production build and **26 Edge tests (3.4m)** pass. Eight responsive checks have no overflow/browser errors; local screenshots under `.tmp/tts-ui/` were inspected. A real FFmpeg conversion from 44.1kHz stereo to 24kHz mono PCM16 passed. Owned QA servers were stopped, user servers retained and source remains uncommitted/unpushed.

Normal backend tests mock Gemini HTTP/processing seams. Browser tests use an isolated database with explicit synthetic test recordings/grants and an intercepted provider response; they never send those clips to Google. Existing real local PDF/audio/VAD and fixture compliance/payment tests remain separate. Initial browser failures were caused by the test's independent API cookie not matching the page cookie; corrected tests set the page-context role. See PLAN.md and TESTING.md for verification details. The existing Starlette deprecation warning is non-blocking; the prior Taste checker ERROR was not rerun or claimed as passing.
