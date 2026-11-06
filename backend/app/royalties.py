from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .schemas import Campaign, ContentFindings, Terms

CENT = Decimal("0.01")


def calculate(terms: Terms, spoken_seconds: Decimal, prior_seconds: Decimal = Decimal(0)) -> dict:
    if terms.included_seconds is None or terms.additional_rate is None or terms.billing_basis is None:
        raise ValueError("Approved allowance, rate and billing basis are required.")
    if (
        not spoken_seconds.is_finite()
        or spoken_seconds < 0
        or not prior_seconds.is_finite()
        or prior_seconds < 0
    ):
        raise ValueError("Usage must be finite and nonnegative.")
    prior = prior_seconds if terms.billing_basis == "cumulative" else Decimal(0)
    allowance_remaining = max(Decimal(0), terms.included_seconds - prior)
    excess = max(Decimal(0), spoken_seconds - allowance_remaining)
    amount = (excess * terms.additional_rate).quantize(CENT, rounding=ROUND_HALF_UP)
    return {
        "spoken_seconds": str(spoken_seconds),
        "prior_seconds": str(prior),
        "included_seconds": str(terms.included_seconds),
        "allowance_remaining": str(allowance_remaining),
        "additional_seconds": str(excess),
        "rate": str(terms.additional_rate),
        "amount": str(amount),
        "currency": terms.currency,
        "billing_basis": terms.billing_basis,
        "rounding": "ROUND_HALF_UP to 2 decimals",
        "explanation": f"max(0, {spoken_seconds}s − {allowance_remaining}s remaining) × "
        f"{terms.additional_rate} {terms.currency}/s = {amount} {terms.currency}",
    }


def evaluate(
    terms: Terms,
    campaign: Campaign,
    measurement: dict,
    findings: ContentFindings,
    prior_seconds: Decimal = Decimal(0),
    speaker: dict | None = None,
) -> dict:
    reasons = []
    restricted = []
    fields = [
        "artist",
        "studio",
        "start_date",
        "end_date",
        "permitted_media",
        "territories",
        "languages",
        "campaigns",
        "included_seconds",
        "billing_basis",
        "additional_rate",
        "currency",
        "additional_usage_permitted",
        "restricted_categories",
    ]
    missing = [name for name in fields if getattr(terms, name) is None]
    if missing:
        reasons.append("Unknown contract terms: " + ", ".join(missing))
    reasons.extend(terms.ambiguities)
    if terms.special_conditions:
        reasons.append(
            "Special conditions require human interpretation: " + "; ".join(terms.special_conditions)
        )
    for label, rules, actual in [
        ("region", terms.territories, campaign.region),
        ("medium", terms.permitted_media, campaign.medium),
        ("language", terms.languages, campaign.language),
        ("campaign", terms.campaigns, campaign.name),
    ]:
        if rules is None:
            continue
        if not actual:
            if "*" not in rules:
                reasons.append(f"Missing declared {label}; permitted scope cannot be verified.")
        elif "*" not in rules and actual.casefold() not in [x.casefold() for x in rules]:
            restricted.append(f"Declared {label} '{actual}' falls outside the approved license.")
    if terms.start_date and campaign.intended_use_date < terms.start_date:
        restricted.append("Intended usage predates the license.")
    if terms.end_date and campaign.intended_use_date > terms.end_date:
        restricted.append("Intended usage is after license expiry.")
    if campaign.category and campaign.category.casefold() in [
        x.casefold() for x in terms.restricted_categories or []
    ]:
        restricted.append(f"Declared category '{campaign.category}' is prohibited by the approved terms.")
    if measurement.get("measurement_uncertain") or measurement.get("spoken_seconds") is None:
        reasons.append("Speech measurement is uncertain or unavailable; total duration is not substituted.")
    if not measurement.get("transcript", "").strip():
        reasons.append("No transcript available for content assessment.")
    for finding in findings.findings:
        if finding.possible_conflict or finding.needs_review:
            reasons.append(f"Possible {finding.category}: {finding.explanation}")
    reasons.extend(findings.uncertainty)
    if speaker and speaker.get("status") not in {"disabled", "match"}:
        reasons.append(
            "Experimental speaker verification is inconclusive or unavailable. No identity charge applies."
        )
    calculation = None
    if not missing and measurement.get("spoken_seconds") is not None:
        calculation = calculate(terms, Decimal(measurement["spoken_seconds"]), prior_seconds)
        if Decimal(calculation["additional_seconds"]) > 0 and terms.additional_usage_permitted is not True:
            restricted.append("Additional usage is not explicitly permitted.")
    if restricted:
        status = "RESTRICTED_USAGE"
    elif reasons:
        status = "NEEDS_REVIEW"
    elif calculation and Decimal(calculation["amount"]) > 0:
        status = "ADDITIONAL_ROYALTY_DUE"
    else:
        status = "COMPLIANT"
    return {
        "status": status,
        "reasons": restricted + reasons,
        "calculation": calculation,
        "findings": findings.model_dump(mode="json"),
        "metadata_note": "Region, medium and intended use are studio declarations. Audio does not prove distribution.",
        "legal_note": "AI findings and speaker similarity are not legal determinations.",
        "evaluated_on": date.today().isoformat(),
    }
