"""Failure diagnostics retain actionable categories, never provider private text."""

import json

import httpx
import pytest

from app import voice_generation
from app.config import settings
from app.voice_errors import VoiceProviderFailure, diagnostic
from pydantic import SecretStr
from test_voice_generation import setup_grant, wav_bytes

PRIVATE = "secret-key-never-display voicekey_private private-contract-passage"


@pytest.mark.parametrize(
    "body,category",
    [
        (
            {
                "error": {
                    "status": "INVALID_ARGUMENT",
                    "message": "Unknown name 'replicated' at 'voice': " + PRIVATE,
                }
            },
            "REQUEST_SCHEMA",
        ),
        (
            {"error": {"message": "Consent audio failed verification of the required phrase. " + PRIVATE}},
            "CONSENT_VERIFICATION",
        ),
        ({"error": {"message": "Reference and consent speaker mismatch. " + PRIVATE}}, "SPEAKER_MISMATCH"),
        (
            {"error": {"message": "Voice replication requires a paid tier project. " + PRIVATE}},
            "BILLING_OR_PAID_TIER",
        ),
        ({"error": {"message": "Invalid audio sample rate. " + PRIVATE}}, "AUDIO_REJECTED"),
        (
            {"error": {"message": "Synthetic audio with SynthID is not allowed. " + PRIVATE}},
            "SYNTHETIC_AUDIO_REJECTED",
        ),
        (
            {
                "error": {
                    "message": PRIVATE,
                    "details": [{"reason": "BILLING_DISABLED", "metadata": {"credential": PRIVATE}}],
                }
            },
            "BILLING_OR_PAID_TIER",
        ),
        ({"error": {"message": PRIVATE}}, "INVALID_REQUEST_UNSPECIFIED"),
        (
            {
                "error": {
                    "message": "Model 'gemini-3.8-flash-lite-tts' does not support Voice Replication. "
                    + PRIVATE
                }
            },
            "MODEL_ACCESS",
        ),
    ],
)
def test_safe_categorization_never_echoes_provider_body(body, category):
    response = httpx.Response(400, json=body)
    detail = diagnostic("voice_replication", response=response)
    assert detail["category"] == category
    assert detail["provider_http_status"] == 400
    rendered = json.dumps(detail) + VoiceProviderFailure(detail).detail
    assert PRIVATE not in rendered and "voicekey_private" not in rendered
    if category == "REQUEST_SCHEMA":
        assert detail["request_fields"] == ["replicated", "voice"]
    if category == "MODEL_ACCESS":
        assert "GEMINI_VOICE_REPLICATION_MODEL" in VoiceProviderFailure(detail).detail


@pytest.mark.parametrize(
    "content", [b"private provider HTML", b"x" * 70000, b"[]", b'{"error":{"status":[],"details":[]}}']
)
def test_invalid_or_oversized_error_body_remains_safe(content):
    result = diagnostic("voice_replication", response=httpx.Response(400, content=content))
    assert result["category"] == "INVALID_REQUEST_UNSPECIFIED"
    assert "body" not in result and "message" not in result


def test_synthesis_failure_identifies_second_stage_and_never_replays(monkeypatch, tmp_path):
    original = voice_generation.genai.Client
    calls = []
    data = wav_bytes()

    def handler(request):
        calls.append(request.url.path)
        if request.url.path.endswith("/voices"):
            return httpx.Response(200, json={"type": "replicated", "key": "voicekey_test_only"})
        return httpx.Response(
            400,
            json={
                "error": {
                    "status": "INVALID_ARGUMENT",
                    "message": "Unknown field 'speech_config'. " + PRIVATE,
                }
            },
        )

    def client(**kwargs):
        hooks = kwargs["http_options"].httpx_client.event_hooks
        options = kwargs["http_options"].model_copy(
            update={"httpx_client": httpx.Client(transport=httpx.MockTransport(handler), event_hooks=hooks)}
        )
        return original(api_key=kwargs["api_key"], http_options=options)

    monkeypatch.setattr(voice_generation.genai, "Client", client)
    monkeypatch.setattr(settings, "enable_voice_generation", True)
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("test-only-key"))
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    monkeypatch.setattr(voice_generation, "replication_wav", lambda *args: data)
    with pytest.raises(VoiceProviderFailure) as error:
        voice_generation.synthesize(
            tmp_path / "reference", tmp_path / "consent", "Original demonstration text.", "test"
        )
    result = error.value.diagnostic
    assert result["stage"] == "speech_synthesis" and result["voice_replication_accepted"]
    assert result["category"] == "REQUEST_SCHEMA" and result["request_fields"] == ["speech_config"]
    assert len(calls) == 2 and PRIVATE not in error.value.detail


def test_failed_job_keeps_stage_diagnostic_without_success_receipt(
    client, artist, studio, monkeypatch, terms
):
    _, _, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)

    def fail(*args):
        raise VoiceProviderFailure(
            diagnostic(
                "voice_replication",
                response=httpx.Response(
                    400, json={"error": {"message": "Consent verification failed. " + PRIVATE}}
                ),
            )
        )

    monkeypatch.setattr(voice_generation, "synthesize", fail)
    response = client.post("/api/generations", headers=studio, json=body)
    assert response.status_code == 502 and "voice replication" in response.json()["detail"]
    saved = client.get("/api/generations", headers=studio).json()[0]
    assert saved["status"] == "FAILED" and saved["asset_id"] is None
    assert saved["receipt"]["failure"]["stage"] == "voice_replication"
    assert saved["receipt"]["failure"]["category"] == "CONSENT_VERIFICATION"
    assert saved["receipt"]["requested_replication_model"] == settings.gemini_voice_replication_model
    assert saved["receipt"]["requested_model"] == settings.gemini_tts_model
    assert "succeeded_at" not in saved["receipt"] and PRIVATE not in json.dumps(saved)
    monkeypatch.setattr(
        voice_generation,
        "synthesize",
        lambda *args: pytest.fail("Saved failed request must not be repeated."),
    )
    assert client.post("/api/generations", headers=studio, json=body).json()["id"] == saved["id"]
