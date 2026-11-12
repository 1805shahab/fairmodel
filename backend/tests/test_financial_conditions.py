"""Approved financial prose must be checked by deterministic code, not Gemini."""

from decimal import Decimal

import pytest

from app import voice_generation
from app.contract_rules import condition_kind, condition_plan, source_evidence
from app.royalties import evaluate
from app.schemas import ContentFindings
from test_royalties import campaign, measurement
from test_voice_generation import setup_grant, wav_bytes
from test_workflow import mock_audio, process

SPEECH = "Billable duration is measured spoken duration, not total recording length; silence and non-speech music are excluded."
ROUNDING = "Fractional spoken seconds are billed proportionally. The final monetary amount is rounded to two decimal places using HALF_UP rounding."
APPROVAL = "The artist must approve additional royalties before an invoice is issued."


@pytest.mark.parametrize("text", [SPEECH, ROUNDING, SPEECH.upper(), ROUNDING.replace(". ", "; ")])
def test_supported_financial_prose_is_not_content_or_human_interpretation(text):
    assert condition_kind(text)[0] == "financial"


@pytest.mark.parametrize(
    "text",
    [
        ROUNDING.replace("HALF_UP", "HALF_EVEN"),
        ROUNDING + " Political endorsements are permitted.",
        SPEECH + " Additional approval is required from an outside agency.",
        "Fractional spoken seconds are billed proportionally unless the campaign is television.",
    ],
)
def test_conflicting_or_mixed_financial_prose_keeps_human_review(text):
    assert condition_kind(text)[0] == "human_review"


@pytest.mark.parametrize(
    "seconds,expected", [("23.52", "0.00"), ("45", "30.00"), ("58.77", "57.54"), ("30.0025", "0.01")]
)
def test_known_conditions_use_fractional_spoken_duration_and_final_half_up(terms, seconds, expected):
    terms.special_conditions = [SPEECH, ROUNDING, APPROVAL]
    usage = measurement(seconds=seconds)
    usage["duration_seconds"] = "96.19"
    result = evaluate(
        terms,
        campaign(),
        usage,
        ContentFindings(findings=[], uncertainty=[]),
        authorization={"identity_confirmed": True, "use_authorized": True},
    )
    assert result["status"] == ("COMPLIANT" if Decimal(expected) == 0 else "ADDITIONAL_ROYALTY_DUE")
    assert result["calculation"]["amount"] == expected
    assert result["calculation"]["spoken_seconds"] == seconds
    checks = [check for check in result["rule_checks"] if check.get("kind") == "financial"]
    assert len(checks) == 2 and all(check["outcome"] == "satisfied" for check in checks)


def test_speech_billing_requires_actual_reliable_measurement(terms):
    terms.special_conditions = [SPEECH]
    usage = measurement()
    usage["spoken_seconds"], usage["measurement_uncertain"] = None, True
    result = evaluate(
        terms,
        campaign(),
        usage,
        ContentFindings(findings=[], uncertainty=[]),
        authorization={"identity_confirmed": True, "use_authorized": True},
    )
    assert result["status"] == "NEEDS_REVIEW" and not result["eligible_for_charge"]
    assert result["calculation"] is None
    assert (
        next(check for check in result["rule_checks"] if check.get("kind") == "financial")["outcome"]
        == "needs_review"
    )


def test_financial_citations_are_still_mandatory(terms):
    terms.special_conditions = [ROUNDING]
    source = source_evidence(terms, [])
    result = evaluate(
        terms,
        campaign(),
        measurement(),
        ContentFindings(findings=[], uncertainty=[]),
        authorization={"identity_confirmed": True, "use_authorized": True},
        source_review=source,
    )
    assert result["status"] == "NEEDS_REVIEW" and not result["eligible_for_charge"]
    check = next(check for check in result["rule_checks"] if check.get("kind") == "financial")
    assert check["outcome"] == "needs_review" and check["citations"] == []
    assert "verified supporting contract quotation" in check["explanation"]


def test_generation_preview_and_full_analysis_use_approved_financial_clauses(
    client, artist, studio, monkeypatch, terms
):
    terms.special_conditions = [SPEECH, ROUNDING, APPROVAL]
    _, grant, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)
    preview = client.post(
        f"/api/licenses/{grant['license_id']}/estimate",
        headers=studio,
        json={"campaign": body["campaign"], "spoken_seconds": "45"},
    )
    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["scope_status"] == "SCOPE_APPEARS_PERMITTED" and data["calculation"]["amount"] == "30.00"
    checks = [check for check in data["checks"] if check.get("kind") == "financial"]
    assert len(checks) == 2 and all(check["citations"] for check in checks)
    assert any(check["outcome"] == "deferred_to_audio_analysis" for check in checks)
    assert any("not verify speech duration" in requirement for requirement in data["requirements"])
    monkeypatch.setattr(
        voice_generation,
        "synthesize",
        lambda *args: (wav_bytes(), {"service": "mocked test; no real Gemini call"}),
    )
    response = client.post("/api/generations", headers=studio, json=body)
    assert response.status_code == 201, response.text
    asset_id = response.json()["asset_id"]
    assert client.get("/api/royalties", headers=artist).json() == []
    mock_audio(monkeypatch, seconds="45")
    assert process(client, studio, asset_id, authorize_usage=False)["status"] == "NEEDS_REVIEW"
    report = process(client, studio, asset_id)
    assert report["status"] == "ADDITIONAL_ROYALTY_DUE", report
    assert report["result"]["calculation"]["amount"] == "30.00"
    assert not any("human interpretation" in reason for reason in report["result"]["reasons"])
    assert all(
        check["citations"] for check in report["result"]["rule_checks"] if check.get("kind") == "financial"
    )
    assert client.get("/api/invoices", headers=artist).json() == []
    saved = client.get(f"/api/licenses/{grant['license_id']}", headers=artist).json()
    assert saved["terms"]["special_conditions"] == [SPEECH, ROUNDING, APPROVAL]


def test_unknown_rounding_still_blocks_generation_before_provider(client, artist, studio, monkeypatch, terms):
    terms.special_conditions = [ROUNDING.replace("HALF_UP", "HALF_EVEN")]
    _, _, _, _, body = setup_grant(client, artist, studio, monkeypatch, terms)
    monkeypatch.setattr(
        voice_generation,
        "synthesize",
        lambda *args: pytest.fail("Unrecognized financial condition must block generation."),
    )
    response = client.post("/api/generations", headers=studio, json=body)
    assert response.status_code == 409 and "human interpretation" in response.json()["detail"]
    assert client.get("/api/generations", headers=studio).json() == []


def test_financial_conditions_never_enter_content_provider_plan(terms):
    terms.special_conditions = [SPEECH, ROUNDING, APPROVAL, "Content must not contain violent threats."]
    content = [item["text"] for item in condition_plan(terms) if item["kind"] == "content"]
    assert content == ["Content must not contain violent threats."]
