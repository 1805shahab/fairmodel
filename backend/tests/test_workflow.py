import io
import json
import wave
from pathlib import Path

import pytest
from fastapi import HTTPException
from reportlab.pdfgen import canvas

from app import ai, audio
from app.schemas import ContentFindings


def pdf_bytes():
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream)
    pdf.drawString(
        50, 760, "Voice artist Amara. Included duration 30 seconds. Additional rate 2 USD per second."
    )
    pdf.save()
    return stream.getvalue()


def setup_license(client, artist, monkeypatch, terms):
    monkeypatch.setattr(ai, "extract_contract", lambda *args: (terms, "test_mock (not Gemini)"))
    result = client.post(
        "/api/licenses", headers=artist, json={"title": "Test agreement", "studio_id": "studio_demo"}
    )
    assert result.status_code == 201, result.text
    license_id = result.json()["id"]
    upload = client.post(
        f"/api/licenses/{license_id}/contract",
        headers=artist,
        files={"file": ("license.pdf", pdf_bytes(), "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    extracted = client.post(
        f"/api/licenses/{license_id}/extract", headers=artist, json={"use_demo_fixture": False}
    )
    assert extracted.status_code == 200, extracted.text
    license_ = extracted.json()
    approval = client.post(
        f"/api/licenses/{license_id}/approve",
        headers=artist,
        json={
            "terms": license_["terms"],
            "expected_version": license_["version"],
            "note": "Reviewed source terms.",
        },
    )
    assert approval.status_code == 200, approval.text
    return approval.json()


def mock_audio(monkeypatch, seconds="45"):
    monkeypatch.setattr(
        audio,
        "probe",
        lambda path: {"duration_seconds": "50", "format": "wav", "sample_rate": 16000, "channels": 1},
    )
    monkeypatch.setattr(audio, "normalize", lambda path, output: output.write_bytes(b"test normalized"))
    monkeypatch.setattr(
        audio,
        "speech_activity",
        lambda path: {
            "spoken_seconds": seconds,
            "speech_segments": [],
            "measurement_uncertain": False,
            "vad": "test mock",
            "measurement_note": "test mock",
        },
    )
    monkeypatch.setattr(
        ai,
        "transcribe",
        lambda *args: {"transcript": "A new collection.", "timestamps": [], "provider": "test mock"},
    )
    monkeypatch.setattr(
        ai, "content_findings", lambda *args: (ContentFindings(findings=[], uncertainty=[]), "test mock")
    )


def submit(client, studio, license_id, content=b"test audio", **metadata):
    campaign = {
        "name": "Launch",
        "region": "US",
        "medium": "online advertising",
        "language": "English",
        "intended_use_date": "2026-11-06",
        **metadata,
    }
    return client.post(
        "/api/assets",
        headers=studio,
        data={"license_id": license_id, "campaign": json.dumps(campaign)},
        files={"file": ("asset.wav", content, "audio/wav")},
    )


def process(client, studio, asset_id):
    response = client.post(f"/api/assets/{asset_id}/analyze", headers=studio, json={})
    assert response.status_code == 200, response.text
    response = client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={})
    assert response.status_code == 200, response.text
    return response.json()


def test_complete_approval_invoice_and_duplicate_workflow(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    upload = submit(client, studio, license_["id"])
    assert upload.status_code == 201
    asset_id = upload.json()["id"]
    assert process(client, studio, asset_id)["status"] == "ADDITIONAL_ROYALTY_DUE"
    royalties = client.get("/api/royalties", headers=artist).json()
    assert len(royalties) == 1 and royalties[0]["amount"] == "30.00"
    royalty_id = royalties[0]["id"]
    assert client.post(f"/api/royalties/{royalty_id}/invoice", headers=artist).status_code == 409
    assert (
        client.post(
            f"/api/royalties/{royalty_id}/decision",
            headers=studio,
            json={"approve": True, "note": "Review complete"},
        ).status_code
        == 403
    )
    approved = client.post(
        f"/api/royalties/{royalty_id}/decision",
        headers=artist,
        json={"approve": True, "note": "Reviewed evidence and charges."},
    )
    assert approved.status_code == 200
    invoice = client.post(f"/api/royalties/{royalty_id}/invoice", headers=artist).json()
    repeated_invoice = client.post(f"/api/royalties/{royalty_id}/invoice", headers=artist).json()
    assert invoice["id"] == repeated_invoice["id"]
    assert invoice["provider_id"].startswith("SIMULATED-") and invoice["simulated"]
    assert "NO REAL FUNDS" in invoice["notice"]
    invoice_id = invoice["id"]
    assert (
        client.post(
            f"/api/invoices/{invoice_id}/simulate-payment",
            headers=studio,
            json={"event_key": "pay_before_send"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/invoices/{invoice_id}/send", headers=artist, json={"event_key": "send_once_123"}
        ).status_code
        == 200
    )
    for _ in range(2):
        paid = client.post(
            f"/api/invoices/{invoice_id}/simulate-payment",
            headers=studio,
            json={"event_key": "payment_once_123"},
        )
        assert paid.status_code == 200
        assert paid.json()["status"] == "PAID_SIMULATED"
    detail = client.get(f"/api/invoices/{invoice_id}", headers=artist).json()
    assert len(detail["events"]) == 3
    assert (
        client.post(
            f"/api/invoices/{invoice_id}/send", headers=artist, json={"event_key": "send_again_123"}
        ).status_code
        == 409
    )
    duplicate = submit(
        client, studio, license_["id"], name="Different metadata cannot bypass duplicate check"
    )
    assert duplicate.status_code == 200 and duplicate.json()["duplicate"]
    assert duplicate.json()["id"] == asset_id
    process(client, studio, asset_id)
    assert len(client.get("/api/royalties", headers=artist).json()) == 1
    assert (
        client.get("/api/analytics", headers=artist).json()["totals_by_currency"]["USD"]["paid_simulated"]
        == "30.00"
    )
    assert len(client.get("/api/audit", headers=artist).json()) >= 8


@pytest.mark.parametrize(
    "metadata,status",
    [({"category": "political advertising"}, "RESTRICTED_USAGE"), ({"region": ""}, "NEEDS_REVIEW")],
)
def test_review_or_restriction_never_allocates_royalty(
    client, artist, studio, monkeypatch, terms, metadata, status
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"], **metadata).json()["id"]
    assert process(client, studio, asset_id)["status"] == status
    assert client.get("/api/royalties", headers=artist).json() == []
    assert client.get("/api/invoices", headers=artist).json() == []


def test_metadata_recovery(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"], region="").json()["id"]
    assert process(client, studio, asset_id)["status"] == "NEEDS_REVIEW"
    fixed = client.patch(
        f"/api/assets/{asset_id}/campaign",
        headers=studio,
        json={
            "name": "Launch",
            "region": "US",
            "medium": "online advertising",
            "language": "English",
            "intended_use_date": "2026-11-06",
        },
    )
    assert fixed.status_code == 200
    assert process(client, studio, asset_id)["status"] == "ADDITIONAL_ROYALTY_DUE"
    assert (
        client.patch(
            f"/api/assets/{asset_id}/campaign", headers=studio, json=fixed.json()["campaign"]
        ).status_code
        == 409
    )


def test_cumulative_allocation_persists(client, artist, studio, monkeypatch, terms):
    terms.billing_basis = "cumulative"
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch, "20")
    first = submit(client, studio, license_["id"], b"first distinct file").json()["id"]
    second = submit(client, studio, license_["id"], b"second distinct file").json()["id"]
    assert process(client, studio, first)["status"] == "COMPLIANT"
    assert process(client, studio, second)["result"]["calculation"]["amount"] == "20.00"
    assert sorted(x["amount"] for x in client.get("/api/royalties", headers=artist).json()) == [
        "0.00",
        "20.00",
    ]


def test_approval_version_and_immutability(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    assert client.post(f"/api/licenses/{license_['id']}/extract", headers=artist, json={}).status_code == 409
    assert (
        client.post(
            "/api/licenses", headers=studio, json={"title": "Forbidden", "studio_id": "studio_demo"}
        ).status_code
        == 403
    )
    assert client.get("/api/licenses").status_code == 401
    detail = client.get(f"/api/licenses/{license_['id']}", headers=artist).json()
    assert detail["versions"][0]["terms"] == license_["terms"]
    assert "contract_path" not in detail


def test_unknowns_and_stale_reviews_are_explicit(client, artist, monkeypatch):
    from app.schemas import Terms

    monkeypatch.setattr(ai, "extract_contract", lambda *args: (Terms(), "test mock"))
    license_ = client.post(
        "/api/licenses", headers=artist, json={"title": "Unknown terms", "studio_id": "studio_demo"}
    ).json()
    lid = license_["id"]
    client.post(
        f"/api/licenses/{lid}/contract",
        headers=artist,
        files={"file": ("license.pdf", pdf_bytes(), "application/pdf")},
    )
    extracted = client.post(f"/api/licenses/{lid}/extract", headers=artist, json={}).json()
    body = {
        "terms": extracted["terms"],
        "expected_version": extracted["version"],
        "note": "Unknowns remain for review.",
    }
    assert client.post(f"/api/licenses/{lid}/approve", headers=artist, json=body).status_code == 422
    saved = client.put(f"/api/licenses/{lid}/terms", headers=artist, json=body)
    assert saved.status_code == 200
    assert client.put(f"/api/licenses/{lid}/terms", headers=artist, json=body).status_code == 409
    body.update({"expected_version": saved.json()["version"], "acknowledge_unknowns": True})
    assert client.post(f"/api/licenses/{lid}/approve", headers=artist, json=body).status_code == 200


def test_invalid_pdf_and_audio(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    bad = submit(client, studio, license_["id"], b"not audio at all")
    assert bad.status_code == 422
    draft = client.post(
        "/api/licenses", headers=artist, json={"title": "Invalid PDF", "studio_id": "studio_demo"}
    ).json()
    assert (
        client.post(
            f"/api/licenses/{draft['id']}/contract",
            headers=artist,
            files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
        ).status_code
        == 422
    )


def test_persistent_transcription_error_and_retry(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]

    def unavailable(*args):
        raise HTTPException(502, "Provider unavailable")

    monkeypatch.setattr(ai, "transcribe", unavailable)
    assert client.post(f"/api/assets/{asset_id}/analyze", headers=studio, json={}).status_code == 502
    failed = client.get(f"/api/assets/{asset_id}", headers=studio).json()
    assert failed["status"] == "FAILED" and failed["analysis"] is None
    mock_audio(monkeypatch)
    assert client.post(f"/api/assets/{asset_id}/analyze", headers=studio, json={}).status_code == 200


def test_reference_requires_consent(client, artist):
    assert (
        client.post(
            "/api/references",
            headers=artist,
            data={"consent": "false"},
            files={"file": ("voice.wav", b"voice", "audio/wav")},
        ).status_code
        == 422
    )


def test_unassigned_persona_cannot_access_private_records(client, artist, studio, monkeypatch, terms):
    from app.db import Persona, get_session
    from app.main import app

    license_ = setup_license(client, artist, monkeypatch, terms)
    session_generator = app.dependency_overrides[get_session]()
    session = next(session_generator)
    session.add(Persona(id="other_artist", role="artist", name="Other", email="other@example.test"))
    session.commit()
    session_generator.close()
    unrelated = {"X-Demo-Persona": "other_artist"}
    assert client.get(f"/api/licenses/{license_['id']}", headers=unrelated).status_code == 404
    assert client.get(f"/api/licenses/{license_['id']}/contract", headers=unrelated).status_code == 404
    assert client.get("/api/licenses", headers=unrelated).json() == []
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]
    assert client.get(f"/api/assets/{asset_id}/audio", headers=unrelated).status_code == 404


def test_concurrent_duplicates_allocate_once(client, artist, studio, monkeypatch, terms):
    from concurrent.futures import ThreadPoolExecutor

    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: submit(client, studio, license_["id"]), range(2)))
    assert sorted(r.status_code for r in results) == [200, 201]
    assert len({r.json()["id"] for r in results}) == 1
    asset_id = results[0].json()["id"]
    assert client.post(f"/api/assets/{asset_id}/analyze", headers=studio, json={}).status_code == 200
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(
            pool.map(
                lambda _: client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={}), range(2)
            )
        )
    assert all(r.status_code == 200 for r in reports)
    assert len({r.json()["id"] for r in reports}) == 1
    assert len(client.get("/api/royalties", headers=artist).json()) == 1


def test_real_audio_metadata_and_silence_measurement(tmp_path):
    path = tmp_path / "silence.wav"
    with wave.open(str(path), "wb") as sample:
        sample.setnchannels(1)
        sample.setsampwidth(2)
        sample.setframerate(16000)
        sample.writeframes(b"\0\0" * 16000)
    assert audio.probe(path)["duration_seconds"] == "1.000"
    normalized = tmp_path / "normalized.wav"
    audio.normalize(path, normalized)
    result = audio.speech_activity(normalized)
    assert result["spoken_seconds"] == "0.00"
    assert result["measurement_uncertain"]


def test_actual_demo_media_pipeline(client, artist, studio):
    """Real PDF parsing + ffprobe/FFmpeg + VAD. Explicit fixture AI, no network or fabricated calls."""
    fixture_dir = Path("fixtures")
    if not (fixture_dir / "sample-narration.wav").exists():
        pytest.skip("Generate local stock-TTS fixtures with scripts/create-demo.ps1 first.")
    license_ = client.post(
        "/api/licenses", headers=artist, json={"title": "Real media demo", "studio_id": "studio_demo"}
    ).json()
    lid = license_["id"]
    assert (
        client.post(
            f"/api/licenses/{lid}/contract",
            headers=artist,
            files={
                "file": ("sample.pdf", (fixture_dir / "sample-license.pdf").read_bytes(), "application/pdf")
            },
        ).status_code
        == 200
    )
    extracted = client.post(
        f"/api/licenses/{lid}/extract", headers=artist, json={"use_demo_fixture": True}
    ).json()
    assert extracted["terms"]["ambiguities"] == []
    assert (
        client.post(
            f"/api/licenses/{lid}/approve",
            headers=artist,
            json={
                "terms": extracted["terms"],
                "expected_version": extracted["version"],
                "note": "Reviewed bundled demo terms.",
            },
        ).status_code
        == 200
    )
    asset_id = submit(client, studio, lid, (fixture_dir / "sample-narration.wav").read_bytes()).json()["id"]
    measured = client.post(f"/api/assets/{asset_id}/analyze", headers=studio, json={"use_demo_fixture": True})
    assert measured.status_code == 200, measured.text
    result = measured.json()["result"]
    assert float(result["duration_seconds"]) > float(result["spoken_seconds"]) > 30
    assert result["provider"] == "demo_fixture (not Groq)"
    report = client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={"use_demo_fixture": True})
    assert report.status_code == 200, report.text
    assert report.json()["status"] == "ADDITIONAL_ROYALTY_DUE"
    audio_response = client.get(f"/api/assets/{asset_id}/audio", headers=artist)
    assert audio_response.status_code == 200 and audio_response.content[:4] == b"RIFF"
