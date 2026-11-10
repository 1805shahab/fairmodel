"""Regression coverage for the reported version-4 contract semantics (no private inputs)."""

import json
import wave
from unittest.mock import MagicMock
import pytest
from sqlalchemy import select
from app import ai, audio
from app.canonical import medium_scope
from app.contract_rules import condition_kind, source_evidence
from app.db import Audit, LicenseVersion, get_session
from app.main import app
from app.royalties import evaluate
from app.schemas import ContentFindings, Terms
from test_compliance_safety import edit_db
from test_royalties import campaign, measurement
from test_workflow import mock_audio, process, setup_license, submit

SUBMIT = (
    "The studio must submit each generated advertisement for licensing compliance review before publication."
)
APPROVE = "Additional royalties must be approved by the artist before an invoice is issued."


def actual_scope(terms):
    return terms.model_copy(
        update={
            "permitted_media": ["Online commercial advertisements"],
            "territories": ["United States"],
            "campaigns": ["Spring Campaign"],
            "restricted_categories": [
                "Political endorsements",
                "gambling promotions",
                "adult-content advertising",
            ],
            "special_conditions": [SUBMIT, APPROVE],
        }
    )


@pytest.mark.parametrize(
    "declared,permitted,expected",
    [
        ("online advertising", "Online commercial advertisements", "allowed"),
        (" ONLINE commercial ADVERTISING ", "online advertising", "allowed"),
        ("television", "Online commercial advertisements", "violated"),
        ("podcast", "Online commercial advertisements", "violated"),
        ("radio", "Online commercial advertisements", "violated"),
        ("online video placement", "Online commercial advertisements", "uncertain"),
        ("online advertising", "online advertising on approved news sites only", "uncertain"),
    ],
)
def test_medium_equivalences_are_explicit_and_preserve_limits(declared, permitted, expected):
    assert medium_scope(declared, [permitted]) == expected


def test_authorized_2352_seconds_uses_live_measurement_not_total_and_admin_receipts(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, actual_scope(terms))
    mock_audio(monkeypatch, "23.52")
    asset_id = submit(client, studio, license_["id"], name="Spring Campaign").json()["id"]
    result = process(client, studio, asset_id)["result"]
    assert result["status"] == "COMPLIANT" and result["eligible_for_charge"]
    assert result["calculation"]["amount"] == "0.00"
    assert result["calculation"]["spoken_seconds"] == "23.52"
    checks = {check["rule"]: check for check in result["rule_checks"]}
    assert checks["medium"]["canonical_declared"] == "online_advertising"
    assert checks["medium"]["outcome"] == "satisfied"
    assert checks["submission_before_publication"]["outcome"] == "satisfied"
    assert checks["artist_approval_before_invoice"]["outcome"] == "enforced_before_invoice"
    assert result["workflow"]["upload_event_id"] and result["workflow"]["review_request_event_id"]
    assert not result["workflow"]["publication_verified"]
    assert not result["substantiated_violations"]
    assert (
        client.get(f"/api/assets/{asset_id}", headers=artist).json()["analysis"]["result"]["speaker"][
            "status"
        ]
        == "disabled"
    )
    assert (
        client.post(
            f"/api/royalties/{client.get('/api/royalties', headers=artist).json()[0]['id']}/invoice",
            headers=artist,
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "metadata,rule",
    [({"medium": "television"}, "medium"), ({"category": "political advertising"}, "restricted_category")],
)
def test_genuine_approved_prohibition_is_explainable(
    client, artist, studio, monkeypatch, terms, metadata, rule
):
    license_ = setup_license(client, artist, monkeypatch, actual_scope(terms))
    mock_audio(monkeypatch, "23.52")
    asset_id = submit(client, studio, license_["id"], name="Spring Campaign", **metadata).json()["id"]
    result = process(client, studio, asset_id)["result"]
    assert result["status"] == "RESTRICTED_USAGE"
    assert result["substantiated_violations"][0]["rule"] == rule
    assert result["substantiated_violations"][0]["citations"][0]["quote"].strip()
    assert client.get("/api/royalties", headers=artist).json() == []


def test_missing_admin_database_receipt_is_review_not_spoken_evidence(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, actual_scope(terms))
    mock_audio(monkeypatch, "23.52")
    asset_id = submit(client, studio, license_["id"], name="Spring Campaign").json()["id"]

    def remove_receipt(db):
        db.delete(
            db.scalar(select(Audit).where(Audit.entity_id == asset_id, Audit.action == "asset.uploaded"))
        )

    edit_db(remove_receipt)
    result = process(client, studio, asset_id)["result"]
    assert result["status"] == "NEEDS_REVIEW"
    assert any("receipts are incomplete" in reason for reason in result["reasons"])
    assert not result["substantiated_violations"]


def test_exact_source_recovers_each_admin_clause_and_preserves_genuine_ambiguity():
    terms = Terms(
        special_conditions=[SUBMIT, APPROVE],
        ambiguities=[
            "No verified source citation for special_conditions; confirm against the PDF.",
            "Campaign purpose needs human interpretation.",
        ],
    )
    pages = [{"page": 2, "text": SUBMIT.replace(" ", "\n \n") + "\n" + APPROVE}]
    resolved = source_evidence(terms, pages)
    assert len(resolved["citations"]) == 2 and all(c["page"] == 2 for c in resolved["citations"])
    assert all(c["quote"] in pages[0]["text"] for c in resolved["citations"])
    assert resolved["review_reasons"] == ["Campaign purpose needs human interpretation."]
    assert terms.evidence == [] and len(terms.ambiguities) == 2
    checked = ai.validate_evidence(terms, pages)
    assert len(checked.evidence) == 2


def test_missing_condition_source_is_never_invented():
    terms = Terms(special_conditions=[SUBMIT])
    resolved = source_evidence(terms, [{"page": 1, "text": "Unrelated source clause."}])
    assert not resolved["citations"] and "special_conditions" in resolved["missing_fields"]
    assert resolved["review_reasons"]


def test_missing_medium_provenance_is_not_a_substantiated_violation(terms):
    result = evaluate(
        terms,
        campaign(medium="television"),
        measurement("23.52"),
        ContentFindings(findings=[], uncertainty=[]),
        authorization={"identity_confirmed": True, "use_authorized": True},
        source_review={
            "citations": [],
            "missing_fields": ["permitted_media"],
            "review_reasons": ["Missing medium provenance."],
        },
    )
    assert result["status"] == "NEEDS_REVIEW" and not result["substantiated_violations"]


def test_live_prompt_excludes_admin_scope_and_financial_fields(monkeypatch, terms):
    terms = actual_scope(terms)
    terms.special_conditions.append("Content must not contain violent threats.")
    request = MagicMock(return_value=ContentFindings(findings=[], uncertainty=[]))
    monkeypatch.setattr(ai, "gemini_json", request)
    ai.content_findings(
        terms, "A consented creative narration.", False, campaign={"category": "consumer products"}
    )
    encoded = json.dumps(request.call_args.args[1])
    assert SUBMIT not in encoded and APPROVE not in encoded
    assert "included_seconds" not in encoded and "permitted_media" not in encoded
    assert "violent threats" in encoded
    assert "OUTSIDE this model" in request.call_args.args[2]


def test_benign_metadata_findings_are_not_promoted_to_conflicts(monkeypatch, terms):
    result = ContentFindings(
        findings=[
            {
                "category": "Campaign",
                "passage": "a contract quote",
                "explanation": "The campaign matches.",
                "possible_conflict": False,
                "needs_review": False,
            }
        ],
        uncertainty=[],
    )
    monkeypatch.setattr(ai, "gemini_json", lambda *args: result)
    findings, _ = ai.content_findings(terms, "No spoken campaign name is required.", False)
    assert not findings.findings and not findings.uncertainty


def test_uncertain_creative_purpose_is_review_not_restricted(terms):
    findings = ContentFindings(
        findings=[
            {
                "category": "Campaign purpose",
                "scope": "purpose",
                "passage": "An unusual creative narration.",
                "explanation": "Its campaign purpose is uncertain.",
                "possible_conflict": False,
                "needs_review": True,
            }
        ],
        uncertainty=[],
    )
    result = evaluate(
        terms,
        campaign(),
        {**measurement("23.52"), "transcript": "An unusual creative narration."},
        findings,
        authorization={"identity_confirmed": True, "use_authorized": True},
    )
    assert result["status"] == "NEEDS_REVIEW" and result["calculation"]["amount"] == "0.00"
    assert not result["substantiated_violations"]


def test_disabled_speaker_requires_manual_artist_attestation(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, actual_scope(terms))
    mock_audio(monkeypatch, "23.52")
    asset_id = submit(client, studio, license_["id"], name="Spring Campaign").json()["id"]
    result = process(client, studio, asset_id, authorize_usage=False)["result"]
    assert result["status"] == "NEEDS_REVIEW" and not result["eligible_for_charge"]
    assert result["identity_verification"] == "not_automatically_verified"
    assert client.get("/api/royalties", headers=artist).json() == []


def test_overlap_and_file_duplicates_cannot_allocate_a_second_charge(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    text = "First licensed narration with enough distinct words to establish a substantial matching passage in this original campaign recording."
    monkeypatch.setattr(
        ai, "transcribe", lambda *args: {"transcript": text, "provider": "groq:mock-test", "timestamps": []}
    )
    first = submit(client, studio, license_["id"], content=b"original").json()["id"]
    assert process(client, studio, first)["status"] == "ADDITIONAL_ROYALTY_DUE"
    duplicate = submit(client, studio, license_["id"], content=b"original")
    assert duplicate.status_code == 200 and duplicate.json()["id"] == first
    second = submit(client, studio, license_["id"], content=b"transcoded or overlapping excerpt").json()["id"]
    report = process(client, studio, second)
    assert report["status"] == "NEEDS_REVIEW"
    assert report["result"]["overlap"][0]["asset_id"] == first
    assert client.get(f"/api/assets/{second}", headers=artist).json()["royalty"] is None
    assert len(client.get("/api/royalties", headers=artist).json()) == 1
    # Repeated evaluation and older allocated asset remain idempotent.
    assert process(client, studio, second)["status"] == "NEEDS_REVIEW"
    assert client.get("/api/royalties", headers=artist).json()[0]["eligible_for_charge"]


def test_condition_router_is_conservative():
    assert condition_kind(SUBMIT)[0] == "administrative"
    assert condition_kind(APPROVE)[0] == "administrative"
    assert condition_kind("Campaign category must be consumer products.")[0] == "metadata"
    assert condition_kind("Content must not contain violent threats.")[0] == "content"
    assert (
        condition_kind("Content must not contain threats and the studio must submit it for approval.")[0]
        == "human_review"
    )
    assert condition_kind("Usage must be appropriate and all approvals obtained.")[0] == "human_review"


def test_normalized_fingerprint_ignores_container_metadata(tmp_path):
    paths = [tmp_path / "first.wav", tmp_path / "renamed.wav"]
    for path in paths:
        with wave.open(str(path), "wb") as sample:
            sample.setnchannels(1)
            sample.setsampwidth(2)
            sample.setframerate(16000)
            sample.writeframes(b"\x01\x00" * 16000)
    # A non-audio trailing metadata chunk changes the container's raw file hash.
    paths[1].write_bytes(paths[1].read_bytes() + b"LIST\x04\x00\x00\x00test")
    assert paths[0].read_bytes() != paths[1].read_bytes()
    assert (
        audio.normalized_fingerprint(paths[0])["pcm_sha256"]
        == audio.normalized_fingerprint(paths[1])["pcm_sha256"]
    )


def test_decoded_duplicates_hold_even_when_transcription_differs(client, artist, studio, monkeypatch, terms):
    license_ = setup_license(client, artist, monkeypatch, terms)
    mock_audio(monkeypatch)
    monkeypatch.setattr(
        audio, "normalized_fingerprint", lambda path: {"pcm_sha256": "test-identical-decoded-samples"}
    )
    first = submit(client, studio, license_["id"], content=b"container one").json()["id"]
    assert process(client, studio, first)["status"] == "ADDITIONAL_ROYALTY_DUE"
    monkeypatch.setattr(
        ai,
        "transcribe",
        lambda *args: {
            "provider": "groq:mock-test",
            "timestamps": [],
            "transcript": "Differing recognition.",
        },
    )
    second = submit(client, studio, license_["id"], content=b"container two").json()["id"]
    result = process(client, studio, second)["result"]
    assert result["status"] == "NEEDS_REVIEW"
    assert result["overlap"][0]["kind"] == "decoded_audio_duplicate"
    assert len(client.get("/api/royalties", headers=artist).json()) == 1


def test_api_serializes_verified_quotes_and_persists_approved_snapshot_unchanged(
    client, artist, studio, monkeypatch, terms
):
    license_ = setup_license(client, artist, monkeypatch, actual_scope(terms))

    def legacy_missing(db):
        version = db.scalar(select(LicenseVersion).where(LicenseVersion.license_id == license_["id"]))
        version.terms = {
            **version.terms,
            "evidence": [x for x in version.terms["evidence"] if x["field"] != "special_conditions"],
            "ambiguities": ["No verified source citation for special_conditions; confirm against the PDF."],
        }

    edit_db(legacy_missing)
    mock_audio(monkeypatch, "23.52")
    asset_id = submit(client, studio, license_["id"], name="Spring Campaign").json()["id"]
    result = process(client, studio, asset_id)["result"]
    assert result["status"] == "COMPLIANT"
    assert result["source_review"]["recovered_condition_citations"] == 2
    assert all(
        item["verified"] and item["quote"].strip() and item["page"] >= 1 for item in result["source_pages"]
    )
    generator = app.dependency_overrides[get_session]()
    db = next(generator)
    try:
        version = db.scalar(select(LicenseVersion).where(LicenseVersion.license_id == license_["id"]))
        assert len(version.terms["ambiguities"]) == 1
        assert not any(x["field"] == "special_conditions" for x in version.terms["evidence"])
    finally:
        generator.close()
