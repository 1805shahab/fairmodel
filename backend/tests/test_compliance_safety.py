import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app import ai
from app.db import License, Report, UsageAuthorization, get_session
from app.eligibility import digest
from app.main import app
from app.royalties import evaluate
from app.schemas import ContentFindings
from test_royalties import campaign, measurement
from test_workflow import authorize, mock_audio, process, setup_license, submit


def edit_db(action):
    generator = app.dependency_overrides[get_session]()
    db = next(generator)
    try:
        action(db)
        db.commit()
    finally:
        generator.close()


def test_unreviewed_identity_blocks_proposal_even_when_model_disabled(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]
    report = process(client, studio, asset_id, authorize_usage=False)
    assert report["status"] == "NEEDS_REVIEW"
    assert report["result"]["provider"] == "gemini:mock-test"
    assert report["result"]["calculation"]["amount"] == "30.00"
    assert not report["result"]["eligible_for_charge"]
    assert client.get("/api/royalties", headers=artist).json() == []
    assert (
        client.post(
            f"/api/assets/{asset_id}/authorization",
            headers=studio,
            json={
                "identity_confirmed": True,
                "use_authorized": True,
                "note": "Studio cannot approve identity.",
            },
        ).status_code
        == 403
    )
    assert authorize(client, asset_id).status_code == 200
    updated = client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={}).json()
    assert updated["status"] == "ADDITIONAL_ROYALTY_DUE"
    assert updated["result"]["eligible_for_charge"]
    assert len(client.get("/api/royalties", headers=artist).json()) == 1


@pytest.mark.parametrize("speaker", [None, {"status": "disabled"}, {"status": "match"}])
def test_similarity_never_substitutes_for_authorization(terms, speaker):
    result = evaluate(
        terms, campaign(), measurement(), ContentFindings(findings=[], uncertainty=[]), speaker=speaker
    )
    assert result["status"] == "NEEDS_REVIEW"
    assert not result["eligible_for_charge"]


def test_fixture_transcription_does_not_force_fixture_compliance_or_cached_results(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]
    assert (
        client.post(
            f"/api/assets/{asset_id}/analyze", headers=studio, json={"use_demo_fixture": True}
        ).status_code
        == 200
    )
    fixture = client.post(
        f"/api/assets/{asset_id}/evaluate", headers=studio, json={"use_demo_fixture": True}
    ).json()
    assert fixture["result"]["assessment_fixture"]
    live = client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={}).json()
    assert live["id"] == fixture["id"]
    assert live["result"]["provider"] == "gemini:mock-test"
    assert not live["result"]["assessment_fixture"]
    assert live["result"]["transcription_mode"] == "fixture"
    assert live["status"] == "NEEDS_REVIEW"
    assert client.get("/api/royalties", headers=artist).json() == []
    # Explicit live transcription replaces the cached fixture instead of returning it as a success.
    live_audio = client.post(f"/api/assets/{asset_id}/analyze", headers=studio, json={}).json()
    assert not live_audio["result"]["demo_fixture"]
    assert live_audio["result"]["provider"] == "groq:mock-test"
    detail = client.get(f"/api/assets/{asset_id}", headers=studio).json()
    assert detail["report"] is None and detail["authorization"] is None


def test_failed_live_reassessment_does_not_return_a_fixture_success(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]
    client.post(f"/api/assets/{asset_id}/analyze", headers=studio, json={"use_demo_fixture": True})
    client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={"use_demo_fixture": True})

    def failed(*args, **kwargs):
        raise HTTPException(502, "Gemini denied access (provider HTTP 403). No fixture fallback was used.")

    monkeypatch.setattr(ai, "content_findings", failed)
    response = client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={})
    assert response.status_code == 502
    assert "403" in response.json()["detail"]
    saved = client.get(f"/api/assets/{asset_id}", headers=artist).json()
    assert saved["report"]["result"]["provider"] == "demo_fixture (not Gemini)"
    assert saved["error"] and client.get("/api/royalties", headers=artist).json() == []


def test_approved_snapshot_not_mutable_terms_is_used(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    original_hash = digest(license_["terms"])

    def change_draft_copy(db):
        row = db.get(License, license_["id"])
        row.terms = {**row.terms, "included_seconds": "999", "additional_rate": "0"}

    edit_db(change_draft_copy)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]
    report = process(client, studio, asset_id)
    assert report["result"]["terms_hash"] == original_hash
    assert report["result"]["calculation"]["amount"] == "30.00"
    assert (
        client.post(
            f"/api/assets/{asset_id}/evaluate", headers=studio, json={"terms": {"additional_rate": "0"}}
        ).status_code
        == 422
    )


def test_revoked_artist_review_blocks_existing_royalty_approval_and_invoice(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]
    process(client, studio, asset_id)
    royalty = client.get("/api/royalties", headers=artist).json()[0]
    assert royalty["eligible_for_charge"]
    client.post(
        f"/api/assets/{asset_id}/authorization",
        headers=artist,
        json={
            "identity_confirmed": False,
            "use_authorized": False,
            "note": "Permission is unresolved after further review.",
        },
    )
    assert not client.get("/api/royalties", headers=artist).json()[0]["eligible_for_charge"]
    assert (
        client.post(
            f"/api/royalties/{royalty['id']}/decision",
            headers=artist,
            json={"approve": True, "note": "Try to bypass identity gate."},
        ).status_code
        == 409
    )
    assert client.post(f"/api/royalties/{royalty['id']}/invoice", headers=artist).status_code == 409


def test_legacy_cached_report_requires_current_safety_review(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]
    process(client, studio, asset_id)

    def legacy(db):
        report = db.scalar(select(Report).where(Report.asset_id == asset_id))
        report.result = {
            key: value for key, value in report.result.items() if key not in {"policy_version", "input_hash"}
        }
        review = db.scalar(select(UsageAuthorization).where(UsageAuthorization.asset_id == asset_id))
        db.delete(review)

    edit_db(legacy)
    reevaluated = client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={}).json()
    assert reevaluated["status"] == "NEEDS_REVIEW"
    from app.eligibility import POLICY_VERSION

    assert reevaluated["result"]["policy_version"] == POLICY_VERSION
    assert not client.get("/api/royalties", headers=artist).json()[0]["eligible_for_charge"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("region", "CA"),
        ("medium", "television"),
        ("intended_use_date", "2025-01-01"),
        ("intended_use_date", "2028-01-01"),
        ("category", "political advertising"),
    ],
)
def test_scope_restrictions_still_block_after_manual_authorization(
    client, artist, studio, monkeypatch, terms, field, value
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"], **{field: value}).json()["id"]
    report = process(client, studio, asset_id)
    assert report["status"] == "RESTRICTED_USAGE"
    assert client.get("/api/royalties", headers=artist).json() == []


@pytest.mark.parametrize("seconds", ["NaN", "Infinity", "-1", "51"])
def test_invalid_spoken_duration_holds_financial_result(terms, seconds):
    result = evaluate(
        terms,
        campaign(),
        {**measurement(seconds), "duration_seconds": "50"},
        ContentFindings(findings=[], uncertainty=[]),
        authorization={"identity_confirmed": True, "use_authorized": True},
    )
    assert result["status"] == "NEEDS_REVIEW"
    assert result["calculation"] is None


@pytest.mark.parametrize(
    "seconds,status,amount", [("20", "COMPLIANT", "0.00"), ("45", "ADDITIONAL_ROYALTY_DUE", "30.00")]
)
def test_authorized_measured_usage_uses_approved_decimal_rules(terms, seconds, status, amount):
    result = evaluate(
        terms,
        campaign(),
        {**measurement(seconds), "duration_seconds": "80"},
        ContentFindings(findings=[], uncertainty=[]),
        authorization={"identity_confirmed": True, "use_authorized": True},
    )
    assert result["status"] == status and result["eligible_for_charge"]
    assert result["calculation"]["amount"] == amount
    assert result["calculation"]["spoken_seconds"] == seconds


@pytest.mark.parametrize("uncertainty", ["contract", "content", "region", "measurement", "category"])
def test_uncertainty_blocks_even_after_identity_and_use_confirmed(terms, uncertainty):
    metadata, measured = campaign(), measurement()
    findings = ContentFindings(findings=[], uncertainty=[])
    if uncertainty == "contract":
        terms.ambiguities = ["Duration allowance is ambiguous."]
    elif uncertainty == "content":
        findings.uncertainty = ["Possible restricted campaign; human review required."]
    elif uncertainty == "region":
        metadata.region = None
    elif uncertainty == "category":
        metadata.category = None
    else:
        measured["measurement_uncertain"] = True
    result = evaluate(
        terms,
        metadata,
        measured,
        findings,
        authorization={"identity_confirmed": True, "use_authorized": True},
    )
    assert result["status"] == "NEEDS_REVIEW" and not result["eligible_for_charge"]


def test_failed_reassessment_holds_prior_charge_and_retry_calls_provider(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]
    process(client, studio, asset_id)
    original = ai.content_findings

    def failed(*args, **kwargs):
        raise HTTPException(
            502, "Gemini reported a rate limit (provider HTTP 429). No fixture fallback was used."
        )

    monkeypatch.setattr(ai, "content_findings", failed)
    assert (
        client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={"reprocess": True}).status_code
        == 502
    )
    held = client.get("/api/royalties", headers=artist).json()[0]
    assert not held["eligible_for_charge"]
    assert (
        client.post(
            f"/api/royalties/{held['id']}/decision",
            headers=artist,
            json={"approve": True, "note": "Should remain on hold."},
        ).status_code
        == 409
    )
    monkeypatch.setattr(ai, "content_findings", original)
    retried = client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={}).json()
    assert retried["status"] == "ADDITIONAL_ROYALTY_DUE"
    assert client.get("/api/royalties", headers=artist).json()[0]["eligible_for_charge"]


def test_campaign_changes_require_new_artist_review(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset_id = submit(client, studio, license_["id"]).json()["id"]
    process(client, studio, asset_id, authorize_usage=False)
    authorize(client, asset_id)
    before = client.get(f"/api/assets/{asset_id}", headers=artist).json()
    changed = {**before["campaign"], "name": "Different campaign"}
    assert client.patch(f"/api/assets/{asset_id}/campaign", headers=studio, json=changed).status_code == 200
    after = client.get(f"/api/assets/{asset_id}", headers=artist).json()
    assert after["authorization"]["status"] == "unresolved" and after["report"] is None
    result = client.post(f"/api/assets/{asset_id}/evaluate", headers=studio, json={}).json()
    assert result["status"] == "NEEDS_REVIEW"
    assert client.get("/api/royalties", headers=artist).json() == []


def test_schema_one_upgrade_adds_review_table_without_losing_existing_records(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.orm import Session
    from app import main
    from app.db import Base, Persona

    previous = create_engine(
        "sqlite:///" + (tmp_path / "upgrade.db").as_posix(), connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(
        previous,
        tables=[table for table in Base.metadata.sorted_tables if table.name != "usage_authorizations"],
    )
    with previous.begin() as connection:
        connection.exec_driver_sql("PRAGMA user_version=1")
    with Session(previous) as db:
        db.add(
            Persona(id="existing_artist", role="artist", name="Existing owner", email="existing@example.test")
        )
        db.commit()
    monkeypatch.setattr(main, "engine", previous)
    with TestClient(main.app):
        assert "usage_authorizations" in inspect(previous).get_table_names()
        with previous.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA user_version").scalar() == main.SCHEMA_VERSION
        with Session(previous) as db:
            assert db.get(Persona, "existing_artist").name == "Existing owner"
    previous.dispose()
