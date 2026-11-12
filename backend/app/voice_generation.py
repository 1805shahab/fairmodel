"""Consented Gemini replication and TTS, isolated from compliance and finance."""

import base64
import hashlib
import io
import wave
from pathlib import Path

import httpx
from fastapi import HTTPException
from google import genai
from google.genai import types

from . import audio
from .voice_errors import VoiceProviderFailure, diagnostic
from .config import settings
from .db import now

CONSENT_PHRASE = (
    "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model."
)


def require_available():
    if not settings.enable_voice_generation:
        raise HTTPException(
            409,
            "Voice generation is disabled. Set ENABLE_VOICE_GENERATION=true and restart the backend after reviewing Gemini paid-tier access and costs.",
        )
    if not settings.gemini_api_key.get_secret_value():
        raise HTTPException(503, "Gemini API credentials are not configured for voice generation.")


def checked_recording(path: Path, minimum: int, maximum: int, label: str = "Recording"):
    metadata = audio.probe(path)
    from decimal import Decimal

    if not minimum <= Decimal(metadata["duration_seconds"]) <= maximum:
        raise HTTPException(
            422,
            f"{label} measures {metadata['duration_seconds']} seconds. "
            f"Its required length is {minimum}-{maximum} seconds; it does not need to be exactly {maximum} seconds.",
        )
    return metadata


def replication_wav(path: Path, target: Path) -> bytes:
    audio.run(
        [
            settings.ffmpeg_binary,
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            "24000",
            "-c:a",
            "pcm_s16le",
            str(target),
        ]
    )
    data = target.read_bytes()
    if len(data) > 2 * 1024 * 1024:
        raise HTTPException(422, "Normalized consent/reference recording is too large.")
    return data


def validate_wav(data: bytes, provider: str = "Gemini"):
    if not data or len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            502, f"{provider} returned an empty or oversized audio result. No asset was created."
        )
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            frames, rate = wav.getnframes(), wav.getframerate()
            channels, width = wav.getnchannels(), wav.getsampwidth()
            if (
                channels != 1
                or width != 2
                or rate != 24000
                or not 0.1 <= frames / rate <= settings.max_audio_seconds
                or len(wav.readframes(frames)) != frames * channels * width
            ):
                raise ValueError
    except (wave.Error, EOFError, ValueError, ZeroDivisionError):
        raise HTTPException(
            502, f"{provider} did not return a valid 24kHz mono PCM16 WAV. No fixture fallback was used."
        ) from None


def synthesize(reference: Path, consent: Path, script: str, work_id: str) -> tuple[bytes, dict]:
    """No prebuilt-voice substitution, automatic retry, persistent voice profile or key logging."""
    require_available()
    source_temp = settings.storage_dir / f"{work_id}-source.wav"
    consent_temp = settings.storage_dir / f"{work_id}-consent.wav"
    sent = set()
    last_status = {}
    failures = {}
    stage = "voice_replication"

    def prevent_replay(request):
        operation = (request.method, request.url.path)
        if request.method == "POST" and operation in sent:
            error = RuntimeError("Automatic generation replay blocked before transmission.")
            error.status_code = last_status.get(operation)
            raise error
        sent.add(operation)

    def remember_status(response):
        last_status[(response.request.method, response.request.url.path)] = response.status_code
        if response.status_code >= 400:
            response.read()
            failures[stage] = diagnostic(stage, response=response)

    try:
        source = replication_wav(reference, source_temp)
        permission = replication_wav(consent, consent_temp)
        # Current SDK maps its minimum total-attempt count to an extra generated
        # API retry. A public HTTPX hook independently prevents any POST replay.
        with (
            httpx.Client(
                timeout=75, event_hooks={"request": [prevent_replay], "response": [remember_status]}
            ) as transport,
            genai.Client(
                api_key=settings.gemini_api_key.get_secret_value(),
                http_options=types.HttpOptions(
                    api_version="v1beta",
                    timeout=75000,
                    retry_options=types.HttpRetryOptions(attempts=1),
                    httpx_client=transport,
                ),
            ) as client,
        ):
            voice = client.voices.create(
                store=False,
                voice={
                    "model": settings.gemini_voice_replication_model,
                    "type": "replicated",
                    "replicated": {
                        "source_audio": {"mime_type": "audio/wav", "data": base64.b64encode(source).decode()},
                        "consent_audio": {
                            "mime_type": "audio/wav",
                            "data": base64.b64encode(permission).decode(),
                        },
                    },
                },
                timeout=75,
            )
            key = getattr(voice, "key", None)
            if (
                getattr(voice, "type", None) != "replicated"
                or not isinstance(key, str)
                or not key.startswith("voicekey_")
            ):
                raise HTTPException(
                    502,
                    "Gemini did not return a stateless replicated voice. No prebuilt voice was substituted.",
                )
            stage = "speech_synthesis"
            result = client.interactions.create(
                model=settings.gemini_tts_model,
                input=[{"type": "user_input", "content": [{"type": "text", "text": script}]}],
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": key}]},
                store=False,
                timeout=75,
                automatic_continuation=False,
            )
            if getattr(result, "status", None) != "completed":
                raise HTTPException(
                    502,
                    "Gemini did not complete this speech result. No partial asset or automatic continuation was created.",
                )
            output = getattr(result, "output_audio", None)
            encoded = getattr(output, "data", None)
            if not isinstance(encoded, str) or len(encoded) > 34 * 1024 * 1024:
                raise HTTPException(502, "Gemini returned no usable audio. No fixture fallback was used.")
            try:
                data = base64.b64decode(encoded, validate=True)
            except ValueError:
                raise HTTPException(502, "Gemini returned invalid audio encoding.") from None
            validate_wav(data)
            return data, {
                "service": "Gemini TTS",
                "provider": "gemini",
                "mode": "live",
                "succeeded_at": now(),
                "requested_model": settings.gemini_tts_model,
                "requested_replication_model": settings.gemini_voice_replication_model,
                "returned_model": getattr(result, "model", None),
                "voice_mode": "replicated",
                "provider_consent_accepted": True,
                "voice_storage": "stateless; key discarded after request",
                "audio_sha256": hashlib.sha256(data).hexdigest(),
                "identity_note": "Provider acceptance is not independent FairModel speaker verification or final campaign authorization.",
            }
    except HTTPException:
        raise
    except Exception as error:
        detail = failures.get(stage) or diagnostic(stage, error=error)
        raise VoiceProviderFailure(detail) from None
    finally:
        source_temp.unlink(missing_ok=True)
        consent_temp.unlink(missing_ok=True)
