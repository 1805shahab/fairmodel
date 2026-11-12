import sqlite3

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import (
    Analysis,
    Asset,
    Audit,
    Base,
    CaseEvent,
    EvidenceRevision,
    Invoice,
    License,
    Persona,
    Royalty,
    UsageCase,
    get_session,
)
from app.main import app
from app.migrations import migrate, SCHEMA_VERSION
from test_workflow import setup_license, mock_audio, submit, process
from test_compliance_safety import edit_db


def prepared(client, artist, studio, monkeypatch, terms, seconds="45"):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch, seconds)
    asset = submit(client, studio, license_["id"]).json()["id"]
    process(client, studio, asset)
    return license_, asset


def counts():
    generator = app.dependency_overrides[get_session]()
    db = next(generator)
    try:
        return {
            m.__tablename__: len(list(db.scalars(select(m))))
            for m in (Asset, Royalty, Invoice, Audit, EvidenceRevision, UsageCase, CaseEvent)
        }
    finally:
        generator.close()


def open_case(client, artist, asset, **changes):
    return client.post(
        f"/api/assets/{asset}/review-cases",
        headers=artist,
        json={
            "request_key": "review-first-0001",
            "decision": "INVESTIGATE",
            "category": "royalty",
            "note": "Please investigate this allocation before any further invoice action.",
            **changes,
        },
    )


def test_passport_is_private_stable_read_only_and_bound_to_approved_version(
    client, artist, studio, monkeypatch, terms
):
    license_, asset = prepared(client, artist, studio, monkeypatch, terms)
    before = counts()
    a = client.get(f"/api/assets/{asset}/passport", headers=artist)
    b = client.get(f"/api/assets/{asset}/passport", headers=studio)
    assert a.status_code == b.status_code == 200
    p = a.json()
    assert p["id"] == b.json()["id"] == "VP-" + asset.upper()
    assert p["license"]["version"] == license_["version"]
    assert p["asset"]["authorization"]["status"] == "artist_confirmed"
    assert p["asset"]["royalty"]["amount"] == "30.00"
    assert p["private"] and "not a legal certificate" in p["disclaimer"]
    assert "not an acoustic fingerprint" in p["audio_evidence"]["hash_note"]
    assert p["license"]["source_review"]["citations"] and counts() == before
    assert "path" not in p["asset"]
    assert client.get(f"/api/assets/{asset}/passport").status_code == 401
    edit_db(
        lambda db: db.add(Persona(id="unrelated", role="artist", name="Other", email="other@example.test"))
    )
    assert (
        client.get(f"/api/assets/{asset}/passport", headers={"X-Demo-Persona": "unrelated"}).status_code
        == 404
    )
    edit_db(lambda db: setattr(db.get(License, license_["id"]), "version", 99))
    assert (
        client.get(f"/api/assets/{asset}/passport", headers=artist).json()["license"]["version"]
        == license_["version"]
    )


def test_history_survives_failed_reassessment_and_repeated_reads(client, artist, studio, monkeypatch, terms):
    from fastapi import HTTPException
    from app import ai

    _, asset = prepared(client, artist, studio, monkeypatch, terms)
    original = client.get(f"/api/assets/{asset}/passport", headers=artist).json()
    assert {r["kind"] for r in original["history"]} == {"analysis", "compliance", "authorization"}

    def failed(*args, **kwargs):
        raise HTTPException(502, "Gemini test network failure; no fixture fallback.")

    monkeypatch.setattr(ai, "content_findings", failed)
    assert (
        client.post(f"/api/assets/{asset}/evaluate", headers=studio, json={"reprocess": True}).status_code
        == 502
    )
    latest = client.get(f"/api/assets/{asset}/passport", headers=artist).json()
    assert latest["asset"]["report"]["result"]["latest_attempt_failed"]
    assert any(r["snapshot"].get("status") == "ADDITIONAL_ROYALTY_DUE" for r in latest["history"])
    assert latest["asset"]["royalty"]["amount"] == "30.00"
    before = counts()
    client.get(f"/api/assets/{asset}/passport", headers=artist)
    assert counts() == before


def test_mock_paid_passport_never_claims_actual_sandbox_payment(client, artist, studio, monkeypatch, terms):
    _, asset = prepared(client, artist, studio, monkeypatch, terms)
    royalty = client.get(f"/api/assets/{asset}", headers=artist).json()["royalty"]["id"]
    client.post(
        f"/api/royalties/{royalty}/decision",
        headers=artist,
        json={"approve": True, "note": "Reviewed the approved financial evidence."},
    )
    invoice = client.post(f"/api/royalties/{royalty}/invoice", headers=artist).json()
    client.post(
        f"/api/invoices/{invoice['id']}/send", headers=artist, json={"event_key": "test-passport-send"}
    )
    client.post(
        f"/api/invoices/{invoice['id']}/simulate-payment",
        headers=studio,
        json={"event_key": "test-passport-paid"},
    )
    p = client.get(f"/api/assets/{asset}/passport", headers=artist).json()
    assert p["asset"]["invoice"]["provider"] == "mock"
    assert p["asset"]["invoice"]["provider_id"].startswith("SIMULATED-")
    assert "NO REAL FUNDS" in p["asset"]["invoice"]["notice"]
    assert p["stages"][-1]["state"] == "simulated"


def test_artist_dispute_blocks_charge_and_send_preserves_financial_history(
    client, artist, studio, monkeypatch, terms
):
    _, asset = prepared(client, artist, studio, monkeypatch, terms)
    royalty = client.get(f"/api/assets/{asset}", headers=artist).json()["royalty"]["id"]
    client.post(
        f"/api/royalties/{royalty}/decision",
        headers=artist,
        json={"approve": True, "note": "Reviewed before the later dispute."},
    )
    invoice = client.post(f"/api/royalties/{royalty}/invoice", headers=artist).json()
    case = open_case(client, artist, asset)
    assert case.status_code == 201
    before = counts()
    assert open_case(client, artist, asset).json()["id"] == case.json()["id"]
    assert counts() == before
    assert (
        client.post(
            f"/api/invoices/{invoice['id']}/send", headers=artist, json={"event_key": "blocked-case-send"}
        ).status_code
        == 409
    )
    assert client.get(f"/api/invoices/{invoice['id']}", headers=artist).json()["amount"] == invoice["amount"]
    assert client.get(f"/api/assets/{asset}", headers=studio).json()["compliance_state"] == "NEEDS_REVIEW"
    report = client.post(f"/api/assets/{asset}/evaluate", headers=studio, json={}).json()
    assert report["status"] == "NEEDS_REVIEW" and not report["result"]["eligible_for_charge"]
    assert (
        client.post(
            f"/api/review-cases/{case.json()['id']}/events",
            headers=studio,
            json={
                "request_key": "resolve-invalid-01",
                "kind": "RESOLVE",
                "note": "Studio must not resolve artist concerns.",
            },
        ).status_code
        == 403
    )
    response = {
        "request_key": "studio-response-01",
        "kind": "RESPONSE",
        "note": "Studio supplied the requested campaign explanation.",
    }
    assert (
        client.post(
            f"/api/review-cases/{case.json()['id']}/events", headers=studio, json=response
        ).status_code
        == 200
    )
    resolution = {
        "request_key": "artist-resolution-01",
        "kind": "RESOLVE",
        "note": "Artist reviewed the response and resolved this concern.",
    }
    resolved = client.post(f"/api/review-cases/{case.json()['id']}/events", headers=artist, json=resolution)
    assert resolved.status_code == 200 and resolved.json()["status"] == "RESOLVED"
    assert (
        client.post(f"/api/review-cases/{case.json()['id']}/events", headers=artist, json=resolution).json()[
            "events"
        ]
        == resolved.json()["events"]
    )
    assert (
        client.post(
            f"/api/invoices/{invoice['id']}/send", headers=artist, json={"event_key": "still-stale-approval"}
        ).status_code
        == 409
    )
    assert (
        client.post(f"/api/assets/{asset}/evaluate", headers=studio, json={}).json()["status"]
        == "ADDITIONAL_ROYALTY_DUE"
    )
    assert not client.get(f"/api/assets/{asset}", headers=artist).json()["royalty"]["approval_current"]
    assert counts()["invoices"] == 1


def test_review_permissions_missing_evidence_and_changed_inputs(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset = submit(client, studio, license_["id"]).json()["id"]
    assert open_case(client, studio, asset).status_code == 403
    assert open_case(client, artist, asset, evidence_refs=["unrelated-private-id"]).status_code == 422
    case = open_case(client, artist, asset, decision="APPROVE_USAGE").json()
    assert case["status"] == "RESOLVED"
    process(client, studio, asset)
    p = client.get(f"/api/assets/{asset}/passport", headers=artist).json()
    assert p["cases"][0]["status"] == "STALE_REVIEW"
    assert not p["asset"]["report"]["result"]["eligible_for_charge"]
    assert "history" in p and "source_review" in p["license"]


@pytest.mark.parametrize(
    "seconds,amount", [("20", "0.00"), ("30", "0.00"), ("45", "30.00"), ("58.77", "57.54")]
)
def test_estimator_uses_decimal_without_creating_records(
    client, artist, studio, monkeypatch, terms, seconds, amount
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    before = counts()
    payload = {
        "spoken_seconds": seconds,
        "campaign": {
            "name": "Launch",
            "medium": "online commercial advertisements",
            "region": "US",
            "language": "English",
            "category": "consumer products",
            "intended_use_date": "2026-11-06",
        },
    }
    response = client.post(f"/api/licenses/{license_['id']}/estimate", headers=studio, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["estimate_only"] and response.json()["calculation"]["amount"] == amount
    assert response.json()["scope_status"] == "SCOPE_APPEARS_PERMITTED"
    assert not any("receipts verify" in check["explanation"] for check in response.json()["checks"])
    assert counts() == before
    assert (
        client.post(f"/api/licenses/{license_['id']}/estimate", headers=artist, json=payload).status_code
        == 403
    )
    payload["campaign"]["medium"] = "television"
    restricted = client.post(f"/api/licenses/{license_['id']}/estimate", headers=studio, json=payload).json()
    assert restricted["scope_status"] == "RESTRICTED_USAGE" and restricted["calculation"] is None
    payload["spoken_seconds"] = "NaN"
    assert (
        client.post(f"/api/licenses/{license_['id']}/estimate", headers=studio, json=payload).status_code
        == 422
    )


def test_v5_migration_backfills_current_evidence_only_and_preserves_rows(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path / "upgrade.db").as_posix())
    Base.metadata.create_all(
        engine,
        tables=[
            t
            for t in Base.metadata.sorted_tables
            if t.name not in {"evidence_revisions", "usage_cases", "usage_case_events"}
        ],
    )
    with Session(engine) as db:
        db.add_all(
            [
                Persona(id="artist", role="artist", name="Owner", email="a@example.test"),
                Persona(id="studio", role="studio", name="Studio", email="s@example.test"),
            ]
        )
        db.flush()
        db.add(License(id="license", artist_id="artist", studio_id="studio", title="Preserve", terms={}))
        db.flush()
        db.add(
            Asset(
                id="asset",
                license_id="license",
                studio_id="studio",
                license_version=4,
                campaign={},
                original_name="private.wav",
                path="private/path",
                file_hash="originalhash",
            )
        )
        db.flush()
        db.add(Analysis(asset_id="asset", result={"transcript": "Persisted original text"}))
        db.commit()
    with engine.begin() as c:
        c.exec_driver_sql("PRAGMA user_version=4")
    backup = migrate(engine)
    assert backup and backup.is_file()
    with sqlite3.connect(backup) as c:
        assert c.execute("PRAGMA user_version").fetchone()[0] == 4
    with Session(engine) as db:
        revision = db.scalar(select(EvidenceRevision))
        assert revision.origin == "migration_current_only"
        assert revision.snapshot["result"]["transcript"] == "Persisted original text"
        assert db.get(Asset, "asset").file_hash == "originalhash"
    assert migrate(engine) is None and SCHEMA_VERSION == 7
    engine.dispose()


def test_usage_review_does_not_fabricate_identity_attestation(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset = submit(client, studio, license_["id"]).json()["id"]
    client.post(f"/api/assets/{asset}/analyze", headers=studio, json={})
    assert open_case(client, artist, asset, decision="APPROVE_USAGE").status_code == 201
    report = client.post(f"/api/assets/{asset}/evaluate", headers=studio, json={}).json()
    assert report["status"] == "NEEDS_REVIEW"
    assert (
        client.get(f"/api/assets/{asset}/passport", headers=artist).json()["asset"]["authorization"] is None
    )
    assert client.get("/api/royalties", headers=artist).json() == []


def test_dispute_on_same_usage_edit_blocks_canonical_charge(client, artist, studio, monkeypatch, terms):
    from test_overlap_resolution import make_pair, decide

    _, original, edited = make_pair(client, artist, studio, monkeypatch, terms, allocate_first=True)
    assert decide(client, artist, edited, original).status_code == 200
    assert open_case(client, artist, edited).status_code == 201
    royalty = client.get(f"/api/assets/{original}", headers=artist).json()["royalty"]
    assert not royalty["eligible_for_charge"]
    assert (
        client.post(
            f"/api/royalties/{royalty['id']}/decision",
            headers=artist,
            json={"approve": True, "note": "Must be held by the linked edited recording concern."},
        ).status_code
        == 409
    )


def test_campaign_correction_retains_previous_compliance_snapshot(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset = submit(client, studio, license_["id"]).json()["id"]
    client.post(f"/api/assets/{asset}/analyze", headers=studio, json={})
    old = client.post(f"/api/assets/{asset}/evaluate", headers=studio, json={}).json()
    detail = client.get(f"/api/assets/{asset}", headers=studio).json()
    corrected = client.patch(
        f"/api/assets/{asset}/campaign",
        headers=studio,
        json={**detail["campaign"], "name": "Revised campaign metadata"},
    )
    assert corrected.status_code == 200
    p = client.get(f"/api/assets/{asset}/passport", headers=artist).json()
    assert p["asset"]["report"] is None
    assert any(row["snapshot"]["id"] == old["id"] for row in p["history"] if row["kind"] == "compliance")


def test_receipt_based_provenance_never_promotes_configured_model_names_to_live():
    from app.passports import provenance

    assert provenance({"provider": "groq:configured-only"}, {"provider": "gemini:configured-only"}) == {
        "transcription": "unverified",
        "compliance": "unverified",
    }
    receipt = {"mode": "live", "succeeded_at": "2026-11-11T00:00:00Z"}
    assert provenance(
        {"provider": "groq:verified", "provider_receipt": receipt},
        {"provider": "gemini:verified", "provider_receipt": receipt},
    ) == {"transcription": "live", "compliance": "live"}
    assert provenance(
        {"demo_fixture": True, "provider_receipt": receipt},
        {"assessment_fixture": True, "provider_receipt": receipt},
    ) == {"transcription": "fixture", "compliance": "fixture"}
