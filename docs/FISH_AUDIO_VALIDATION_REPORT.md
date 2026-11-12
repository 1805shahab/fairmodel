# Fish response integrity audit — November 11, 2026

## Findings from the saved failures

Both original generation jobs are FAILED, provider `fish`, requested model `s2.1-pro-free`, with no linked asset. They have not been edited or replayed.

| Job | Available evidence | What remains unknown |
| --- | --- | --- |
| `3ebe33b3d9034869a4f2cf0a057ce687` | Old canonical-format rejection; generic local failure receipt | Original bytes, HTTP headers, container, sample rate, channels, encoding, completeness |
| `16c5625e14584cbdb236c9b18576d288` | HTTP 200; 2,097,500 received bytes; `RIFF_LENGTH_MISMATCH` before inner-format inspection | Exact RIFF/data sizes, content type, encoding and whether the audio was complete |

No original response file is retained. First-byte/container inspection is therefore impossible retrospectively. New synthetic test responses are **not reconstructions** of these recordings.

The first implementation wrongly required incoming Fish audio to already satisfy the application's canonical WAV validator, shared with Gemini. That rejects otherwise valid sample-rate/channel/encoding variants rather than converting them. The second implementation initially rejected an outer RIFF length mismatch before inspecting inner data. Streaming writers may emit unknown or stale lengths, but truncation can also cause mismatches. The exact cause in the lost historical response cannot be established. The previous follow-up already addressed several WAV variants; this audit adds transport evidence, MP3 support and stricter decoder checks.

## Verified request contract

The native API remains `POST https://api.fish.audio/v1/tts`, with backend Bearer authentication and `Content-Type: application/msgpack`. The **exact** `model: s2.1-pro-free` header is mandatory. Missing/unrecognized model headers can select the paid default, so runtime/configuration guards reject other models.

The body still explicitly requests `format: wav`, `sample_rate: 24000`, `latency: normal`, generation text and inline reference audio/transcript. No reusable profile is created. No undocumented `streaming` flag is added. HTTPX `Client.stream` consumes the binary HTTP response incrementally; it does not select Fish's separate SSE or WebSocket API. All delivered chunks must be collected and the HTTP stream must end normally before audio can be accepted.

Fish documents WAV/PCM at several rates, MP3 and Opus. FairModel accepts supported framed WAV and MPEG Layer III MP3; raw PCM, Opus, arbitrary containers and error documents are rejected explicitly. It never guesses raw PCM parameters from the requested format.

Sources: [native TTS schema](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech), [format/MessagePack guide](https://docs.fish.audio/features/text-to-speech), [published OpenAPI](https://docs.fish.audio/api-reference/openapi.json). The [open-source Fish stream writer](https://github.com/fishaudio/fish-speech/blob/main/fish_speech/inference_engine/utils.py) shows unknown-length header conventions; it does not establish which header the hosted API returned for either failed job.

## Output handling

- Inspect actual magic bytes in memory and retain fixed container labels only. No audio prefix, reference content, arbitrary provider body, tag text or secret is logged.
- Preserve HTTP status, allowlisted content type/encoding, declared length, decoded byte/chunk count, transfer mode and completion state. Request identity HTTP encoding; compare Content-Length to received bytes when applicable. Network/protocol interruption fails without replay. HTTP success alone is not audio success.
- WAV: inspect chunk bounds/padding, format, rate, channels, bit depth, alignment, finite float samples, duration and size. Finite inner data must be complete. A stale outer index may be corrected only after full inner validation. Recognized paired unknown markers and the narrow legacy empty-WAV streaming layout use observed aligned samples; no padding or expansion of a truncated finite declaration.
- MP3: bound ID3 metadata, walk complete MPEG Layer III frames, check rate/channel consistency, and verify Xing/Info/VBRI counts when present. Detect mid-frame loss and indexed whole-frame loss before decoding. Header/frame validation is followed by actual strict FFmpeg decoding. Frame parsing follows the format conventions used by [FFmpeg's MP3 demuxer](https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/mp3dec.c).
- Normalize noncanonical input through existing local FFmpeg with `-xerror -err_detect explode`, a fixed WAV/MP3 demuxer and local-only protocol whitelist. Resample/downmix to WAV / 24000 Hz / mono / signed PCM16. Validate the final container again and compare source/output durations, allowing bounded MP3 encoder priming/padding. Never rename compressed bytes to WAV or accept a header-only repair as the converted result.
- Bound source/output byte size and duration. Clean temporary input/output files on success and failure. Only the validated output reaches the unchanged generation-route persistence checks; successful assets start at UPLOADED, with identity and all normal downstream approvals unresolved.

Source/output hashes, numeric format/frame/duration facts, normalized output facts and response metadata are retained on new success receipts. New failures retain safe categories and available response facts, without a success timestamp or asset.

Limit: complete HTTP framing plus valid audio frames cannot prove the provider intended no additional speech. Unknown-length WAVs and unindexed MP3s have no independent final-duration assertion; receipts explicitly retain this uncertainty. Indexed/declaration mismatches, finite truncation, decoder failures and interrupted transfers remain rejected. The artist must listen to and review every generated result.

## Error categories

Examples include `EMPTY_AUDIO`, `NON_WAV_RESPONSE` (unsupported framed format), `PROVIDER_ERROR_PAYLOAD`, `PROVIDER_NON_AUDIO_RESPONSE`, `HTTP_LENGTH_MISMATCH`, `TRUNCATED_PROVIDER_RESPONSE`, `INCOMPLETE_PROVIDER_RESPONSE`, `TRUNCATED_CHUNK`, `INCOMPLETE_AUDIO_FRAME`, `TRUNCATED_MP3_FRAME`, `MP3_FRAME_COUNT_MISMATCH`, `LOCAL_NORMALIZATION_FAILED` and `NORMALIZATION_DURATION_MISMATCH`. HTTP/provider failures retain their existing authentication, permission and rate-limit categories. Neither error text nor diagnostics includes raw decoder/provider messages.

## Scope and verification

Changed runtime files: `backend/app/fish_audio.py`, `fish_generation.py`, new `fish_mp3.py`, and the Fish-only integration-status version in `main.py` (`wav-mp3-inspect-normalize-v4`). New mocked integration tests: `backend/tests/test_fish_response.py`. Existing WAV/Fish tests are retained. No dependency, schema, `.env`, Gemini, Groq, compliance, royalty or PayPal logic change is required.

Verification: **345 backend tests pass** (109.12 seconds, one existing Starlette warning); backend Ruff, frontend TypeScript/ESLint and the 21-page production Webpack build pass. Twenty-one new tests cover MP3 decoding/frame/index loss, HTTP chunk assembly/length/type/errors, interrupted transfers, failed conversion/final validation and persistent no-asset/no-finance/no-replay failure behavior. Existing WAV variants and other provider/workflow tests pass. An initial new test failed because it corrupted an assumed metadata offset; it now locates the actual MPEG header and the full rerun passes. No frontend source change or browser-suite rerun. An optional broader root-level Ruff scan reported eight existing findings in unrelated Gemini diagnostic scripts; those files remain unchanged.

Read-only checks confirm the running backend advertises v4, 23 protected backend source hashes are unchanged, both original failed job rows match exactly, SQLite integrity is OK and foreign-key checks return zero errors. Tests use only synthetic audio, real local FFmpeg and mocked HTTP, with isolated database/storage and blank provider keys. No actual Fish generation has been successfully verified by this audit. There has been no live sample transfer, profile operation, paid-model request, automatic retry or financial operation.

## Next owner-run manual test

1. Restart the backend using `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1`. Confirm Integration status reports Fish pipeline `wav-mp3-inspect-normalize-v4`. Do not change payment write flags for this audio test.
2. Open the existing application. As Studio, choose **Generate advertisement → Fish Audio** and the artist's valid Fish-specific grant. Review reference/transcript, original script and permitted campaign metadata. Do not reuse an expired/revoked grant or a Gemini-only grant.
3. Choose **Start a new generation request** for a deliberately new request; failed saved jobs are never automatically replayed. Review the third-party processing confirmation and click **Generate with licensed artist voice** once. This is the owner's explicit sample transfer; no agent-run request is scheduled.
4. On success, play the recording. Inspect its saved generation receipt: requested free model, HTTP 200/completed body, source container/format, normalization and output 24000 Hz / mono / 16-bit facts. The asset must be UPLOADED; it must not claim independently verified identity or completed compliance.
5. Run normal audio analysis, compliance and artist authorization before royalties/invoices. On failure, inspect the safe category and response facts. Do not repeat blindly or switch models/providers. Both historical failed jobs must remain unchanged.

Run local regression tests from the project root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
.\backend\.venv\Scripts\python.exe -m ruff check backend
```
