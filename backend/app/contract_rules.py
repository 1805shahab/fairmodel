"""Source-backed clause recovery and conservative routing of non-content obligations."""

import re
from .schemas import Terms


def compact(value: str) -> str:
    return " ".join(value.split())


def locate_quote(quote: str, pages: list[dict], page_number: int | None = None) -> dict | None:
    if not quote.strip():
        return None
    pattern = r"\s+".join(re.escape(token) for token in quote.split())
    for page in pages:
        if page_number is not None and page["page"] != page_number:
            continue
        match = re.search(pattern, page["text"])
        if match:
            return {"page": page["page"], "quote": page["text"][match.start() : match.end()]}
    return None


def source_evidence(terms: Terms, pages: list[dict]) -> dict:
    valid = []
    warnings = []
    for item in terms.evidence:
        found = locate_quote(item.quote, pages, item.page)
        if item.field not in Terms.model_fields or not found:
            warnings.append(f"Unsupported source citation for {item.field}; manual review required.")
        else:
            citation = {"field": item.field, **found, "origin": "extracted", "verified": True}
            if citation not in valid:
                valid.append(citation)
    # Recover only the complete, already-approved condition verbatim. No LLM guesses,
    # invented page numbers, semantic rewrites, or changes to the approved terms.
    missing_conditions = []
    for condition in terms.special_conditions:
        supported = any(
            item["field"] == "special_conditions" and compact(condition) in compact(item["quote"])
            for item in valid
        )
        if not supported:
            found = locate_quote(condition, pages)
            if found:
                valid.append(
                    {"field": "special_conditions", **found, "origin": "source_text_match", "verified": True}
                )
            else:
                missing_conditions.append(condition)
    cited = {item["field"] for item in valid}
    missing = [
        name
        for name in Terms.model_fields
        if name not in {"evidence", "ambiguities"}
        and getattr(terms, name) not in (None, [], "")
        and (name not in cited or (name == "special_conditions" and missing_conditions))
    ]
    generated = {
        f"No verified source citation for {name}; confirm against the PDF." for name in Terms.model_fields
    }
    ambiguities = [warning for warning in terms.ambiguities if warning not in generated]
    # Only stale, machine-generated citation warnings may be replaced. Genuine
    # contract ambiguity is never cleared by source matching.
    warnings.extend(f"No verified source citation for {name}; confirm against the PDF." for name in missing)
    return {
        "citations": valid,
        "missing_fields": missing,
        "review_reasons": sorted(set(ambiguities + warnings)),
        "missing_conditions": missing_conditions,
    }


SUBMISSION = {
    "the studio must submit each generated advertisement for licensing compliance review before publication",
    "each generated advertisement must be submitted for licensing compliance review before publication",
}
APPROVAL = {
    "additional royalties must be approved by the artist before an invoice is issued",
    "the artist must approve additional royalties before an invoice is issued",
}


def condition_kind(text: str) -> tuple[str, str]:
    normalized = compact(text).casefold().rstrip(".")
    if normalized in SUBMISSION:
        return "administrative", "submission_before_publication"
    if normalized in APPROVAL:
        return "administrative", "artist_approval_before_invoice"
    if re.fullmatch(r"campaign category must be [\w -]+", normalized):
        return "metadata", "campaign_category"
    if (
        normalized.startswith(
            (
                "content must not contain ",
                "the advertisement must not contain ",
                "the transcript must not contain ",
            )
        )
        and ";" not in normalized
        and not any(
            word in normalized
            for word in ("submit", "invoice", "approval", "before publication", "territor", "spoken second")
        )
    ):
        return "content", "content_restriction"
    return "human_review", "unrecognized_condition"


def condition_plan(terms: Terms) -> list[dict]:
    return [
        {"text": text, "kind": condition_kind(text)[0], "check": condition_kind(text)[1]}
        for text in terms.special_conditions
    ]
