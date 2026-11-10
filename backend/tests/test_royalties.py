from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.royalties import calculate, evaluate
from app.schemas import Campaign, ContentFindings, Finding, Terms


def campaign(**overrides):
    return Campaign(
        name="Launch",
        region="US",
        medium="online advertising",
        language="English",
        category="consumer products",
        intended_use_date="2026-11-06",
    ).model_copy(update=overrides)


def measurement(seconds="45"):
    return {"spoken_seconds": seconds, "measurement_uncertain": False, "transcript": "A new collection."}


@pytest.mark.parametrize(
    "seconds,expected",
    [("20", "0.00"), ("30", "0.00"), ("45", "30.00"), ("30.125", "0.25"), ("30.0025", "0.01")],
)
def test_exact_decimal_calculations(terms, seconds, expected):
    assert calculate(terms, Decimal(seconds))["amount"] == expected


def test_per_asset_ignores_prior(terms):
    assert calculate(terms, Decimal(20), Decimal(100))["amount"] == "0.00"


def test_cumulative_remaining_allowance(terms):
    terms.billing_basis = "cumulative"
    result = calculate(terms, Decimal(20), Decimal(20))
    assert result["amount"] == "20.00"
    assert result["allowance_remaining"] == "10"


def test_restricted_declared_political_campaign(terms):
    result = evaluate(
        terms,
        campaign(category="political advertising"),
        measurement(),
        ContentFindings(findings=[], uncertainty=[]),
    )
    assert result["status"] == "RESTRICTED_USAGE"


def test_ai_possible_prohibition_requires_review(terms):
    findings = ContentFindings(
        findings=[
            Finding(
                category="political",
                passage="Vote for us",
                explanation="Possible political appeal",
                possible_conflict=True,
                needs_review=True,
            )
        ],
        uncertainty=[],
    )
    assert evaluate(terms, campaign(), measurement(), findings)["status"] == "NEEDS_REVIEW"


@pytest.mark.parametrize("metadata", [{"region": None}, {"language": ""}, {"medium": None}])
def test_missing_metadata_requires_review(terms, metadata):
    assert (
        evaluate(terms, campaign(**metadata), measurement(), ContentFindings(findings=[], uncertainty=[]))[
            "status"
        ]
        == "NEEDS_REVIEW"
    )


def test_unknown_terms_never_charge(terms):
    terms.additional_rate = None
    result = evaluate(terms, campaign(), measurement(), ContentFindings(findings=[], uncertainty=[]))
    assert result["status"] == "NEEDS_REVIEW"
    assert result["calculation"] is None


def test_vad_failure_does_not_use_total_duration(terms):
    result = evaluate(
        terms,
        campaign(),
        {"duration_seconds": "45", "spoken_seconds": None},
        ContentFindings(findings=[], uncertainty=[]),
    )
    assert result["status"] == "NEEDS_REVIEW"
    assert result["calculation"] is None


def test_speaker_failure_never_creates_charge(terms):
    assert (
        evaluate(
            terms,
            campaign(),
            measurement(),
            ContentFindings(findings=[], uncertainty=[]),
            speaker={"status": "unavailable"},
        )["status"]
        == "NEEDS_REVIEW"
    )


@pytest.mark.parametrize("seconds", ["NaN", "Infinity", "-1"])
def test_invalid_measures_rejected(terms, seconds):
    with pytest.raises(ValueError):
        calculate(terms, Decimal(seconds))


def test_date_and_schema_validation():
    with pytest.raises(ValidationError):
        Terms(start_date="2027-01-01", end_date="2026-01-01")
    assert Terms().additional_rate is None
    with pytest.raises(ValidationError):
        Terms(additional_rate="-1")


def test_additional_permission_required(terms):
    terms.additional_usage_permitted = False
    assert (
        evaluate(terms, campaign(), measurement(), ContentFindings(findings=[], uncertainty=[]))["status"]
        == "RESTRICTED_USAGE"
    )


def test_outside_scope_and_expired_are_restricted(terms):
    assert (
        evaluate(terms, campaign(region="CA"), measurement(), ContentFindings(findings=[], uncertainty=[]))[
            "status"
        ]
        == "RESTRICTED_USAGE"
    )
    assert (
        evaluate(
            terms,
            campaign(intended_use_date=__import__("datetime").date(2028, 1, 1)),
            measurement(),
            ContentFindings(findings=[], uncertainty=[]),
        )["status"]
        == "RESTRICTED_USAGE"
    )
