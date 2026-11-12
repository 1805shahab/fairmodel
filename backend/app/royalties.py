from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .schemas import Campaign, ContentFindings, Terms
from .canonical import MEDIA, canonical, category, label as canonical_label, medium_scope, territory
from .contract_rules import compact, condition_plan

CENT = Decimal("0.01")


def calculate(terms: Terms, spoken_seconds: Decimal, prior_seconds: Decimal = Decimal(0)) -> dict:
    if terms.included_seconds is None or terms.additional_rate is None or terms.billing_basis is None:
        raise ValueError("Approved allowance, rate and billing basis are required.")
    if (
        not terms.included_seconds.is_finite()
        or terms.included_seconds < 0
        or not terms.additional_rate.is_finite()
        or terms.additional_rate < 0
        or terms.currency not in {"USD", "EUR", "GBP"}
        or terms.billing_basis not in {"per_asset", "cumulative"}
    ):
        raise ValueError(
            "Approved finite nonnegative financial terms and a supported currency/billing basis are required."
        )
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
    authorization: dict | None = None,
    evidence_is_fixture: bool = False,
    assessment_is_fixture: bool = False,
    source_review: dict | None = None,
    workflow: dict | None = None,
    overlap: list[dict] | None = None,
    preview_only: bool = False,
) -> dict:
    reasons = []
    restricted = []
    checks = []

    def check(rule, outcome, explanation, field=None):
        citations = [x for x in (source_review or {}).get("citations", []) if x["field"] == field]
        if outcome == "violation" and source_review is not None and field in source_review["missing_fields"]:
            outcome = "needs_review"
            explanation += (
                " Supporting contract provenance is incomplete; no substantiated violation is asserted."
            )
        checks.append({"rule": rule, "outcome": outcome, "explanation": explanation, "citations": citations})
        if outcome == "violation":
            restricted.append(explanation)
        elif outcome == "needs_review":
            reasons.append(explanation)

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
    reasons.extend(source_review["review_reasons"] if source_review is not None else terms.ambiguities)
    for label, rules, actual in [
        ("region", terms.territories, campaign.region),
        ("medium", terms.permitted_media, campaign.medium),
        ("language", terms.languages, campaign.language),
        ("campaign", terms.campaigns, campaign.name),
    ]:
        if rules is None:
            continue
        if not rules:
            check(
                label, "needs_review", f"Approved {label} scope is empty; explicit permission needs review."
            )
            continue
        if not actual:
            if "*" not in rules:
                check(label, "needs_review", f"Missing declared {label}; permitted scope cannot be verified.")
            continue
        field = {
            "region": "territories",
            "medium": "permitted_media",
            "language": "languages",
            "campaign": "campaigns",
        }[label]
        if label == "medium":
            outcome = medium_scope(actual, rules)
            check(
                "medium",
                {"allowed": "satisfied", "violated": "violation", "uncertain": "needs_review"}[outcome],
                f"Declared medium '{actual}' "
                + (
                    "is permitted by an exact/documented equivalent license category."
                    if outcome == "allowed"
                    else "falls outside the approved license."
                    if outcome == "violated"
                    else "requires semantic review; no documented medium equivalence establishes permission or a violation."
                ),
                field,
            )
            checks[-1]["canonical_declared"] = canonical(actual, MEDIA)
            checks[-1]["canonical_permitted"] = [canonical(x, MEDIA) for x in rules]
        else:
            normalizer = territory if label == "region" else canonical_label
            allowed = "*" in rules or normalizer(actual) in [normalizer(x) for x in rules]
            check(
                label,
                "satisfied" if allowed else "violation",
                f"Declared {label} '{actual}' "
                + ("matches the approved scope." if allowed else "falls outside the approved license."),
                field,
            )
    if terms.start_date and campaign.intended_use_date < terms.start_date:
        check("start_date", "violation", "Intended usage predates the license.", "start_date")
    if terms.end_date and campaign.intended_use_date > terms.end_date:
        check("end_date", "violation", "Intended usage is after license expiry.", "end_date")
    if campaign.category and category(campaign.category) in [
        category(x) for x in terms.restricted_categories or []
    ]:
        check(
            "restricted_category",
            "violation",
            f"Declared category '{campaign.category}' is prohibited by the approved terms.",
            "restricted_categories",
        )
    if terms.restricted_categories and not campaign.category:
        reasons.append("Missing declared campaign category; restricted-category eligibility requires review.")
    for condition in condition_plan(terms):
        kind, code = condition["kind"], condition["check"]
        outcome, explanation = "needs_review", "Condition requires human interpretation: " + condition["text"]
        if code == "submission_before_publication":
            if (workflow or {}).get("submission_recorded"):
                outcome = "satisfied"
                explanation = "Studio upload and compliance-request receipts verify submission for review in this application. External publication timing is not independently verified."
            else:
                explanation = "Administrative submission-for-review receipts are incomplete. This cannot be inferred from spoken dialogue."
        elif code == "artist_approval_before_invoice":
            outcome = "enforced_before_invoice"
            explanation = "Artist charge approval is a separate recorded workflow decision required before invoice creation. This obligation is not due during transcript analysis."
        elif kind == "metadata":
            expected = canonical_label(condition["text"]).rstrip(".").split(" must be ", 1)[-1]
            if campaign.category and category(campaign.category) == category(expected):
                outcome, explanation = (
                    "satisfied",
                    "Declared campaign category satisfies the source-backed metadata condition.",
                )
            else:
                declared = (campaign.category or "").strip()
                explanation = (
                    f"Campaign category is missing. Enter '{expected}' to satisfy the approved category condition."
                    if not declared
                    else f"Declared campaign category '{declared}' does not match the approved required category '{expected}'. Correct the metadata or ask the artist to review the contract; permission is not inferred."
                )
        elif kind == "content":
            outcome, explanation = (
                "assessed_by_content_provider",
                "Content condition was supplied to the transcript assessment provider: " + condition["text"],
            )
        elif kind == "financial":
            try:
                # Verify supported approved Decimal rules, not an LLM's calculation.
                calculate(terms, Decimal(0))
                required = condition["financial_checks"]
                if "spoken_duration" in required:
                    if preview_only:
                        outcome = "deferred_to_audio_analysis"
                        explanation = "Supported billing rule: actual billable spoken duration will be measured from speech activity after generation; total recording length is not substituted. This preview does not verify speech duration."
                    elif (
                        measurement.get("measurement_uncertain") or measurement.get("spoken_seconds") is None
                    ):
                        explanation = "The approved speech-only billing condition needs a reliable spoken-duration measurement; total recording length cannot replace it."
                    else:
                        calculate(terms, Decimal(measurement["spoken_seconds"]))
                        outcome = "satisfied"
                        explanation = "The royalty engine uses measured spoken seconds, excluding time outside estimated speech activity. Total recording length is not used as billable speech; final artist review remains required."
                else:
                    outcome = "satisfied"
                    explanation = "The deterministic royalty engine retains fractional spoken seconds using Decimal arithmetic and rounds only the final monetary amount to two decimal places with ROUND_HALF_UP."
            except (ValueError, ArithmeticError):
                outcome, explanation = (
                    "needs_review",
                    "Approved financial rules or spoken-duration evidence cannot be applied safely by the deterministic engine.",
                )
        check(code, outcome, explanation, "special_conditions")
        if kind == "financial" and source_review is not None:
            checks[-1]["citations"] = [
                citation
                for citation in checks[-1]["citations"]
                if citation.get("verified") and compact(condition["text"]) in compact(citation["quote"])
            ]
            if not checks[-1]["citations"]:
                checks[-1]["outcome"] = "needs_review"
                checks[-1]["explanation"] = (
                    "This financial condition lacks a verified supporting contract quotation; human source review is required."
                )
                reasons.append(checks[-1]["explanation"])
        checks[-1]["kind"], checks[-1]["condition"] = kind, condition["text"]
    if measurement.get("measurement_uncertain") or measurement.get("spoken_seconds") is None:
        reasons.append("Speech measurement is uncertain or unavailable; total duration is not substituted.")
    if not measurement.get("transcript", "").strip():
        reasons.append("No transcript available for content assessment.")
    for finding in findings.findings:
        if finding.possible_conflict or finding.needs_review:
            reasons.append(f"Possible {finding.category}: {finding.explanation}")
    reasons.extend(findings.uncertainty)
    authorization = authorization or {}
    if not authorization.get("identity_confirmed"):
        reasons.append(
            "Speaker identity has not been confirmed by the artist. Optional speaker verification is not identity proof."
        )
    if not authorization.get("use_authorized"):
        reasons.append("Artist authorization for this asset and campaign is unresolved.")
    if overlap:
        reasons.append(
            "Possible duplicate/overlapping usage needs review before any new allocation. Transcript similarity is a conservative signal, not proof of identical audio or unauthorized use."
        )
    if (
        speaker
        and speaker.get("status") not in {"disabled", "match"}
        and not authorization.get("identity_confirmed")
    ):
        reasons.append(
            "Experimental speaker verification is inconclusive or unavailable. No identity charge applies."
        )
    calculation = None
    if not missing and measurement.get("spoken_seconds") is not None:
        try:
            spoken = Decimal(measurement["spoken_seconds"])
            total = Decimal(measurement["duration_seconds"]) if measurement.get("duration_seconds") else None
            if total is not None and (not total.is_finite() or spoken > total):
                raise ValueError("Invalid speech measurement")
            calculation = calculate(terms, spoken, prior_seconds)
        except (ValueError, ArithmeticError):
            reasons.append(
                "Speech duration is invalid or exceeds the recording; measurement review is required."
            )
        if (
            calculation
            and Decimal(calculation["additional_seconds"]) > 0
            and terms.additional_usage_permitted is not True
        ):
            if terms.additional_usage_permitted is False:
                check(
                    "additional_usage",
                    "violation",
                    "Additional usage is not explicitly permitted.",
                    "additional_usage_permitted",
                )
            else:
                check(
                    "additional_usage",
                    "needs_review",
                    "Additional usage permission is unknown.",
                    "additional_usage_permitted",
                )
    if evidence_is_fixture and not assessment_is_fixture:
        reasons.append(
            "Gemini assessed an offline fixture transcript. Run live Groq transcription before proposing a live-evidence charge."
        )
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
        "rule_checks": checks,
        "substantiated_violations": [x for x in checks if x["outcome"] == "violation"],
        "overlap": overlap or [],
        "calculation": calculation,
        "eligible_for_charge": status in {"COMPLIANT", "ADDITIONAL_ROYALTY_DUE"},
        "authorization": authorization,
        "identity_verification": "not_automatically_verified",
        "findings": findings.model_dump(mode="json"),
        "metadata_note": "Region, medium and intended use are studio declarations. Audio does not prove distribution.",
        "legal_note": "AI findings and speaker similarity are not legal determinations.",
        "evaluated_on": date.today().isoformat(),
    }
