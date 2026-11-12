# Fish Audio: free inline voice generation

Reviewed against official documentation on November 11, 2026. Automated provider responses are mocked. The owner's later live request reached local output validation but failed; successful live generation remains unverified. No agent-run live Fish request or retry was performed.

Latest pipeline: `mp3-complete-probe-normalize-v5` explicitly requests MP3/44100/128 from the free model, collects the complete HTTP body, checks MPEG framing and FFprobe metadata, then strictly converts to validated 24kHz mono PCM16 WAV. The latest saved failure's finite data-size mismatch remains rejected. See [the completed-MP3 investigation and next manual test](FISH_MP3_OUTPUT.md). No new live request was made.

Previous response audit: `wav-mp3-inspect-normalize-v4` added HTTP completion/length/type diagnostics and bounded MP3 frame validation with strict local FFmpeg conversion. WAV variants remain supported; final output must pass canonical validation before asset creation. See [the validation report](FISH_AUDIO_VALIDATION_REPORT.md) for both earlier historical failures and integrity limits. Their lost response bytes cannot establish an exact original format or prove a live repair succeeded.

## Free API findings

Fish lists `s2.1-pro-free` at $0 per million input UTF-8 bytes under fair-use limits. Its quickstart says new accounts can use it without API credit. The model overview describes the same quality as S2.1-Pro, with no TTFA or DPA guarantees. General starter concurrency is five; free-model capacity/account access still depends on Fish. This documents availability, not a successful test of your account.

Sources: [pricing](https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits), [model overview](https://docs.fish.audio/developer-guide/models-pricing/models-overview), [account quickstart](https://docs.fish.audio/developer-guide/getting-started/quickstart).

TTS accepts inline `references` for zero-shot cloning with audio and its exact transcript. The free model is explicitly supported. Reusable profiles instead use `POST /model` and `reference_id`. The create-model guide does not establish free-account profile-creation entitlements or quotas. FairModel implements **inline references only**: no profile training/publication, no `/model` calls, no claim that unlimited reusable profiles are free.

Sources: [cloning](https://docs.fish.audio/features/voice-cloning), [TTS schema](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech), [create-model schema](https://docs.fish.audio/api-reference/endpoint/model/create-model).

## Retention and licensing

No zero-retention guarantee, training exclusion or API-specific deletion deadline was established. Fish's privacy policy retains content as needed for service/business purposes, with exceptions for obligations/disputes. Inline requests avoid creating a reusable profile through FairModel; they do **not** prove immediate deletion. Free access has no DPA guarantee. Artists must acknowledge these points before granting Fish processing.

Fish terms require rights to submitted material, prohibit misuse and misleading claims that generated content is entirely human-made, and include broad submission-processing licenses. Public submissions carry additional sharing rights. Free pricing does not replace artist rights, the approved contract, provider terms or applicable law. Production/commercial deployment requires separate terms/data review; no blanket commercial permission or legal clearance is claimed.

Sources: [privacy/retention](https://fish.audio/privacy/), [terms/content restrictions](https://fish.audio/terms/).

## Configure locally

MessagePack provides the documented binary wire format. No Fish SDK or model download is needed. Install backend dependencies using the existing requirements/lock instructions. Add these yourself to the existing `backend/.env`; never replace the file or share the key:

```dotenv
FISH_API_KEY=
FISH_TTS_MODEL=s2.1-pro-free
ENABLE_VOICE_GENERATION=true
ENABLE_FISH_GENERATION=true
```

Restart with `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1`. Fish defaults off. Gemini remains available with independent credentials/settings. Startup and tests never call Fish.

## Artist → studio → existing workflow

1. Artist uploads an owned private reference and approves the licensing agreement. This initial Fish workflow accepts 10–30 seconds of clean single-speaker audio; longer existing files remain stored.
2. In **Reference voice → Authorize your licensed voice**, select **Fish Audio**, the reference and approved agreement. Enter its exact transcript, acknowledge Fish retention/terms, confirm adult-speaker ownership and explicitly authorize third-party processing and the assigned studio. Google grants never imply Fish permission. Fish does not receive the separate Google consent clip.
3. Studio opens **Generate advertisement**, explicitly selects **Fish Audio** and that Fish grant, enters an original permitted script/campaign, and confirms this particular request. No automatic provider fallback exists.
4. A valid successful WAV enters **Uploaded**, with provider/model/hash/timestamp provenance. Run Groq/VAD analysis, Gemini compliance and final artist identity/use attestation; resolve overlaps as before. Only permitted usage can proceed through deterministic royalties, charge approval and invoices. PayPal behavior is unchanged.

Grants are artist/studio/version-bound, revocable and idempotent. Transcript changes are rejected to preserve consent history; use a new reference/grant for corrected permission. Both providers can have distinct grants for the same reference/version. Unique studio/request keys prevent automatic replay of failed/interrupted jobs. Neither provider generation nor manual consent establishes independent speaker identity.

## HTTP and provenance

One `POST https://api.fish.audio/v1/tts`, backend-only Bearer auth, `Content-Type: application/msgpack`, **exact `model: s2.1-pro-free` header**. Body includes `text`, `references: [{audio: <WAV bytes>, text: <reference transcript>}]`, `format: mp3`, `sample_rate: 44100`, `mp3_bitrate: 128`, `latency: normal`. Binary references are described in the [direct API guide](https://docs.fish.audio/features/text-to-speech). Local FFmpeg normalizes the reference. The complete returned body is inspected by actual container, frame-checked and (for MP3) FFprobe-validated, then normalized to bounded 24kHz mono PCM16. HTTP transport may be chunked; processing waits for normal completion. Supported valid WAV input remains accepted without weakening finite-truncation checks. Redirects, retries, paid model names and profile endpoints are blocked.

### Returned-WAV validation repair

The owner's failed job `3ebe33b3d9034869a4f2cf0a057ce687` hit the earlier strict output-format check. Raw response bytes were discarded; that historical response's exact sample rate/encoding cannot now be established. The earlier implementation mistakenly required Fish's incoming WAV to already match Gemini's canonical format. [Fish documents multiple output rates](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech), and its [open-source stream-header implementation](https://github.com/fishaudio/fish-speech/blob/main/fish_speech/inference_engine/utils.py) uses unknown RIFF/data lengths. The latter is evidence of a possible format variant, not proof of what this hosted request returned.

The Fish adapter validates inner chunks, format, frame alignment, finite float samples and observed duration before decoding. It handles supported integer/float and extensible WAV variants, preserves received format metadata, and uses real local FFmpeg to resample/downmix genuine samples. Modern unknown-length streams use paired documented `0xFFFFFFFF` RIFF/data markers. A narrow legacy empty 44-byte mono PCM16 WAV header (RIFF size 36/data size 0 followed by observed aligned samples) is also recognized, with explicit streaming uncertainty. Finite sizes are derived from actual received bytes before normalization; no silence or invented samples are appended. Stream headers cannot establish the provider's intended final duration. Final artist review remains mandatory.

Follow-up job `16c5625e14584cbdb236c9b18576d288` recorded HTTP 200 and 2,097,500 bytes but failed the prior outer-RIFF-size check before recording its numeric declared size or format. Its exact header is not recoverable. Outer size is now checked after inner framing: if every finite inner chunk and sample is complete, only the stale outer size is corrected. This never expands a finite data declaration or treats metadata chunks as audio. Finite data truncation, unsupported zero-header layouts, inconsistent modern stream markers and incomplete sample frames still fail. New failure diagnostics retain declared/actual sizes and format facts without copying sample bytes. The synthetic same-byte-count regression is not a reconstruction or live test of this historical response.

Non-WAV/JSON, malformed/truncated finite chunks, incomplete frames, excessive duration/size and decoder failures remain errors. New failure receipts retain safe numeric format facts and an explicit local-audio category without copying provider bodies. HTTP 200 alone is not audio success. Success receipts retain both provider-response and normalized-output hashes, source format/duration, normalization status and canonical stored format. Existing failed jobs stay failed; no automatic replay, salvage claim or provider switch. A deliberately new owner-run request is needed to test the repaired path live.

Repair checks: **311 backend tests**, Ruff, frontend TypeScript/ESLint and the 21-page production build pass. Twenty-nine new WAV cases exercise actual FFmpeg, normalized asset persistence and rejection/cleanup/privacy without real provider calls. Runtime `voice_generation.fish.output_audio_pipeline` reports `wav-inspect-normalize-v2`. The five prior Edge generation checks remain historical; this backend-only repair did not rerun them. No schema or original failed-job change and no live retry.

The RIFF follow-up is `wav-inspect-normalize-v3`: **324 backend tests**, Ruff, frontend TypeScript/ESLint and the production build pass. Thirteen additional regressions cover stale outer sizes, the narrow legacy stream, actual sample preservation, metadata exclusion and truncated finite-data rejection. A synthetic mocked response matches the owner's observed byte count but is not a reconstruction of the lost output. Both saved failures remain unchanged. No agent-run live request was made; use a deliberately new owner-authorized request for the next test.

Fish documents that missing/unrecognized model headers default to paid S2.1-Pro; configuration and runtime guards therefore require the exact free identifier. FairModel cannot independently attest which model Fish actually served or the provider's final bill from binary output alone; receipts explicitly distinguish requested model from an independently verified served model.

Success receipts persist provider, requested model, completion time, consent-policy version and output/reference hashes only after valid audio. Failure receipts have safe status/categories and no success timestamp. No provider response bodies, credentials, reference audio or transcripts are logged. Script/reference transcript remain private database inputs.

## Optional manually authorized live smoke test

Do not run this in automated tests. Installing/configuring does not authorize a live transfer. Review the actual Fish grant, recordings, script, campaign, account free access and terms first. The owner may deliberately submit once through the browser, or prepare ignored `.tmp/fish-script.txt` and `.tmp/fish-campaign.json`. Campaign JSON uses normal name/medium/region/language/category/intended_use_date fields.

```powershell
# Dry run: no HTTP or audio transfer. Replace the grant ID with your Fish grant.
.\backend\.venv\Scripts\python.exe .\scripts\fish_live_smoke.py --grant-id YOUR_FISH_GRANT_ID --script-file .tmp/fish-script.txt --campaign-file .tmp/fish-campaign.json --request-key fish_manual_001
# Only after authorizing this exact sample/script transfer:
.\backend\.venv\Scripts\python.exe .\scripts\fish_live_smoke.py --grant-id YOUR_FISH_GRANT_ID --script-file .tmp/fish-script.txt --campaign-file .tmp/fish-campaign.json --request-key fish_manual_001 --confirm-private-audio-transfer --confirm-free-tier-terms --execute
```

The helper makes one local FairModel request as studio_demo, reads no keys and performs no PayPal action. Repeat the same key to retrieve its saved operation; a new key is a deliberate new operation. After success, inspect provenance, listen to actual output, run analysis/review and verify persistence after restart. Account errors/limits are failures, never fixtures or reasons to request a paid model.

## Migration and verification

Schema 7 adds provider/reference-transcript metadata, expands grant uniqueness by provider and preserves legacy grants/jobs as Gemini. Backup: `backend/backups/fairmodel-before-fish-20261111T123548522194Z.db`. All original fields/rows across 22 tables and private-file hashes matched the pre-change inventory; integrity/foreign keys passed. The grant-table rebuild is transactional with validation; normal older-database upgrades create consistent backups. No contracts, approvals, recordings or financial history were rewritten.

Verified: **282 backend tests**, Ruff, frontend TypeScript/ESLint, 21-page production build and **five Edge generation checks** pass. Thirty-three focused Fish cases cover safe HTTP/serialization, eligibility/idempotency, migration and manual-test dry-run. Browser provider responses are explicitly mocked and all clips are synthetic QA fixtures, never uploaded to Fish. Original DB has zero Fish jobs. Actual Fish account access, generated quality, provider retention behavior and billing remain unverified. See PLAN for detailed results and historical checks.
