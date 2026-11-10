"""Explain the final deterministic outcome after all eligibility checks are applied."""


def explain_report(result):
    violations = [rule for rule in result.get("rule_checks", []) if rule["outcome"] == "violation"]
    satisfied = [
        rule
        for rule in result.get("rule_checks", [])
        if rule["outcome"] in {"satisfied", "enforced_before_invoice", "assessed_by_content_provider"}
    ]
    result["satisfied_conditions"] = satisfied
    result["violated_conditions"] = violations
    violation_messages = {rule["explanation"] for rule in violations}
    result["unresolved_conditions"] = [
        reason for reason in result["reasons"] if reason not in violation_messages
    ]
    result["primary_reason"] = (
        result["reasons"][0]
        if result["reasons"]
        else (
            "Included usage: no additional royalty or payable invoice."
            if (result.get("calculation") or {}).get("amount") == "0.00"
            else "Permitted additional usage requires separate artist charge approval."
        )
    )
    usage = result.get("billing_usage", {})
    if (
        usage.get("disposition") == "SAME_USAGE"
        and not usage.get("reconciliation_required")
        and not result["reasons"]
    ):
        result["primary_reason"] = (
            "Edited version linked to canonical licensed usage; no separate royalty allocation."
        )
    result["payable_amount"] = (
        "0.00"
        if usage.get("disposition") == "SAME_USAGE"
        else (result.get("calculation") or {}).get("amount")
        if result.get("eligible_for_charge")
        else None
    )
    if result["status"] == "RESTRICTED_USAGE":
        action = "Review the cited restriction. Correct incorrect metadata or obtain a new approved license; no invoice is permitted."
    elif usage.get("reconciliation_required"):
        action = "Reconcile existing usage allocations with the artist. Historical charges and invoices remain unchanged."
    elif usage.get("unresolved"):
        action = "Artist: compare the related recordings and record a same, separate or uncertain usage decision, then reevaluate."
    elif result.get("authorization", {}).get("status") != "artist_confirmed":
        action = "Artist: review identity and campaign authorization, save the attestation, then reevaluate."
    elif result["status"] == "NEEDS_REVIEW":
        action = "Resolve the listed evidence or contract uncertainty and reevaluate. No charge can be approved while held."
    elif usage.get("disposition") == "SAME_USAGE":
        action = "Open the canonical licensed usage for royalty and invoice review. This edited version receives no separate allocation."
    elif (result.get("calculation") or {}).get("amount") == "0.00":
        action = "Included usage. No payable invoice is needed."
    else:
        action = "Artist: inspect the deterministic calculation and approve the charge before creating an invoice with the selected payment provider."
    result["next_action"] = action
    return result
