"""Bind manual usage review and charge eligibility to the actual persisted evidence."""

from fastapi import HTTPException
from sqlalchemy import select

from .db import Analysis, Asset, License, LicenseVersion, Report, RoyaltyApproval, UsageAuthorization
from .compliance_evidence import evidence_context
from .evidence import digest, evidence_hash

POLICY_VERSION = 4


def approved_version(db, asset, license_):
    version = db.scalar(
        select(LicenseVersion).where(
            LicenseVersion.license_id == asset.license_id,
            LicenseVersion.version == asset.license_version,
        )
    )
    if (
        license_.status != "ACTIVE"
        or not license_.approved_at
        or not version
        or version.approved_by != license_.artist_id
        or asset.studio_id != license_.studio_id
    ):
        raise HTTPException(
            409, "An active artist-approved contract snapshot and assigned studio are required."
        )
    return version


def authorization_state(db, asset, analysis, license_):
    review = db.scalar(select(UsageAuthorization).where(UsageAuthorization.asset_id == asset.id))
    valid = bool(
        review
        and review.artist_id == license_.artist_id
        and review.license_version == asset.license_version
        and review.evidence_hash
        in {evidence_hash(asset, analysis), evidence_hash(asset, analysis, legacy=True)}
    )
    return review, {
        "status": "artist_confirmed"
        if valid and review.identity_confirmed and review.use_authorized
        else "unresolved",
        "identity_confirmed": bool(valid and review.identity_confirmed),
        "use_authorized": bool(valid and review.use_authorized),
        "method": "artist_manual_review" if valid else "not_reviewed",
        "review_id": review.id if review else None,
        "reviewed_at": review.updated_at if review else None,
        "note": "Artist attestation is recorded separately from experimental speaker similarity.",
    }


def assessment_hash(asset, analysis, version, authorization, context=None) -> str:
    return digest(
        {
            "evidence": evidence_hash(asset, analysis),
            "approved_terms": version.terms,
            "authorization": authorization,
            "policy_version": POLICY_VERSION,
            "context": context,
        }
    )


def royalty_is_eligible(db, royalty) -> bool:
    if royalty.status == "REJECTED":
        return False
    asset = db.get(Asset, royalty.asset_id)
    license_ = db.get(License, royalty.license_id)
    analysis = db.scalar(select(Analysis).where(Analysis.asset_id == royalty.asset_id))
    report = db.scalar(select(Report).where(Report.asset_id == royalty.asset_id))
    if not asset or not license_ or not analysis or not report:
        return False
    try:
        version = approved_version(db, asset, license_)
    except HTTPException:
        return False
    _, authorization = authorization_state(db, asset, analysis, license_)
    context = evidence_context(db, asset, analysis, license_, version)
    result = report.result
    calculation = result.get("calculation") or {}
    return bool(
        result.get("policy_version") == POLICY_VERSION
        and result.get("eligible_for_charge")
        and result.get("input_hash") == assessment_hash(asset, analysis, version, authorization, context)
        and report.status in {"COMPLIANT", "ADDITIONAL_ROYALTY_DUE"}
        and authorization["status"] == "artist_confirmed"
        and context["usage"]["allocation_permitted"]
        and not context.get("cumulative_reconciliation_required")
        and calculation.get("amount") == royalty.amount
        and calculation.get("currency") == royalty.currency
    )


def approval_is_current(db, royalty) -> bool:
    if royalty.status != "APPROVED" or not royalty_is_eligible(db, royalty):
        return False
    report = db.scalar(select(Report).where(Report.asset_id == royalty.asset_id))
    return bool(
        db.scalar(
            select(RoyaltyApproval).where(
                RoyaltyApproval.royalty_id == royalty.id,
                RoyaltyApproval.artist_id == royalty.artist_id,
                RoyaltyApproval.evidence_hash == report.result.get("input_hash"),
            )
        )
    )
