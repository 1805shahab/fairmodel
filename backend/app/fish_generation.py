"""Free-model-only inline Fish cloning; no profile creation or automatic retries."""

import hashlib
from pathlib import Path

import httpx
from fastapi import HTTPException

from .config import settings
from .db import now
from .fish_audio import FishAudioFailure, normalize_output
from .voice_generation import replication_wav

MODEL = "s2.1-pro-free"
POLICY = "fish-inline-2026-11-11"
CONSENT_NOTE = (
    "Fish Audio receives the reference audio, its transcript and generation text. "
    "No reusable voice profile is created by FairModel. The free model has no DPA guarantee; "
    "provider retention and terms apply, with no verified zero-retention promise. "
    "Artist consent is an attestation, not independently verified identity."
)


class FishProviderFailure(HTTPException):
    def __init__(self, status=None, response_facts=None):
        category, reason = {
            400: ("INVALID_REQUEST", "rejected the request or reference audio"),
            401: ("AUTHENTICATION", "rejected authentication"),
            402: (
                "FREE_ACCESS_UNAVAILABLE",
                "requires account access/credit despite the free-model request; no paid model was requested",
            ),
            403: ("PERMISSION", "denied access"),
            404: ("MODEL_ACCESS", "could not find the requested resource/model"),
            422: ("VALIDATION", "rejected the request format or input"),
            429: ("RATE_LIMIT", "reported a fair-use/rate limit"),
        }.get(
            status,
            ("PROVIDER_UNAVAILABLE", "reported a service failure")
            if status
            else ("NETWORK_OR_TIMEOUT", "could not complete the request; remote outcome may be unknown"),
        )
        self.diagnostic = {
            "stage": "inline_voice_synthesis",
            "provider_http_status": status,
            "category": category,
        }
        if response_facts is not None:
            self.diagnostic["response"] = response_facts
        code = f" (provider HTTP {status})" if status else ""
        super().__init__(
            502,
            f"Fish Audio {reason}{code}. No paid request, provider switch, fixture fallback or automatic retry was attempted.",
        )


def response_metadata(response):
    """Allowlist HTTP facts; arbitrary header values/body text are private."""
    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    types = {
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/mpeg",
        "audio/mp3",
        "application/octet-stream",
        "application/json",
        "text/html",
        "text/event-stream",
    }
    length = response.headers.get("content-length", "")
    encoding = response.headers.get("content-encoding", "identity").lower()
    return {
        "provider_http_status": response.status_code,
        "content_type": content_type if content_type in types else "other" if content_type else "missing",
        "declared_content_length": int(length)
        if length.isascii() and length.isdigit() and len(length) < 12
        else None,
        "content_encoding": encoding
        if encoding in {"identity", "gzip", "deflate", "br", "zstd"}
        else "other",
        "transfer_mode": "chunked"
        if "chunked" in response.headers.get("transfer-encoding", "").lower()
        else "content_length"
        if length
        else "connection_delimited",
        "api_mode": "one_shot_http",  # Client.stream bounds memory; this is not the SSE API.
        "http_body_complete": False,
        "received_bytes": 0,
        "received_chunks": 0,
    }


def require_available():
    if not settings.enable_voice_generation or not settings.enable_fish_generation:
        raise HTTPException(
            409,
            "Fish generation is disabled. Enable ENABLE_VOICE_GENERATION and ENABLE_FISH_GENERATION after reviewing artist consent and Fish processing terms.",
        )
    if settings.fish_tts_model != MODEL:
        raise HTTPException(409, "Only Fish s2.1-pro-free is permitted; paid/default models are blocked.")
    if not settings.fish_api_key.get_secret_value():
        raise HTTPException(503, "FISH_API_KEY is not configured on the backend.")
    try:
        import msgpack  # noqa: F401
    except ImportError:
        raise HTTPException(
            503, "Install the backend MessagePack dependency from requirements.txt before Fish generation."
        ) from None


def synthesize(reference: Path, reference_text: str, script: str, work_id: str):
    require_available()
    import msgpack

    if not 1 <= len(reference_text.strip()) <= 4000:
        raise HTTPException(422, "The artist must supply the exact reference transcript for Fish cloning.")
    temporary = settings.storage_dir / f"{work_id}-fish-reference.wav"
    response_facts = None
    try:
        source = replication_wav(reference, temporary)
        payload = msgpack.packb(
            {
                "text": script,
                "references": [{"audio": source, "text": reference_text}],
                "format": "mp3",
                "sample_rate": 44100,
                "mp3_bitrate": 128,
                "latency": "normal",
            },
            use_bin_type=True,
        )
        # Fixed origin, exact free header, no redirects, no retry transport, no /model calls.
        with httpx.Client(timeout=httpx.Timeout(120, connect=15), follow_redirects=False) as client:
            with client.stream(
                "POST",
                "https://api.fish.audio/v1/tts",
                content=payload,
                headers={
                    "Authorization": f"Bearer {settings.fish_api_key.get_secret_value()}",
                    "Content-Type": "application/msgpack",
                    "model": MODEL,
                    "Accept": "audio/mpeg",
                    "Accept-Encoding": "identity",
                },
            ) as response:
                response_facts = response_metadata(response)
                response_facts.update(requested_format="mp3", consumption="complete_body_before_validation")
                if response.status_code != 200:
                    raise FishProviderFailure(response.status_code, response_facts)
                if response_facts["content_type"] in {"application/json", "text/html", "text/event-stream"}:
                    raise FishAudioFailure("PROVIDER_NON_AUDIO_RESPONSE")
                data = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    data.extend(chunk)
                    response_facts["received_bytes"] = len(data)
                    response_facts["received_chunks"] += 1
                    if len(data) > settings.max_upload_mb * 1024 * 1024:
                        raise FishAudioFailure("OUTPUT_TOO_LARGE", {"response_bytes_at_least": len(data)})
                # Decoded lengths differ from wire lengths for compressed HTTP.
                declared = response_facts["declared_content_length"]
                if declared is not None and response_facts["content_encoding"] == "identity":
                    response_facts["content_length_matches"] = declared == len(data)
                    if declared != len(data):
                        raise FishAudioFailure("HTTP_LENGTH_MISMATCH", {"response_bytes": len(data)})
                response_facts["http_body_complete"] = True
        output, processing = normalize_output(bytes(data), work_id)
        return output, {
            "provider": "fish",
            "service": "Fish Audio",
            "mode": "live",
            "requested_model": MODEL,
            "requested_output": {"format": "mp3", "sample_rate": 44100, "mp3_bitrate": 128},
            "model_selection": "exact model request header; response does not independently attest the served model",
            "succeeded_at": now(),
            "voice_mode": "inline_reference",
            "voice_storage": "no reusable voice profile requested; provider retention terms apply",
            "consent_policy": POLICY,
            "audio_sha256": hashlib.sha256(output).hexdigest(),
            "audio_processing": processing,
            "provider_http_status": 200,
            "response": response_facts,
            "reference_audio_sha256": hashlib.sha256(source).hexdigest(),
            "reference_text_sha256": hashlib.sha256(reference_text.encode()).hexdigest(),
            "identity_note": "Artist-attested consent; identity has not been independently verified.",
        }
    except FishAudioFailure as error:
        if response_facts is not None:
            error.diagnostic["response"] = response_facts
        raise
    except httpx.HTTPError as error:
        if response_facts is not None and response_facts["provider_http_status"] == 200:
            category = (
                "TRUNCATED_PROVIDER_RESPONSE"
                if isinstance(error, httpx.RemoteProtocolError)
                else "INCOMPLETE_PROVIDER_RESPONSE"
            )
            failure = FishAudioFailure(category, {"response_bytes": response_facts["received_bytes"]})
            failure.diagnostic["response"] = response_facts
            raise failure from None
        raise FishProviderFailure(response_facts=response_facts) from None
    finally:
        temporary.unlink(missing_ok=True)
