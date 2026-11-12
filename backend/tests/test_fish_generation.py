"""Mocked Fish HTTP only. Test recordings/keys must never reach a real service."""

import hashlib
import json
import sqlite3

import httpx
import msgpack
import pytest
from fastapi import HTTPException
from pydantic import SecretStr, ValidationError
from sqlalchemy import create_engine

from app import fish_generation, voice_generation
from app.config import Settings, settings
from app.db import VoiceGrant
from app.migrations import migrate, SCHEMA_VERSION
from test_voice_generation import setup_grant, wav_bytes, session
from test_workflow import mock_audio, process


def fish_case(client, artist, studio, monkeypatch, terms):
    reference, google, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)
    consent = {
        "reference_id": reference["id"],
        "license_id": google["license_id"],
        "provider": "fish",
        "owner_confirmed": "true",
        "provider_transfer_consent": "true",
        "provider_policy_ack": "true",
        "reference_text": "A synthetic automated-test recording, not a real speaker.",
        "note": "Test-only Fish transfer consent, no real speaker or network operation.",
    }
    result = client.post("/api/voice-grants", headers=artist, data=consent)
    assert result.status_code == 201, result.text
    monkeypatch.setattr(settings, "enable_fish_generation", True)
    monkeypatch.setattr(settings, "fish_api_key", SecretStr("test-only-fish-key"))
    return google, result.json(), consent, body | {"provider": "fish", "grant_id": result.json()["id"]}


def mocked_http(monkeypatch, tmp_path, handler):
    original = fish_generation.httpx.Client
    monkeypatch.setattr(
        fish_generation.httpx,
        "Client",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    monkeypatch.setattr(settings, "enable_voice_generation", True)
    monkeypatch.setattr(settings, "enable_fish_generation", True)
    monkeypatch.setattr(settings, "fish_api_key", SecretStr("test-only-fish-key"))
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    monkeypatch.setattr(fish_generation, "replication_wav", lambda *args: wav_bytes())


def test_exact_free_wire_contract_and_real_wav_validation(monkeypatch, tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        assert str(request.url) == "https://api.fish.audio/v1/tts"
        assert request.headers["model"] == "s2.1-pro-free"
        assert request.headers["authorization"] == "Bearer test-only-fish-key"
        assert request.headers["content-type"] == "application/msgpack"
        payload = msgpack.unpackb(request.content, raw=False)
        assert payload["references"] == [{"audio": wav_bytes(), "text": "Test reference transcript."}]
        assert payload["text"] == "Original test advertisement."
        assert payload["format"] == "mp3" and payload["sample_rate"] == 44100
        assert payload["mp3_bitrate"] == 128
        assert request.headers["accept"] == "audio/mpeg"
        assert "streaming" not in payload
        assert "reference_id" not in payload
        return httpx.Response(200, content=wav_bytes(), headers={"content-type": "audio/wav"})

    mocked_http(monkeypatch, tmp_path, handler)
    data, receipt = fish_generation.synthesize(
        tmp_path / "ref", "Test reference transcript.", "Original test advertisement.", "test"
    )
    assert len(calls) == 1 and data == wav_bytes()
    assert receipt["provider"] == "fish" and receipt["mode"] == "live"
    assert receipt["requested_model"] == "s2.1-pro-free" and receipt["succeeded_at"]
    assert receipt["audio_sha256"] == hashlib.sha256(data).hexdigest()
    assert "not been independently verified" in receipt["identity_note"]
    assert "test-only-fish-key" not in json.dumps(receipt)


@pytest.mark.parametrize("status", [301, 400, 401, 402, 403, 404, 422, 429, 500, 503, "network"])
def test_provider_errors_never_retry_switch_or_leak(monkeypatch, tmp_path, status):
    calls = []
    private = "private-reference secret-token private-provider-message"

    def handler(request):
        calls.append(request)
        if status == "network":
            raise httpx.ReadTimeout(private, request=request)
        return httpx.Response(
            status, json={"message": private}, headers={"location": "https://another-host.invalid"}
        )

    mocked_http(monkeypatch, tmp_path, handler)
    with pytest.raises(fish_generation.FishProviderFailure) as caught:
        fish_generation.synthesize(tmp_path / "ref", "Test transcript.", "Test script.", "error")
    assert len(calls) == 1
    assert private not in str(caught.value.detail) + json.dumps(caught.value.diagnostic)
    assert "No paid request" in caught.value.detail
    assert not (tmp_path / "error-fish-reference.wav").exists()


@pytest.mark.parametrize(
    "bad", [b"", b"not WAV", b'{"message":"private"}', wav_bytes()[:-20], b"x" * (2 * 1024 * 1024)]
)
def test_invalid_outputs_never_become_success(monkeypatch, tmp_path, bad):
    mocked_http(monkeypatch, tmp_path, lambda _: httpx.Response(200, content=bad))
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    with pytest.raises(HTTPException) as caught:
        fish_generation.synthesize(tmp_path / "ref", "Test transcript.", "Test script.", "bad")
    assert "Fish" in caught.value.detail and "Gemini" not in caught.value.detail


@pytest.mark.parametrize("reason", ["disabled", "key", "paid_model", "transcript"])
def test_configuration_blocks_before_transmitting(monkeypatch, tmp_path, reason):
    monkeypatch.setattr(settings, "enable_voice_generation", True)
    monkeypatch.setattr(settings, "enable_fish_generation", True)
    monkeypatch.setattr(settings, "fish_api_key", SecretStr("test-only-key"))
    if reason == "disabled":
        monkeypatch.setattr(settings, "enable_fish_generation", False)
    if reason == "key":
        monkeypatch.setattr(settings, "fish_api_key", SecretStr(""))
    if reason == "paid_model":
        monkeypatch.setattr(settings, "fish_tts_model", "s2.1-pro")
    monkeypatch.setattr(
        fish_generation,
        "replication_wav",
        lambda *args: pytest.fail("Blocked before audio processing/transmission"),
    )
    with pytest.raises(HTTPException):
        fish_generation.synthesize(
            tmp_path / "ref", "" if reason == "transcript" else "Test.", "Test script.", "blocked"
        )


def test_settings_reject_paid_model():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, fish_tts_model="s2.1-pro")


def test_manual_smoke_is_dry_run_without_explicit_execution(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    script = tmp_path / "script.txt"
    script.write_text("Original test advertisement.", encoding="utf-8")
    campaign = tmp_path / "campaign.json"
    campaign.write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "scripts/fish_live_smoke.py"),
            "--grant-id",
            "fictional",
            "--script-file",
            str(script),
            "--campaign-file",
            str(campaign),
            "--request-key",
            "dry_run_test",
            "--port",
            "1",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "DRY RUN" in result.stdout and "Original test" not in result.stdout


def test_separate_provider_consent_and_idempotence(client, artist, studio, monkeypatch, terms):
    google, fish, consent, body = fish_case(client, artist, studio, monkeypatch, terms)
    assert google["id"] != fish["id"] and fish["provider"] == "fish"
    assert client.post("/api/voice-grants", headers=studio, data=consent).status_code == 403
    assert client.post("/api/voice-grants", headers=artist, data=consent).json()["id"] == fish["id"]
    for changed in (
        {"provider_policy_ack": "false"},
        {"provider_transfer_consent": "false"},
        {"owner_confirmed": "false"},
        {"reference_text": "  "},
    ):
        assert client.post("/api/voice-grants", headers=artist, data=consent | changed).status_code == 422
    changed = client.post(
        "/api/voice-grants", headers=artist, data=consent | {"reference_text": "Changed text."}
    )
    assert changed.status_code == 409
    rendered = client.get("/api/voice-grants", headers=studio).text
    assert "consent_path" not in rendered and consent["reference_text"] not in rendered
    assert client.post("/api/generations", headers=artist, json=body).status_code == 403
    monkeypatch.setattr(
        fish_generation, "synthesize", lambda *args: pytest.fail("Mismatched consent must not call Fish")
    )
    assert (
        client.post("/api/generations", headers=studio, json=body | {"grant_id": google["id"]}).status_code
        == 409
    )
    monkeypatch.setattr(
        voice_generation, "synthesize", lambda *args: pytest.fail("Fish consent must not authorize Google")
    )
    assert (
        client.post("/api/generations", headers=studio, json=body | {"provider": "gemini"}).status_code == 409
    )


def test_fish_generation_enters_existing_review_and_finance_pipeline(
    client, artist, studio, monkeypatch, terms
):
    _, grant, _, body = fish_case(client, artist, studio, monkeypatch, terms)
    calls = []

    def synthesize(*args):
        calls.append(args)
        return wav_bytes(), {
            "provider": "fish",
            "service": "Fish Audio",
            "mode": "mocked test HTTP",
            "requested_model": "s2.1-pro-free",
        }

    monkeypatch.setattr(fish_generation, "synthesize", synthesize)
    monkeypatch.setattr(voice_generation, "synthesize", lambda *args: pytest.fail("No Gemini fallback"))
    response = client.post("/api/generations", headers=studio, json=body)
    assert response.status_code == 201, response.text
    job = response.json()
    assert job["provider"] == "fish" and job["status"] == "SUCCEEDED"
    assert client.post("/api/generations", headers=studio, json=body).json()["id"] == job["id"]
    assert (
        client.post("/api/generations", headers=studio, json=body | {"provider": "gemini"}).status_code == 409
    )
    assert len(calls) == 1
    asset = client.get(f"/api/assets/{job['asset_id']}", headers=studio).json()
    assert asset["status"] == "UPLOADED" and asset["analysis"] is None
    assert asset["license_version"] == grant["license_version"]
    assert (
        asset["authorization_state"] == "unresolved"
        and "Fish Audio" in asset["campaign"]["generation_provider"]
    )
    assert client.get("/api/royalties", headers=artist).json() == []
    assert client.get("/api/invoices", headers=artist).json() == []
    mock_audio(monkeypatch, "45")
    assert process(client, studio, job["asset_id"], authorize_usage=False)["status"] == "NEEDS_REVIEW"
    assert process(client, studio, job["asset_id"])["status"] == "ADDITIONAL_ROYALTY_DUE"
    assert client.get("/api/royalties", headers=artist).json()[0]["amount"] == "30.00"
    assert client.get("/api/invoices", headers=artist).json() == []


def test_failed_fish_job_is_durable_and_not_replayed(client, artist, studio, monkeypatch, terms):
    _, _, _, body = fish_case(client, artist, studio, monkeypatch, terms)
    monkeypatch.setattr(
        fish_generation,
        "synthesize",
        lambda *args: (_ for _ in ()).throw(fish_generation.FishProviderFailure(402)),
    )
    first = client.post("/api/generations", headers=studio, json=body)
    assert first.status_code == 502
    monkeypatch.setattr(
        fish_generation, "synthesize", lambda *args: pytest.fail("No replay of saved failure")
    )
    saved = client.post("/api/generations", headers=studio, json=body).json()
    assert saved["status"] == "FAILED" and saved["provider"] == "fish" and saved["asset_id"] is None
    assert saved["receipt"]["failure"]["category"] == "FREE_ACCESS_UNAVAILABLE"
    assert "succeeded_at" not in saved["receipt"]
    assert client.get("/api/royalties", headers=artist).json() == []


@pytest.mark.parametrize("reason", ["revoked", "version", "scope", "disabled", "changed_file", "during_call"])
def test_fish_respects_current_license_and_permission(client, artist, studio, monkeypatch, terms, reason):
    _, grant, _, body = fish_case(client, artist, studio, monkeypatch, terms)
    if reason == "revoked":
        client.post(f"/api/voice-grants/{grant['id']}/revoke", headers=artist)
    elif reason == "version":
        from app.db import License

        gen = session()
        db = next(gen)
        db.get(License, grant["license_id"]).version += 1
        db.commit()
        gen.close()
    elif reason == "scope":
        body["campaign"]["medium"] = "television"
    elif reason == "disabled":
        monkeypatch.setattr(settings, "enable_fish_generation", False)
    elif reason == "changed_file":
        from pathlib import Path

        gen = session()
        db = next(gen)
        Path(db.get(VoiceGrant, grant["id"]).consent_path).write_bytes(b"changed")
        gen.close()

    def synthesize(*args):
        if reason != "during_call":
            pytest.fail("Invalid Fish request must not run")
        client.post(f"/api/voice-grants/{grant['id']}/revoke", headers=artist)
        return wav_bytes(), {"mode": "mocked test"}

    monkeypatch.setattr(fish_generation, "synthesize", synthesize)
    assert client.post("/api/generations", headers=studio, json=body).status_code == 409
    assert client.get("/api/assets", headers=studio).json() == []
    assert client.get("/api/royalties", headers=artist).json() == []


def test_v6_migration_preserves_grants_jobs_and_provider_unique_key(tmp_path):
    target = tmp_path / "legacy.db"
    with sqlite3.connect(target) as db:
        # Use the actual pre-Fish schema/records, with fictional values only.
        db.executescript("""
            CREATE TABLE personas(id VARCHAR PRIMARY KEY);
            CREATE TABLE licenses(id VARCHAR PRIMARY KEY);
            CREATE TABLE reference_voices(id VARCHAR PRIMARY KEY);
            CREATE TABLE media_assets(id VARCHAR PRIMARY KEY);
            CREATE TABLE voice_generation_grants(id VARCHAR PRIMARY KEY, created_at VARCHAR NOT NULL, updated_at VARCHAR NOT NULL,
              reference_id VARCHAR NOT NULL REFERENCES reference_voices(id), license_id VARCHAR NOT NULL REFERENCES licenses(id),
              license_version INTEGER NOT NULL, artist_id VARCHAR NOT NULL REFERENCES personas(id), studio_id VARCHAR NOT NULL REFERENCES personas(id),
              consent_path VARCHAR NOT NULL, consent_hash VARCHAR NOT NULL, note VARCHAR NOT NULL, revoked_at VARCHAR,
              UNIQUE(reference_id,license_id,license_version));
            CREATE TABLE speech_generations(id VARCHAR PRIMARY KEY,grant_id VARCHAR REFERENCES voice_generation_grants(id));
            INSERT INTO personas VALUES('artist'),('studio'); INSERT INTO licenses VALUES('license');
            INSERT INTO reference_voices VALUES('reference');
            INSERT INTO voice_generation_grants VALUES('grant','time','time','reference','license',4,'artist','studio','private','hash','note',NULL);
            INSERT INTO speech_generations VALUES('job','grant'); PRAGMA user_version=6;
        """)
    engine = create_engine("sqlite:///" + target.as_posix())
    backup = migrate(engine)
    assert backup and backup.is_file()
    with sqlite3.connect(backup) as original:
        assert original.execute("pragma user_version").fetchone()[0] == 6
        assert "provider" not in {
            r[1] for r in original.execute("pragma table_info(voice_generation_grants)")
        }
    assert migrate(engine) is None
    with sqlite3.connect(target) as db:
        assert db.execute("select provider,reference_text,note from voice_generation_grants").fetchone() == (
            "gemini",
            None,
            "note",
        )
        assert db.execute("select id,grant_id,provider from speech_generations").fetchone() == (
            "job",
            "grant",
            "gemini",
        )
        assert db.execute("pragma foreign_key_check").fetchall() == []
        db.execute(
            "INSERT INTO voice_generation_grants VALUES('fish','time','time','reference','license',4,'artist','studio','private','hash','note',NULL,'fish','transcript')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO voice_generation_grants VALUES('fish2','time','time','reference','license',4,'artist','studio','private','hash','note',NULL,'fish','transcript')"
            )
    engine.dispose()
    assert SCHEMA_VERSION == 7
