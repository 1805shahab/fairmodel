# Fish completed MP3 output — November 11, 2026

## Saved failure: exact evidence

Job `39e683f43f624ae0ac0f3485d590fd31` remains FAILED with no asset, no replay and no financial record created by the failed request. Its saved receipt records:

| Fact | Saved value |
| --- | --- |
| Requested model | `s2.1-pro-free` |
| HTTP | 200, `audio/wav`, identity encoding, chunked transfer |
| HTTP body completion | true; 32 delivered chunks; no Content-Length |
| Received body bytes | 2,039,544 |
| RIFF declared size | 4,294,967,076 (`0xFFFFFF24`) |
| Actual bytes after RIFF prefix | 2,039,536 |
| Data declared size | 4,294,967,040 (`0xFFFFFF00`) |
| Data bytes available | 2,039,500 |
| Parsed format | PCM tag 1, 24,000 Hz, mono, 16 bits |

The failing chunk is **data**: its finite declared extent exceeds the received body. The RIFF declaration is consistent with that enormous data declaration (`data + 36`), rather than with the actual body. Normal HTTP chunked termination establishes transport completion; it does not prove Fish produced all intended speech.

Near-4GB values suggest a possible writer placeholder. They are neither the documented paired `0xFFFFFFFF` unknown-length markers nor the recognized legacy zero-data layout. No original response file was retained, so a provider placeholder versus incomplete provider output cannot be established retrospectively. Correct sample rate/channels/bit depth do not establish complete sample data. The repair keeps this finite mismatch rejected; it never expands the accepted placeholder vocabulary or invents missing samples.

Synthetic tests reproduce these numeric/header facts only, not the lost recording. The historical receipt is preserved, not retroactively supplemented with inferred measurements or new provenance.

## Official client investigation

Fish's [native API schema](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech) documents MP3 output at 32/44.1 kHz and 64/128/192 kbps. It also documents MessagePack inline references and exact `model: s2.1-pro-free`. No paid/default model is requested.

The official [Python TTS implementation](https://github.com/fishaudio/fish-audio-python/blob/main/src/fishaudio/resources/tts.py) implements `convert()` as `stream(...).collect()` against `/v1/tts`. Its [AudioStream collector](https://github.com/fishaudio/fish-audio-python/blob/main/src/fishaudio/core/iterators.py) concatenates bytes; it does not finalize or rewrite WAV headers. Thus “complete audio” does not require an undocumented `streaming: false` request flag. The [TTS guide](https://docs.fish.audio/features/text-to-speech) describes complete-byte and incremental consumption separately.

The [Fish Speech open-source writer](https://github.com/fishaudio/fish-speech/blob/main/fish_speech/inference_engine/utils.py) emits paired all-ones lengths for unknown-length WAV. That source does not prove how this hosted response's different finite values were produced.

## Changes

New generation requests use the same single fixed endpoint, backend authentication and inline consented reference, but request:

```text
POST https://api.fish.audio/v1/tts
model: s2.1-pro-free
Content-Type: application/msgpack
Accept: audio/mpeg
Accept-Encoding: identity

format: mp3
sample_rate: 44100
mp3_bitrate: 128
latency: normal
```

All response bytes must be collected before decoding or persistence. Bounded HTTPX streaming consumption remains to enforce the size limit and detect interruptions; the provider may still use HTTP chunked transfer. This is complete-file consumption, not SSE/WebSocket generation or playback of partially received audio. There are no automatic retries, redirects, model/provider switches or fixture fallback.

For an actual MP3 response:

1. Validate bounded metadata, complete MPEG frames and available frame/byte indexes. Incomplete MP3s fail before decoding.
2. Write a private temporary `.mp3` file and run local FFprobe with a fixed MP3 demuxer and local-only protocols. Require one MP3 audio stream, finite bounded duration, and rate/channels matching inspected headers. Retain only safe codec/rate/channels/duration facts; no tags or full probe output.
3. Decode through existing FFmpeg using strict error handling; downmix/resample to WAV / 24kHz / mono / signed PCM16. Compare durations with bounded encoder priming/padding allowance.
4. Validate the final WAV container, encoding and frame payload again. Only then can the unchanged route perform its ownership/version checks and create an UPLOADED asset. All subsequent analysis, identity/use authorization, compliance and financial reviews remain separate.
5. Remove temporary input/output files on success or failure. Retain requested output settings, actual source container/probe facts, normalized output facts and hashes in successful provenance.

Existing supported WAV normalization remains available for genuine validated WAV input, including unexpected provider output; the actual container is always recorded. Finite truncated chunks remain rejected. New failure diagnostics identify a fixed-label failed chunk type and numeric offset/declared/available sizes; no arbitrary chunk IDs, audio prefixes or raw bodies are persisted.

Runtime marker: `voice_generation.fish.output_audio_pipeline = mp3-complete-probe-normalize-v5`. Changed runtime files are limited to `fish_generation.py`, `fish_audio.py` and that Fish status marker in `main.py`. No new dependency or schema change. Licensing, royalties, Gemini, Groq and PayPal sources are protected against changes during this milestone.

## Verification and limits

**354 backend tests pass** (98.71 seconds; one existing Starlette warning), plus backend Ruff and frontend TypeScript/ESLint. Nine new cases cover the saved finite near-uint32 header facts, correct/missing chunk padding, FFprobe failures/mismatches, conversion failure/no asset and the complete mocked MP3-to-UPLOADED flow. Existing valid WAV resampling, malformed/finite-truncated/unknown-length WAVs, incomplete MP3, protocol interruption and final-validation tests pass. Tests use synthetic recordings, actual local FFprobe/FFmpeg, mocked Fish HTTP, isolated databases and blank API keys.

Read-only checks confirm v5 loaded in the existing backend, 24 protected source hashes unchanged, the saved failure unchanged and all inspected contract-version/grant/generation/media/royalty/invoice rows unchanged. SQLite integrity is OK with zero foreign-key errors. No schema or private-media change. The frontend production Webpack build also passes (21 static pages); no frontend source change/browser-suite rerun.

No new live Fish generation has been run. Another **owner-authorized new request** is needed to verify actual provider output and account behavior. A successful mock/FFmpeg test is not a successful Fish API result. An unindexed MP3's complete HTTP transfer and decodable frames cannot independently attest the provider's intended final duration; retain the existing uncertainty note and listen/review manually.

## Next manual test

The existing backend may reload automatically; otherwise restart it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1
```

Confirm Integration status reports v5. In Studio → Generate advertisement, explicitly select Fish Audio and the current Fish grant. For the supplied approved version 4, enter **consumer products** in Campaign category; placeholder text is not a saved value. Use the other approved campaign fields and review the script/transfer confirmation. Choose **Start a new generation request**, then generate once. The prior FAILED job must remain unchanged.

On success, inspect the saved receipt for requested MP3/44100/128, completed HTTP, actual MP3/FFprobe facts and normalized WAV/24000/mono/16-bit. Play the output, then run the normal analysis and artist reviews. On failure, inspect the safe category and do not repeat automatically. No PayPal action is part of this test.
