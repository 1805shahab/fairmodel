from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import sqlite3
import pytest
from sqlalchemy import select, create_engine, inspect
from sqlalchemy.orm import Session
from app import ai, audio
from app.db import (
    Base,
    Persona,
    Analysis,
    Asset,
    OverlapReview,
    UsageAuthorization,
    get_session,
)
from app.evidence import evidence_hash
from app.main import app
from app.migrations import migrate
from app.royalties import calculate
from test_workflow import setup_license, mock_audio, submit, authorize, process

WORDS = "These original campaign words describe a thoughtful collection of useful products made for everyday customers who enjoy practical and carefully designed objects."


def make_pair(
    client,
    artist,
    studio,
    monkeypatch,
    terms,
    first_seconds="45",
    second_seconds="23.52",
    allocate_first=False,
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch, first_seconds)
    monkeypatch.setattr(
        ai, "transcribe", lambda *args: {"transcript": WORDS, "timestamps": [], "provider": "groq:mock-test"}
    )
    first = submit(client, studio, license_["id"], content=b"original recording").json()["id"]
    if allocate_first:
        assert process(client, studio, first)["status"] in {"COMPLIANT", "ADDITIONAL_ROYALTY_DUE"}
    else:
        assert client.post(f"/api/assets/{first}/analyze", headers=studio, json={}).status_code == 200
    monkeypatch.setattr(
        audio,
        "speech_activity",
        lambda path: {
            "spoken_seconds": second_seconds,
            "speech_segments": [],
            "measurement_uncertain": False,
            "vad": "test mock",
            "measurement_note": "test mock",
        },
    )
    second = submit(client, studio, license_["id"], content=b"edited recording").json()["id"]
    assert process(client, studio, second)["status"] == "NEEDS_REVIEW"
    return license_, first, second


def decide(
    client,
    artist,
    asset,
    related,
    decision="SAME_USAGE",
    note="Artist compared both recordings and reviewed the usage evidence.",
):
    detail = client.get(f"/api/assets/{asset}/overlap", headers=artist).json()
    pair = next((pair for pair in detail["pairs"] if pair["related"]["id"] == related), None)
    current = pair["review"]["id"] if pair and pair["review"] else None
    return client.post(
        f"/api/assets/{asset}/overlap",
        headers=artist,
        json={"related_asset_id": related, "decision": decision, "note": note, "expected_review_id": current},
    )


def evaluate(client, actor, asset):
    response = client.post(f"/api/assets/{asset}/evaluate", headers=actor, json={})
    assert response.status_code == 200, response.text
    return response.json()["result"]


def test_same_usage_links_canonical_and_allocates_once(client, artist, studio, monkeypatch, terms):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    before = client.get(f"/api/assets/{second}", headers=artist).json()["authorization"]
    saved = decide(client, artist, second, first)
    assert saved.status_code == 200, saved.text
    assert saved.json()["evaluation_refreshed"]
    assert client.get(f"/api/assets/{second}", headers=artist).json()["report"]["status"] == "COMPLIANT"
    assert saved.json()["usage"]["canonical_asset_id"] == first
    result = evaluate(client, artist, second)
    assert result["status"] == "COMPLIANT" and result["billing_usage"]["disposition"] == "SAME_USAGE"
    assert not result["eligible_for_charge"]
    assert result["assessment_reused"]
    assert client.get(f"/api/assets/{second}", headers=artist).json()["royalty"] is None
    assert (
        client.get(f"/api/assets/{second}", headers=artist).json()["authorization"]["updated_at"]
        == before["updated_at"]
    )
    assert authorize(client, first).status_code == 200
    original = evaluate(client, artist, first)
    assert original["status"] == "ADDITIONAL_ROYALTY_DUE" and original["calculation"]["amount"] == "30.00"
    assert len(client.get("/api/royalties", headers=artist).json()) == 1
    assert evaluate(client, studio, second)["status"] == "COMPLIANT"


@pytest.mark.parametrize("basis,expected", [("per_asset", "0.00"), ("cumulative", "20.00")])
def test_separate_usage_respects_billing_basis(client, artist, studio, monkeypatch, terms, basis, expected):
    terms.billing_basis = basis
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms, "20", "20", allocate_first=True)
    assert decide(client, artist, second, first, "SEPARATE_USAGE").status_code == 200
    result = evaluate(client, studio, second)
    assert result["calculation"]["amount"] == expected
    assert result["status"] == ("COMPLIANT" if expected == "0.00" else "ADDITIONAL_ROYALTY_DUE")
    assert len(client.get("/api/royalties", headers=artist).json()) == 2


def test_uncertain_holds_and_history_is_append_only_idempotent(client, artist, studio, monkeypatch, terms):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    saved = decide(client, artist, second, first, "UNCERTAIN").json()
    assert evaluate(client, artist, second)["status"] == "NEEDS_REVIEW"
    repeat = decide(client, artist, second, first, "UNCERTAIN").json()
    assert repeat["review"]["id"] == saved["review"]["id"] and not repeat["created"]
    changed = decide(client, artist, second, first, "SEPARATE_USAGE").json()
    assert changed["review"]["previous_id"] == saved["review"]["id"]
    pair = changed["pairs"][0]
    assert len(pair["history"]) == 2
    assert pair["history"][0]["reviewer_id"] == artist["X-Demo-Persona"]
    assert pair["current"]["duration_seconds"] and pair["related"]["spoken_seconds"]
    assert pair["evidence"]["current_excerpt"] in WORDS
    assert pair["evidence"]["related_excerpt"] in WORDS
    assert evaluate(client, artist, second)["status"] == "COMPLIANT"


def test_studio_cannot_review_and_cross_license_cycles_rejected(client, artist, studio, monkeypatch, terms):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    body = {"related_asset_id": first, "decision": "SAME_USAGE", "note": "Studio must not act as the artist."}
    assert client.post(f"/api/assets/{second}/overlap", headers=studio, json=body).status_code == 403
    assert (
        client.post(
            f"/api/assets/{first}/overlap", headers=artist, json={**body, "related_asset_id": second}
        ).status_code
        == 409
    )
    assert client.post(f"/api/assets/{first}/overlap", headers=artist, json=body).status_code == 409
    other = setup_license(client, artist, monkeypatch, terms)
    third = submit(client, studio, other["id"], content=b"other license").json()["id"]
    assert client.post(f"/api/assets/{third}/analyze", headers=studio, json={}).status_code == 200
    assert decide(client, artist, third, first).status_code == 409


def test_transitive_same_separate_contradiction_is_rejected(client, artist, studio, monkeypatch, terms):
    license_, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    assert decide(client, artist, second, first, "SEPARATE_USAGE").status_code == 200
    third = submit(client, studio, license_["id"], content=b"third edit").json()["id"]
    assert client.post(f"/api/assets/{third}/analyze", headers=studio, json={}).status_code == 200
    assert decide(client, artist, third, first).status_code == 200
    rejected = decide(client, artist, third, second)
    assert rejected.status_code == 409 and "contradicts" in rejected.json()["detail"]


def test_changed_metadata_invalidates_both_pair_and_attestation_without_deleting_them(
    client, artist, studio, monkeypatch, terms
):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    saved = decide(client, artist, second, first).json()["review"]
    asset = client.get(f"/api/assets/{second}", headers=studio).json()
    assert (
        client.patch(f"/api/assets/{second}/campaign", headers=studio, json=asset["campaign"]).status_code
        == 200
    )
    assert (
        client.get(f"/api/assets/{second}/overlap", headers=artist).json()["pairs"][0]["review"]["state"]
        == "current"
    )
    assert (
        client.patch(
            f"/api/assets/{second}/campaign",
            headers=studio,
            json={**asset["campaign"], "name": "Updated authorized campaign"},
        ).status_code
        == 200
    )
    after = client.get(f"/api/assets/{second}", headers=artist).json()
    assert (
        after["authorization"]["id"] == asset["authorization"]["id"]
        and after["authorization_state"] == "unresolved"
    )
    pair = client.get(f"/api/assets/{second}/overlap", headers=artist).json()["pairs"][0]
    assert pair["review"]["id"] == saved["id"] and pair["review"]["state"] == "stale"
    assert evaluate(client, artist, second)["status"] == "NEEDS_REVIEW"
    assert decide(client, artist, second, first).json()["review"]["previous_id"] == saved["id"]


def test_unchanged_reanalysis_receipts_and_repeat_authorization_do_not_invalidate(
    client, artist, studio, monkeypatch, terms
):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    saved = decide(client, artist, second, first).json()["review"]
    result = evaluate(client, artist, second)
    before = client.get(f"/api/assets/{second}", headers=artist).json()
    assert authorize(client, second).json()["updated_at"] == before["authorization"]["updated_at"]
    monkeypatch.setattr(
        ai,
        "transcribe",
        lambda *args: {
            "transcript": WORDS,
            "timestamps": [],
            "provider": "groq:mock-test",
            "provider_receipt": {"response_id": "a different real-response receipt", "succeeded_at": "later"},
        },
    )
    assert (
        client.post(f"/api/assets/{second}/analyze", headers=studio, json={"reprocess": True}).status_code
        == 200
    )
    after = client.get(f"/api/assets/{second}", headers=artist).json()
    assert after["authorization_state"] == "artist_confirmed"
    assert after["report"]["result"]["input_hash"] == result["input_hash"]
    assert (
        client.get(f"/api/assets/{second}/overlap", headers=artist).json()["pairs"][0]["review"]["id"]
        == saved["id"]
    )
    assert evaluate(client, artist, second)["status"] == "COMPLIANT"


def test_existing_conflicting_invoices_preserved_and_both_held(client, artist, studio, monkeypatch, terms):
    license_, first, second = make_pair(
        client, artist, studio, monkeypatch, terms, second_seconds="45", allocate_first=True
    )
    assert decide(client, artist, second, first, "SEPARATE_USAGE").status_code == 200
    evaluate(client, artist, second)
    evaluate(client, artist, first)
    entries = client.get("/api/royalties", headers=artist).json()
    invoices = []
    for royalty in entries:
        assert (
            client.post(
                f"/api/royalties/{royalty['id']}/decision",
                headers=artist,
                json={"approve": True, "note": "Artist approved independently licensed usage."},
            ).status_code
            == 200
        )
        invoices.append(client.post(f"/api/royalties/{royalty['id']}/invoice", headers=artist).json())
    assert decide(client, artist, second, first).json()["usage"]["reconciliation_required"]
    assert evaluate(client, artist, second)["status"] == "NEEDS_REVIEW"
    assert evaluate(client, artist, first)["status"] == "NEEDS_REVIEW"
    history = client.get("/api/invoices", headers=artist).json()
    assert {(r["id"], r["amount"], r["status"]) for r in history} == {
        (r["id"], r["amount"], r["status"]) for r in invoices
    }
    assert len(client.get("/api/royalties", headers=artist).json()) == 2
    for royalty in entries:
        assert client.post(f"/api/royalties/{royalty['id']}/invoice", headers=artist).status_code == 409
    assert (
        client.post(
            f"/api/invoices/{invoices[0]['id']}/send", headers=artist, json={"event_key": "held_invoice_send"}
        ).status_code
        == 409
    )


def test_stale_charge_approval_requires_fresh_explicit_approval(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset = submit(client, studio, license_["id"]).json()["id"]
    process(client, studio, asset)
    royalty = client.get("/api/royalties", headers=artist).json()[0]
    url = f"/api/royalties/{royalty['id']}"
    assert (
        client.post(
            url + "/decision",
            headers=artist,
            json={"approve": True, "note": "Initial reviewed financial decision."},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/assets/{asset}/authorization",
            headers=artist,
            json={
                "identity_confirmed": False,
                "use_authorized": False,
                "note": "Revoke while identity evidence is reconsidered.",
            },
        ).status_code
        == 200
    )
    authorize(client, asset)
    evaluate(client, artist, asset)
    assert not client.get("/api/royalties", headers=artist).json()[0]["approval_current"]
    assert client.post(url + "/invoice", headers=artist).status_code == 409
    renewed = client.post(
        url + "/decision",
        headers=artist,
        json={"approve": True, "note": "Fresh approval after new artist attestation."},
    )
    assert renewed.status_code == 200 and renewed.json()["approval_current"]
    a = client.post(url + "/invoice", headers=artist)
    b = client.post(url + "/invoice", headers=artist)
    assert a.status_code == b.status_code == 201 and a.json()["id"] == b.json()["id"]
    detail = client.get(f"/api/assets/{asset}", headers=artist).json()
    assert detail["workflow_stage"] == "INVOICE_DRAFT" and "simulate sending" in detail["next_action"]
    assert detail["processing_state"] == "ANALYZED" and detail["compliance_state"] == "ADDITIONAL_ROYALTY_DUE"


@pytest.mark.parametrize(
    "seconds,amount", [("20", "0.00"), ("23.52", "0.00"), ("30", "0.00"), ("45", "30.00"), ("58.77", "57.54")]
)
def test_required_financial_examples(terms, seconds, amount):
    assert calculate(terms, Decimal(seconds))["amount"] == amount


@pytest.mark.parametrize("rate", ["-1", "NaN", "Infinity"])
def test_invalid_mutated_financial_terms_rejected(terms, rate):
    terms.additional_rate = Decimal(rate)
    with pytest.raises(ValueError):
        calculate(terms, Decimal("45"))


def test_schema_two_backup_and_additive_migration_preserve_records(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path / "existing.db").as_posix())
    Base.metadata.create_all(
        engine,
        tables=[
            t for t in Base.metadata.sorted_tables if t.name not in {"overlap_reviews", "royalty_approvals"}
        ],
    )
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA user_version=2")
    with Session(engine) as db:
        db.add(Persona(id="existing_owner", role="artist", name="Preserved", email="preserved@example.test"))
        db.commit()
    backup = migrate(engine)
    assert backup and backup.is_file()
    assert {"overlap_reviews", "royalty_approvals"}.issubset(inspect(engine).get_table_names())
    with sqlite3.connect(str(backup)) as before:
        assert before.execute("PRAGMA user_version").fetchone()[0] == 2
        assert (
            before.execute("SELECT name FROM personas WHERE id='existing_owner'").fetchone()[0] == "Preserved"
        )
    with Session(engine) as after:
        assert after.get(Persona, "existing_owner").name == "Preserved"
    assert migrate(engine) is None
    engine.dispose()


def test_concurrent_identical_review_requests_create_one_history_record(
    client, artist, studio, monkeypatch, terms
):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    body = {
        "related_asset_id": first,
        "decision": "SAME_USAGE",
        "note": "The artist reviewed the same edited licensed usage.",
        "expected_review_id": None,
    }
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda _: client.post(f"/api/assets/{second}/overlap", headers=artist, json=body), range(2)
            )
        )
    assert all(response.status_code == 200 for response in responses)
    assert len({response.json()["review"]["id"] for response in responses}) == 1
    assert sum(response.json()["created"] for response in responses) == 1
    assert len(client.get(f"/api/assets/{second}/overlap", headers=artist).json()["pairs"][0]["history"]) == 1


def test_changed_transcript_invalidates_pair_and_new_decision_stays_recorded(
    client, artist, studio, monkeypatch, terms
):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    original = decide(client, artist, second, first).json()["review"]
    evaluate(client, artist, second)
    monkeypatch.setattr(
        ai,
        "transcribe",
        lambda *args: {
            "transcript": WORDS + " Additional changed dialogue.",
            "timestamps": [],
            "provider": "groq:mock-test",
        },
    )
    assert (
        client.post(f"/api/assets/{second}/analyze", headers=studio, json={"reprocess": True}).status_code
        == 200
    )
    state = client.get(f"/api/assets/{second}/overlap", headers=artist).json()
    assert state["pairs"][0]["review"]["state"] == "stale"
    assert state["usage"]["unresolved"]
    assert evaluate(client, artist, second)["status"] == "NEEDS_REVIEW"
    updated = decide(client, artist, second, first).json()["review"]
    assert updated["previous_id"] == original["id"]
    # Persisted rows survive a fresh database session; the review is not frontend state.
    authorization_id = client.get(f"/api/assets/{second}", headers=artist).json()["authorization"]["id"]
    generator = app.dependency_overrides[get_session]()
    db = next(generator)
    try:
        assert (
            db.get(OverlapReview, original["id"]).evidence_hash
            != db.get(OverlapReview, updated["id"]).evidence_hash
        )
        asset = db.get(Asset, second)
        analysis = db.scalar(select(Analysis).where(Analysis.asset_id == second))
        assert db.get(
            UsageAuthorization,
            authorization_id,
        ).evidence_hash != evidence_hash(asset, analysis)
    finally:
        generator.close()


def test_longer_edit_requires_reconciliation_instead_of_silently_underbilling(
    client, artist, studio, monkeypatch, terms
):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms, "20", "45")
    assert decide(client, artist, second, first).json()["usage"]["reconciliation_required"]
    assert evaluate(client, artist, second)["status"] == "NEEDS_REVIEW"
    assert client.get("/api/royalties", headers=artist).json() == []


def test_unrelated_restriction_survives_overlap_resolution(client, artist, studio, monkeypatch, terms):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    data = client.get(f"/api/assets/{second}", headers=studio).json()
    assert (
        client.patch(
            f"/api/assets/{second}/campaign",
            headers=studio,
            json={**data["campaign"], "medium": "television"},
        ).status_code
        == 200
    )
    assert decide(client, artist, second, first, "SEPARATE_USAGE").status_code == 200
    authorize(client, second)
    result = evaluate(client, artist, second)
    assert result["status"] == "RESTRICTED_USAGE"
    assert not result["billing_usage"]["unresolved"]
    assert client.get("/api/royalties", headers=artist).json() == []


def test_cumulative_same_usage_reserves_allowance_only_once(client, artist, studio, monkeypatch, terms):
    terms.billing_basis = "cumulative"
    license_, first, second = make_pair(
        client, artist, studio, monkeypatch, terms, "20", "10", allocate_first=True
    )
    assert decide(client, artist, second, first).json()["evaluation_refreshed"]
    assert client.get(f"/api/assets/{second}", headers=artist).json()["royalty"] is None
    mock_audio(monkeypatch, "15")
    third = submit(client, studio, license_["id"], content=b"independent next usage").json()["id"]
    result = process(client, studio, third)["result"]
    assert result["calculation"]["prior_seconds"] == "20"
    assert result["calculation"]["amount"] == "10.00"


def test_unassigned_artist_cannot_inspect_or_resolve_related_recordings(
    client, artist, studio, monkeypatch, terms
):
    from test_compliance_safety import edit_db

    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)
    edit_db(
        lambda db: db.add(
            Persona(id="unassigned_artist", role="artist", name="Unassigned", email="unassigned@example.test")
        )
    )
    other = {"X-Demo-Persona": "unassigned_artist"}
    assert client.get(f"/api/assets/{second}/overlap", headers=other).status_code == 404
    assert (
        client.post(
            f"/api/assets/{second}/overlap",
            headers=other,
            json={
                "related_asset_id": first,
                "decision": "SAME_USAGE",
                "note": "Unassigned identity must not review this usage.",
            },
        ).status_code
        == 404
    )


def test_overlap_refresh_never_uses_cached_assessment_after_a_failed_live_request(
    client, artist, studio, monkeypatch, terms
):
    from fastapi import HTTPException

    _, first, second = make_pair(client, artist, studio, monkeypatch, terms)

    def failure(*args, **kwargs):
        raise HTTPException(502, "Gemini rate limit (provider HTTP 429). No fixture fallback was used.")

    monkeypatch.setattr(ai, "content_findings", failure)
    assert (
        client.post(f"/api/assets/{second}/evaluate", headers=studio, json={"reprocess": True}).status_code
        == 502
    )
    saved = decide(client, artist, second, first)
    assert saved.status_code == 200 and not saved.json()["evaluation_refreshed"]
    assert client.get(f"/api/assets/{second}", headers=artist).json()["report"]["result"][
        "latest_attempt_failed"
    ]
    assert client.get("/api/royalties", headers=artist).json() == []


def test_new_uncertain_excerpt_does_not_revoke_independent_original_approval(
    client, artist, studio, monkeypatch, terms
):
    _, first, second = make_pair(client, artist, studio, monkeypatch, terms, allocate_first=True)
    royalty = client.get("/api/royalties", headers=artist).json()[0]
    url = f"/api/royalties/{royalty['id']}"
    assert (
        client.post(
            url + "/decision",
            headers=artist,
            json={"approve": True, "note": "Reviewed original independent use before excerpt resolution."},
        ).status_code
        == 200
    )
    assert decide(client, artist, second, first, "UNCERTAIN").status_code == 200
    assert client.get(f"/api/assets/{second}", headers=artist).json()["compliance_state"] == "NEEDS_REVIEW"
    original = client.get("/api/royalties", headers=artist).json()[0]
    assert original["eligible_for_charge"] and original["approval_current"]
    assert client.post(url + "/invoice", headers=artist).status_code == 201


def test_legacy_report_has_nullable_billing_state_and_requires_refresh(
    client, artist, studio, monkeypatch, terms
):
    from app.db import Report
    from test_compliance_safety import edit_db

    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    asset = submit(client, studio, license_["id"]).json()["id"]
    process(client, studio, asset)

    def legacy(db):
        report = db.scalar(select(Report).where(Report.asset_id == asset))
        report.result = {key: value for key, value in report.result.items() if key != "billing_usage"}
        report.result = {**report.result, "policy_version": 3}

    edit_db(legacy)
    response = client.get(f"/api/assets/{asset}", headers=artist)
    assert response.status_code == 200
    result = response.json()["report"]["result"]
    assert result["billing_usage"] is None and result["stale"]
    assert response.json()["compliance_state"] == "NEEDS_REVIEW"
