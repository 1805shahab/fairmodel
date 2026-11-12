"""Private persisted evidence projections. Reading a passport never performs provider writes."""

from decimal import Decimal
from sqlalchemy import select

from .db import (
    Analysis,
    Audit,
    CaseEvent,
    EvidenceRevision,
    LicenseVersion,
    Persona,
    Royalty,
    RoyaltyApproval,
    UsageCase,
    now,
    serialize,
)
from .evidence import digest, evidence_hash
from .contract_rules import source_evidence, condition_plan
from .schemas import ContentFindings, Terms
from .royalties import calculate, evaluate

DISCLAIMER = "Workflow evidence record only — not a legal certificate or biometric proof of identity."
ESTIMATE_NOTICE = "Estimate only — actual charges depend on submitted usage, the approved agreement, compliance checks, and artist approval."


def capture_revision(db, kind, record, origin="workflow_snapshot"):
    if record is None:
        return
    db.flush()
    snapshot = serialize(record)
    for key in ("path", "normalized_path", "contract_path"):
        snapshot.pop(key, None)
    revision_hash = digest(snapshot)
    existing = db.scalar(
        select(EvidenceRevision).where(
            EvidenceRevision.asset_id == record.asset_id,
            EvidenceRevision.kind == kind,
            EvidenceRevision.revision_hash == revision_hash,
        )
    )
    if existing is None:
        db.add(
            EvidenceRevision(
                asset_id=record.asset_id,
                kind=kind,
                revision_hash=revision_hash,
                snapshot=snapshot,
                origin=origin,
            )
        )


def provenance(analysis, report):
    a = analysis or {}
    r = report or {}

    def mode(value, fixture, prefix):
        if value.get(fixture) is True:
            return "fixture"
        receipt = value.get("provider_receipt") or {}
        if (
            receipt.get("mode") == "live"
            and receipt.get("succeeded_at")
            and value.get("provider", "").startswith(prefix)
        ):
            return "live"
        return "unverified"

    return {
        "transcription": mode(a, "demo_fixture", "groq:"),
        "compliance": mode(r, "assessment_fixture", "gemini:"),
    }


def case_view(db, case, asset, analysis):
    events = list(
        db.scalars(
            select(CaseEvent).where(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at, CaseEvent.id)
        )
    )
    resolution = next((event for event in reversed(events) if event.kind == "RESOLVE"), None)
    resolved_hash = resolution.evidence_hash if resolution else case.evidence_hash
    stale = case.status == "RESOLVED" and resolved_hash != review_fingerprint(asset, analysis)
    return {
        **serialize(case),
        "status": "STALE_REVIEW" if stale else case.status,
        "stale": stale,
        "events": [{**serialize(e), "actor_name": db.get(Persona, e.actor_id).name} for e in events],
        "requires_reconciliation": case.status != "RESOLVED" or stale,
    }


def review_fingerprint(asset, analysis):
    return (
        evidence_hash(asset, analysis)
        if analysis
        else digest(
            {
                "asset_id": asset.id,
                "file_hash": asset.file_hash,
                "campaign": asset.campaign,
                "license_version": asset.license_version,
                "analysis": None,
            }
        )
    )


def review_context(db, asset, member_ids=None):
    ids = set(member_ids or [asset.id]) | {asset.id}
    rows = list(
        db.scalars(
            select(UsageCase).where(UsageCase.asset_id.in_(ids)).order_by(UsageCase.created_at, UsageCase.id)
        )
    )
    context = []
    for row in rows:
        from .db import Asset

        related = db.get(Asset, row.asset_id)
        analysis = db.scalar(select(Analysis).where(Analysis.asset_id == row.asset_id))
        view = case_view(db, row, related, analysis)
        context.append(
            {
                "id": row.id,
                "asset_id": row.asset_id,
                "decision": row.decision,
                "status": view["status"],
                "updated_at": row.updated_at,
            }
        )
    return {"cases": context, "blocked": any(x["status"] != "RESOLVED" for x in context)}


def passport(db, asset, license_, view):
    version = db.scalar(
        select(LicenseVersion).where(
            LicenseVersion.license_id == asset.license_id, LicenseVersion.version == asset.license_version
        )
    )
    terms = Terms.model_validate(version.terms) if version else None
    source = (
        source_evidence(terms, license_.pages)
        if terms
        else {"citations": [], "review_reasons": ["No approved snapshot is available."]}
    )
    analysis = view.get("analysis")
    report = view.get("report")
    royalty = view.get("royalty")
    invoice = view.get("invoice")
    history = [
        serialize(x)
        for x in db.scalars(
            select(EvidenceRevision)
            .where(EvidenceRevision.asset_id == asset.id)
            .order_by(EvidenceRevision.created_at.desc(), EvidenceRevision.id.desc())
        )
    ]
    ids = {asset.id, license_.id}
    if royalty:
        ids.add(royalty["id"])
    if invoice:
        ids.add(invoice["id"])
    events = list(
        db.scalars(
            select(Audit)
            .where(
                Audit.entity_id.in_(ids),
                Audit.artist_id == license_.artist_id,
                Audit.studio_id == license_.studio_id,
            )
            .order_by(Audit.created_at, Audit.id)
        )
    )
    cases = [
        case_view(db, x, asset, db.scalar(select(Analysis).where(Analysis.asset_id == asset.id)))
        for x in db.scalars(
            select(UsageCase).where(UsageCase.asset_id == asset.id).order_by(UsageCase.created_at.desc())
        )
    ]
    current_analysis = analysis["result"] if analysis else {}
    current_report = report["result"] if report else {}
    authorization = view.get("authorization")
    return {
        "id": "VP-" + asset.id.upper(),
        "asset_id": asset.id,
        "snapshot_at": now(),
        "disclaimer": DISCLAIMER,
        "private": True,
        "asset": view,
        "artist": {"id": license_.artist_id, "name": db.get(Persona, license_.artist_id).name},
        "studio": {"id": asset.studio_id, "name": db.get(Persona, asset.studio_id).name},
        "license": {
            "id": license_.id,
            "title": license_.title,
            "version": asset.license_version,
            "approved_by": version.approved_by if version else None,
            "approved_at": version.created_at if version else None,
            "terms": version.terms if version else None,
            "source_review": source,
        },
        "audio_evidence": {
            "sha256": asset.file_hash,
            "hash_note": "File integrity hash; not an acoustic fingerprint or identity proof.",
            "analysis_id": analysis["id"] if analysis else None,
            "analysis_revision": digest(current_analysis) if analysis else None,
            "processing": "FFprobe / FFmpeg",
            "measured_at": analysis["updated_at"] if analysis else None,
        },
        "provenance": provenance(current_analysis, current_report),
        "history": history,
        "history_note": "History is captured from schema 5 onward. Migration preserves the then-current records only; earlier overwritten decisions cannot be reconstructed.",
        "cases": cases,
        "charge_approvals": [
            serialize(row)
            for row in db.scalars(
                select(RoyaltyApproval)
                .where(RoyaltyApproval.royalty_id == royalty["id"])
                .order_by(RoyaltyApproval.created_at)
            )
        ]
        if royalty
        else [],
        "audit": [{**serialize(x), "actor_name": db.get(Persona, x.actor_id).name} for x in events],
        "stages": [
            {"label": "Submitted", "state": "complete", "detail": asset.created_at},
            {
                "label": "Audio analyzed",
                "state": "complete" if analysis else "pending",
                "detail": view["processing_state"],
            },
            {
                "label": "Compliance",
                "state": "hold"
                if view["compliance_state"] in {"NEEDS_REVIEW", "RESTRICTED_USAGE"}
                else "complete"
                if report
                else "pending",
                "detail": view["compliance_state"],
            },
            {
                "label": "Artist attestation",
                "state": "complete"
                if authorization and authorization["status"] == "artist_confirmed"
                else "pending",
                "detail": "Manual attestation; no biometric verification",
            },
            {
                "label": "Charge approval",
                "state": "included"
                if royalty and royalty["status"] == "NO_CHARGE"
                else "complete"
                if royalty and royalty["approval_current"]
                else "pending",
                "detail": "Included usage — no payable invoice"
                if royalty and royalty["status"] == "NO_CHARGE"
                else royalty["status"]
                if royalty
                else "No eligible allocation",
            },
            {
                "label": "Invoice",
                "state": "complete" if invoice else "pending",
                "detail": invoice["status"] if invoice else "Not created",
            },
            {
                "label": "Payment",
                "state": "simulated"
                if invoice and invoice["simulated"] and invoice["status"] == "PAID_SIMULATED"
                else "complete"
                if invoice and not invoice["simulated"] and invoice["status"] == "PAID"
                else "pending",
                "detail": invoice["notice"] if invoice else "No payment record",
            },
        ],
    }


def estimate(db, license_, version, command):
    terms = Terms.model_validate(version.terms)
    source = source_evidence(terms, license_.pages)
    prior = (
        sum(
            (
                Decimal(x.calculation["spoken_seconds"])
                for x in db.scalars(select(Royalty).where(Royalty.license_id == license_.id))
            ),
            Decimal(0),
        )
        if terms.billing_basis == "cumulative"
        else Decimal(0)
    )
    try:
        calculation = calculate(terms, command.spoken_seconds, prior)
    except ValueError:
        calculation = None
    if set(source["missing_fields"]) & {
        "included_seconds",
        "additional_rate",
        "billing_basis",
        "currency",
        "additional_usage_permitted",
    }:
        calculation = None
    # Reuse deterministic scope rules without inventing a transcript, attestation,
    # or workflow receipt. Only the scope projection is exposed as a preview.
    result = evaluate(
        terms,
        command.campaign,
        {
            "spoken_seconds": str(command.spoken_seconds),
            "duration_seconds": str(command.spoken_seconds),
            "measurement_uncertain": False,
        },
        ContentFindings(findings=[], uncertainty=[]),
        prior,
        source_review=source,
        preview_only=True,
    )
    scope_rules = {
        "region",
        "medium",
        "language",
        "campaign",
        "start_date",
        "end_date",
        "restricted_category",
        "additional_usage",
    }
    checks = [
        check
        for check in result["rule_checks"]
        if check["rule"] in scope_rules or check.get("kind") in {"metadata", "financial"}
    ]
    reasons = list(source["review_reasons"])
    reasons.extend(
        check["explanation"] for check in checks if check["outcome"] in {"needs_review", "violation"}
    )
    missing = [
        field
        for field in (
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
            "restricted_categories",
        )
        if getattr(terms, field) is None
    ]
    if missing:
        reasons.append("Unknown approved terms: " + ", ".join(missing))
    if terms.restricted_categories and not command.campaign.category:
        reasons.append("Declare the intended campaign category to check the known restrictions.")
    if calculation is None:
        reasons.append(
            "Financial terms or their supporting source clauses require review before a reliable estimate."
        )
    conditions = condition_plan(terms)
    reasons.extend(
        "Condition requires human interpretation: " + condition["text"]
        for condition in conditions
        if condition["kind"] == "human_review"
    )
    scope_status = (
        "RESTRICTED_USAGE"
        if any(check["outcome"] == "violation" for check in checks)
        else "NEEDS_REVIEW"
        if reasons
        else "SCOPE_APPEARS_PERMITTED"
    )
    return {
        "estimate_only": True,
        "notice": ESTIMATE_NOTICE,
        "license_id": license_.id,
        "license_version": version.version,
        "snapshot_at": now(),
        "scope_status": scope_status,
        "calculation": calculation if scope_status != "RESTRICTED_USAGE" else None,
        "checks": checks,
        "reasons": reasons,
        "citations": source["citations"],
        "requirements": [
            "Transcript content has not been evaluated.",
            "Spoken duration is an estimate, not an audio measurement.",
            "Artist identity/use and charge approvals are still required.",
            "Cumulative allowance may change before actual submission.",
            *[check["explanation"] for check in checks if check["outcome"] == "deferred_to_audio_analysis"],
            *[
                "Not verified by this preview: " + condition["text"]
                for condition in conditions
                if condition["kind"] in {"administrative", "content", "human_review"}
            ],
        ],
    }
