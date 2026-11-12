import base64
import io
import json
import wave

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from app import audio, voice_generation
from app.config import Settings, settings
from app.db import License, Persona, get_session
from app.main import app
from test_workflow import mock_audio, process, setup_license


def wav_bytes(seconds=1):
    stream = io.BytesIO()
    with wave.open(stream, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(b"\x01\x00" * int(24000 * seconds))
    return stream.getvalue()


def session():
    return app.dependency_overrides[get_session]()


def setup_grant(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    monkeypatch.setattr(
        audio,
        "probe",
        lambda path: {"duration_seconds": "12", "format": "wav", "sample_rate": 24000, "channels": 1},
    )
    reference = client.post(
        "/api/references",
        headers=artist,
        data={"consent": "true"},
        files={"file": ("test-reference.wav", wav_bytes(), "audio/wav")},
    ).json()
    data = {
        "reference_id": reference["id"],
        "license_id": license_["id"],
        "owner_confirmed": "true",
        "provider_transfer_consent": "true",
        "note": "Test-only consent record; no real speaker or provider call.",
    }
    file = {"file": ("test-consent.wav", wav_bytes(0.5), "audio/wav")}
    grant = client.post("/api/voice-grants", headers=artist, data=data, files=file)
    assert grant.status_code == 201, grant.text
    monkeypatch.setattr(settings, "enable_voice_generation", True)
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("test-only-key"))
    body = {
        "grant_id": grant.json()["id"],
        "request_key": "generation_test_001",
        "script": "Discover our original everyday collection today.",
        "confirm_provider_use": True,
        "campaign": {
            "name": "Original Launch",
            "medium": "online advertising",
            "region": "US",
            "language": "English",
            "category": "consumer products",
            "intended_use_date": "2026-11-11",
        },
    }
    return reference, grant.json(), data, file, body


def test_generation_requires_separate_consent_and_artist_role(client, artist, studio, monkeypatch, terms):
    reference, grant, data, file, _ = setup_grant(client, artist, studio, monkeypatch, terms)
    assert client.post("/api/voice-grants", headers=studio, data=data, files=file).status_code == 403
    assert (
        client.post(
            "/api/voice-grants",
            headers=artist,
            data=data | {"provider_transfer_consent": "false"},
            files=file,
        ).status_code
        == 422
    )
    assert client.get(f"/api/references/{reference['id']}/audio", headers=artist).content == wav_bytes()
    assert client.get(f"/api/references/{reference['id']}/audio", headers=studio).status_code == 403
    assert client.post("/api/voice-grants", headers=artist, data=data, files=file).json()["id"] == grant["id"]
    rendered = client.get("/api/voice-grants", headers=studio).text
    assert "consent_path" not in rendered and "consent_hash" not in rendered
    assert "path" not in reference


def test_real_pipeline_entry_and_duplicate_intent_has_no_financial_side_effects(
    client, artist, studio, monkeypatch, terms
):
    _, grant, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)
    calls = []

    def fake(*args):
        calls.append(args)
        return wav_bytes(), {
            "service": "Gemini TTS",
            "mode": "mocked HTTP in automated test",
            "succeeded_at": "test receipt",
        }

    monkeypatch.setattr(voice_generation, "synthesize", fake)
    first = client.post("/api/generations", headers=studio, json=body)
    assert first.status_code == 201, first.text
    result = first.json()
    assert result["status"] == "SUCCEEDED"
    assert client.post("/api/generations", headers=studio, json=body).json()["id"] == result["id"]
    assert len(calls) == 1
    assert (
        client.post(
            "/api/generations", headers=studio, json=body | {"script": "A different advertisement."}
        ).status_code
        == 409
    )
    assert client.post("/api/generations", headers=artist, json=body).status_code == 403
    asset = client.get(f"/api/assets/{result['asset_id']}", headers=studio).json()
    assert asset["status"] == "UPLOADED" and asset["analysis"] is None
    assert asset["authorization_state"] == "unresolved"
    assert asset["license_version"] == grant["license_version"]
    assert asset["campaign"]["generation_provider"] == "Gemini TTS / replicated voice"
    assert client.get("/api/royalties", headers=artist).json() == []
    assert client.get("/api/invoices", headers=artist).json() == []
    mock_audio(monkeypatch, seconds="45")
    assert process(client, studio, result["asset_id"], authorize_usage=False)["status"] == "NEEDS_REVIEW"
    assert client.get("/api/royalties", headers=artist).json() == []
    assert process(client, studio, result["asset_id"])["status"] == "ADDITIONAL_ROYALTY_DUE"
    royalties = client.get("/api/royalties", headers=artist).json()
    assert len(royalties) == 1 and royalties[0]["amount"] == "30.00"
    assert royalties[0]["status"] == "PENDING"
    assert client.get("/api/invoices", headers=artist).json() == []


@pytest.mark.parametrize(
    "reason", ["revoked", "stale", "restricted", "missing_confirmation", "disabled", "changed_reference"]
)
def test_invalid_generation_never_calls_provider(client, artist, studio, monkeypatch, terms, reason):
    _, grant, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)
    monkeypatch.setattr(
        voice_generation, "synthesize", lambda *args: pytest.fail("Blocked request must not call Gemini")
    )
    if reason == "revoked":
        assert client.post(f"/api/voice-grants/{grant['id']}/revoke", headers=studio).status_code == 403
        client.post(f"/api/voice-grants/{grant['id']}/revoke", headers=artist)
    elif reason == "stale":
        gen = session()
        db = next(gen)
        db.get(License, grant["license_id"]).version += 1
        db.commit()
        gen.close()
    elif reason == "restricted":
        body["campaign"]["medium"] = "television advertising"
    elif reason == "missing_confirmation":
        body["confirm_provider_use"] = False
    elif reason == "disabled":
        monkeypatch.setattr(settings, "enable_voice_generation", False)
    else:
        from app.db import ReferenceVoice

        gen = session()
        db = next(gen)
        from pathlib import Path

        Path(db.get(ReferenceVoice, grant["reference_id"]).path).write_bytes(b"modified")
        gen.close()
    assert client.post("/api/generations", headers=studio, json=body).status_code in {409, 422}
    assert client.get("/api/generations", headers=studio).json() == []


def test_provider_failure_persists_intent_without_fallback_or_repeat(
    client, artist, studio, monkeypatch, terms
):
    _, _, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)
    calls = []

    def fail(*args):
        calls.append(1)
        raise HTTPException(502, "Gemini denied access. No fixture fallback was used.")

    monkeypatch.setattr(voice_generation, "synthesize", fail)
    assert client.post("/api/generations", headers=studio, json=body).status_code == 502
    replay = client.post("/api/generations", headers=studio, json=body).json()
    assert replay["status"] == "FAILED" and replay["asset_id"] is None and len(calls) == 1
    assert replay["receipt"] == {}
    assert client.get("/api/assets", headers=studio).json() == []


def test_revocation_during_remote_call_prevents_asset(client, artist, studio, monkeypatch, terms):
    _, grant, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)

    def revoke(*args):
        assert client.post(f"/api/voice-grants/{grant['id']}/revoke", headers=artist).status_code == 200
        return wav_bytes(), {"service": "mocked test"}

    monkeypatch.setattr(voice_generation, "synthesize", revoke)
    assert client.post("/api/generations", headers=studio, json=body).status_code == 409
    assert client.get("/api/assets", headers=studio).json() == []
    assert client.get("/api/generations", headers=artist).json()[0]["status"] == "FAILED"


@pytest.mark.parametrize(
    "status,replication_model",
    [(s, "gemini-3.8-flash-tts") for s in [200, 400, 403, 429, 503, "network"]]
    + [(200, "gemini-3.8-flash-lite-tts")],
)
def test_sdk_wire_contract_and_no_hidden_retry(monkeypatch, tmp_path, status, replication_model):
    """Exercise the installed SDK's real request/response serialization with mocked HTTP."""
    original = voice_generation.genai.Client
    calls = []
    audio_data = wav_bytes()

    def transport(request):
        calls.append(request)
        body = json.loads(request.content)
        assert request.url.host == "generativelanguage.googleapis.com"
        if status == "network":
            raise httpx.ReadTimeout("Test-only transport failure", request=request)
        if status != 200:
            return httpx.Response(
                status, json={"error": {"code": status, "message": "test provider failure"}}
            )
        if request.url.path.endswith("/voices"):
            assert body["voice"]["model"] == replication_model
            assert body["store"] is False
            assert body["voice"]["type"] == "replicated"
            assert set(body["voice"]["replicated"]) == {"source_audio", "consent_audio"}
            for field in ("source_audio", "consent_audio"):
                assert body["voice"]["replicated"][field]["mime_type"] == "audio/wav"
                assert base64.b64decode(body["voice"]["replicated"][field]["data"]) == audio_data
            return httpx.Response(200, json={"type": "replicated", "key": "voicekey_test_ephemeral"})
        assert request.url.path.endswith("/interactions")
        assert body["model"] == "gemini-3.8-flash-lite-tts"
        assert body["store"] is False and body["response_format"] == {"type": "audio"}
        assert body["generation_config"]["speech_config"] == [{"voice": "voicekey_test_ephemeral"}]
        return httpx.Response(
            200,
            json={
                "id": "interaction_test",
                "object": "interaction",
                "status": "completed",
                "model": settings.gemini_tts_model,
                "steps": [
                    {
                        "type": "model_output",
                        "content": [
                            {
                                "type": "audio",
                                "mime_type": "audio/wav",
                                "data": base64.b64encode(audio_data).decode(),
                            }
                        ],
                    }
                ],
            },
        )

    def client(**kwargs):
        original_transport = kwargs["http_options"].httpx_client
        options = kwargs["http_options"].model_copy(
            update={
                "httpx_client": httpx.Client(
                    transport=httpx.MockTransport(transport), event_hooks=original_transport.event_hooks
                )
            }
        )
        return original(api_key=kwargs["api_key"], http_options=options)

    monkeypatch.setattr(voice_generation.genai, "Client", client)
    monkeypatch.setattr(settings, "enable_voice_generation", True)
    monkeypatch.setattr(settings, "gemini_voice_replication_model", replication_model)
    monkeypatch.setattr(settings, "gemini_tts_model", "gemini-3.8-flash-lite-tts")
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("test-only-key"))
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    monkeypatch.setattr(voice_generation, "replication_wav", lambda *args: audio_data)
    if status == 200:
        data, receipt = voice_generation.synthesize(
            tmp_path / "ref", tmp_path / "consent", "Original test script.", "test"
        )
        assert data == audio_data and len(calls) == 2
        assert receipt["requested_replication_model"] == replication_model
        assert receipt["requested_model"] == "gemini-3.8-flash-lite-tts"
        assert receipt["voice_mode"] == "replicated" and "voicekey_" not in str(receipt)
    else:
        with pytest.raises(HTTPException) as error:
            voice_generation.synthesize(
                tmp_path / "ref", tmp_path / "consent", "Original test script.", "test"
            )
        assert error.value.status_code == 502 and "No fixture fallback" in error.value.detail
        if status in (400, 403, 429, 503):
            assert f"HTTP {status}" in error.value.detail
        assert error.value.diagnostic["stage"] == "voice_replication"
        assert len(calls) == 1


def test_replication_default_is_independent_of_synthesis(monkeypatch):
    monkeypatch.delenv("GEMINI_VOICE_REPLICATION_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_TTS_MODEL", raising=False)
    configured = Settings(_env_file=None)
    assert configured.gemini_voice_replication_model == "gemini-3.8-flash-tts"
    assert configured.gemini_tts_model == "gemini-3.8-flash-lite-tts"
    monkeypatch.setenv("GEMINI_VOICE_REPLICATION_MODEL", "gemini-3.8-flash-lite-tts")
    configured = Settings(_env_file=None)
    assert configured.gemini_voice_replication_model == "gemini-3.8-flash-lite-tts"


def test_invalid_or_truncated_wav_is_rejected():
    for invalid in (b"not audio", wav_bytes()[:-20]):
        with pytest.raises(HTTPException):
            voice_generation.validate_wav(invalid)


def test_unassigned_studio_cannot_see_grant_or_generate(client, artist, studio, monkeypatch, terms):
    _, _, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)
    gen = session()
    db = next(gen)
    db.add(Persona(id="another_studio", role="studio", name="Unassigned", email="studio@example.test"))
    db.commit()
    gen.close()
    outsider = {"X-Demo-Persona": "another_studio"}
    assert client.get("/api/voice-grants", headers=outsider).json() == []
    assert client.get("/api/generations", headers=outsider).json() == []
    assert client.post("/api/generations", headers=outsider, json=body).status_code == 404


def test_different_requests_returning_identical_audio_do_not_allocate_twice(
    client, artist, studio, monkeypatch, terms
):
    _, _, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)
    monkeypatch.setattr(
        voice_generation, "synthesize", lambda *args: (wav_bytes(), {"service": "mocked test"})
    )
    first = client.post("/api/generations", headers=studio, json=body).json()
    second = client.post(
        "/api/generations", headers=studio, json=body | {"request_key": "generation_test_002"}
    ).json()
    assert first["asset_id"] == second["asset_id"]
    assert len(client.get("/api/assets", headers=studio).json()) == 1
    changed = body | {
        "request_key": "generation_test_003",
        "campaign": body["campaign"] | {"name": "Different campaign"},
    }
    assert client.post("/api/generations", headers=studio, json=changed).status_code == 409
    assert client.get("/api/royalties", headers=artist).json() == []


def test_reference_duration_enforced_from_measured_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(audio, "probe", lambda path: {"duration_seconds": "9.99"})
    with pytest.raises(HTTPException) as error:
        voice_generation.checked_recording(tmp_path / "audio", 10, 30)
    assert error.value.status_code == 422


@pytest.mark.parametrize(
    "reference_seconds,consent_seconds,status,label",
    [
        ("45.401", "30.000", 422, "Selected artist reference sample measures 45.401"),
        ("30.000", "8.000", 201, None),
        ("15.000", "31.000", 422, "Uploaded consent recording measures 31.000"),
    ],
)
def test_grant_identifies_reference_vs_consent_duration(
    client, artist, studio, monkeypatch, terms, reference_seconds, consent_seconds, status, label
):
    from pathlib import Path
    from app.db import ReferenceVoice

    reference, grant, data, file, _ = setup_grant(client, artist, studio, monkeypatch, terms)
    gen = session()
    source = Path(next(gen).get(ReferenceVoice, reference["id"]).path)
    gen.close()
    monkeypatch.setattr(
        audio,
        "probe",
        lambda path: {"duration_seconds": reference_seconds if path == source else consent_seconds},
    )
    response = client.post("/api/voice-grants", headers=artist, data=data, files=file)
    assert response.status_code == status, response.text
    if label:
        assert label in response.json()["detail"]
        assert "does not need to be exactly" in response.json()["detail"]
    else:
        assert response.json()["id"] == grant["id"]


@pytest.mark.parametrize("seconds", ["10.000", "30.000"])
def test_reference_accepts_inclusive_duration_boundaries(monkeypatch, tmp_path, seconds):
    monkeypatch.setattr(audio, "probe", lambda path: {"duration_seconds": seconds})
    assert voice_generation.checked_recording(tmp_path / "audio", 10, 30)["duration_seconds"] == seconds
