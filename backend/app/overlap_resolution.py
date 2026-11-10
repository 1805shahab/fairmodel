"""Append-only pair decisions and canonical usage groups. No financial history is rewritten."""

from fastapi import HTTPException
from decimal import Decimal, InvalidOperation
from sqlalchemy import select
from .db import Analysis, Asset, Invoice, LicenseVersion, OverlapReview, Royalty, serialize
from .evidence import digest, evidence_hash


def pair_hash(db, asset, related) -> str | None:
    left = db.scalar(select(Analysis).where(Analysis.asset_id == asset.id))
    right = db.scalar(select(Analysis).where(Analysis.asset_id == related.id))
    version = db.scalar(
        select(LicenseVersion).where(
            LicenseVersion.license_id == asset.license_id, LicenseVersion.version == asset.license_version
        )
    )
    if not left or not right or not version or related.license_version != asset.license_version:
        return None
    return digest(
        {
            "current": evidence_hash(asset, left),
            "related": evidence_hash(related, right),
            "terms": version.terms,
        }
    )


def review_graph(db, license_id, replacement=None):
    assets = {a.id: a for a in db.scalars(select(Asset).where(Asset.license_id == license_id))}
    latest = {}
    for row in db.scalars(
        select(OverlapReview)
        .where(OverlapReview.license_id == license_id)
        .order_by(OverlapReview.created_at, OverlapReview.id)
    ):
        latest[(row.asset_id, row.related_asset_id)] = row
    if replacement:
        latest[(replacement.asset_id, replacement.related_asset_id)] = replacement
    valid = {}
    for key, row in latest.items():
        a, b = assets.get(row.asset_id), assets.get(row.related_asset_id)
        valid[key] = bool(a and b and pair_hash(db, a, b) == row.evidence_hash)
    parent = {key: key for key in assets}

    def find(key):
        while parent[key] != key:
            key = parent[key]
        return key

    for key, row in latest.items():
        if valid[key] and row.decision == "SAME_USAGE":
            root_a, root_b = find(row.asset_id), find(row.related_asset_id)
            if root_a != root_b:
                first, second = sorted((root_a, root_b), key=lambda id_: (assets[id_].created_at, id_))
                parent[second] = first
    roots = {key: find(key) for key in assets}
    contradictions = [
        row
        for key, row in latest.items()
        if valid[key]
        and row.decision == "SEPARATE_USAGE"
        and roots[row.asset_id] == roots[row.related_asset_id]
    ]
    return assets, latest, valid, roots, contradictions


def usage_state(db, asset, signals: list[dict]) -> dict:
    assets, latest, valid, roots, contradictions = review_graph(db, asset.license_id)
    canonical_id = roots[asset.id]
    members = sorted(key for key in assets if roots[key] == canonical_id)
    relevant = {
        key: row
        for key, row in latest.items()
        if row.asset_id in members or (row.related_asset_id in members and row.decision == "SAME_USAGE")
    }
    holds = []
    decisions = []
    for key, row in relevant.items():
        state = "current" if valid[key] else "stale"
        decisions.append(
            {
                "id": row.id,
                "asset_id": row.asset_id,
                "related_asset_id": row.related_asset_id,
                "decision": row.decision,
                "state": state,
                "evidence_hash": row.evidence_hash,
            }
        )
        if not valid[key] or row.decision == "UNCERTAIN":
            holds.append(
                {
                    "asset_id": row.asset_id,
                    "related_asset_id": row.related_asset_id,
                    "reason": state if not valid[key] else "uncertain",
                }
            )
    for signal in signals:
        key = (asset.id, signal["asset_id"])
        review = latest.get(key)
        if not review or not valid.get(key):
            if not any(h["asset_id"] == key[0] and h["related_asset_id"] == key[1] for h in holds):
                holds.append(
                    {"asset_id": asset.id, "related_asset_id": signal["asset_id"], "reason": "not_reviewed"}
                )
    allocations = list(db.scalars(select(Royalty).where(Royalty.asset_id.in_(members))))
    reconciliation = (
        bool(contradictions and any(c.asset_id in members for c in contradictions))
        or len(allocations) > 1
        or any(r.asset_id != canonical_id for r in allocations)
    )
    if len(members) > 1:
        measured = {id_: db.scalar(select(Analysis).where(Analysis.asset_id == id_)) for id_ in members}
        try:
            canonical_seconds = Decimal(measured[canonical_id].result["spoken_seconds"])
            if any(Decimal(row.result["spoken_seconds"]) > canonical_seconds for row in measured.values()):
                reconciliation = True
        except (InvalidOperation, TypeError, KeyError, AttributeError):
            reconciliation = True
    return {
        "canonical_asset_id": canonical_id,
        "member_asset_ids": members,
        "disposition": "SAME_USAGE" if canonical_id != asset.id else "CANONICAL_USAGE",
        "decisions": sorted(decisions, key=lambda x: x["id"]),
        "unresolved": holds,
        "reconciliation_required": reconciliation,
        "allocation_permitted": canonical_id == asset.id and not holds and not reconciliation,
    }


def save_review(db, asset, related, actor, body):
    if asset.id == related.id or (asset.created_at, asset.id) <= (related.created_at, related.id):
        raise HTTPException(
            409,
            "Review an excerpt against an earlier related asset. Self-links and circular relationships are not permitted.",
        )
    if (
        asset.license_id != related.license_id
        or asset.license_version != related.license_version
        or asset.studio_id != related.studio_id
    ):
        raise HTTPException(409, "Related assets must use the same assigned license and approved version.")
    fingerprint = pair_hash(db, asset, related)
    if not fingerprint:
        raise HTTPException(409, "Both assets need completed audio analysis under the same approved version.")
    _, latest, _, _, _ = review_graph(db, asset.license_id)
    prior = latest.get((asset.id, related.id))
    if (
        prior
        and prior.decision == body.decision
        and prior.note == body.note
        and prior.evidence_hash == fingerprint
    ):
        return prior, False
    if body.expected_review_id != (prior.id if prior else None):
        raise HTTPException(
            409, "Overlap review changed. Refresh the comparison before saving a new decision."
        )
    row = OverlapReview(
        asset_id=asset.id,
        related_asset_id=related.id,
        license_id=asset.license_id,
        license_version=asset.license_version,
        reviewer_id=actor.id,
        decision=body.decision,
        note=body.note,
        evidence_hash=fingerprint,
        canonical_asset_id=related.id if body.decision == "SAME_USAGE" else asset.id,
        previous_id=prior.id if prior else None,
    )
    # Assign order/id before checking the candidate graph; the row is not committed on a conflict.
    from .db import uid, now

    row.id, row.created_at, row.updated_at = uid(), now(), now()
    _, _, _, roots, conflicts = review_graph(db, asset.license_id, replacement=row)
    if conflicts:
        raise HTTPException(
            409,
            "This decision contradicts an existing same/separate usage relationship. Review those relationships first.",
        )
    row.canonical_asset_id = roots[asset.id]
    db.add(row)
    db.flush()
    return row, True


def comparison(db, asset, analysis, signals):
    assets, latest, valid, _, _ = review_graph(db, asset.license_id)
    related_ids = {signal["asset_id"] for signal in signals}
    related_ids.update(row.related_asset_id for row in latest.values() if row.asset_id == asset.id)

    def summary(item):
        measured = db.scalar(select(Analysis).where(Analysis.asset_id == item.id))
        result = measured.result if measured else {}
        royalty = db.scalar(select(Royalty).where(Royalty.asset_id == item.id))
        invoice = db.scalar(select(Invoice).where(Invoice.royalty_id == royalty.id)) if royalty else None
        return {
            "id": item.id,
            "name": item.original_name,
            "license_id": item.license_id,
            "license_version": item.license_version,
            "campaign_name": item.campaign.get("name"),
            "duration_seconds": result.get("duration_seconds"),
            "spoken_seconds": result.get("spoken_seconds"),
            "transcript": result.get("transcript", ""),
            "royalty_status": royalty.status if royalty else None,
            "invoice_status": invoice.status if invoice else None,
        }

    pairs = []
    for id_ in sorted(related_ids):
        related = assets.get(id_)
        if not related:
            continue
        key = (asset.id, id_)
        row = latest.get(key)
        history = [
            serialize(r)
            for r in db.scalars(
                select(OverlapReview)
                .where(OverlapReview.asset_id == asset.id, OverlapReview.related_asset_id == id_)
                .order_by(OverlapReview.created_at.desc(), OverlapReview.id.desc())
            )
        ]
        pairs.append(
            {
                "current": summary(asset),
                "related": summary(related),
                "evidence": next(
                    (s for s in signals if s["asset_id"] == id_),
                    {"kind": "artist_identified", "basis": "recorded artist review"},
                ),
                "review": {**serialize(row), "state": "current" if valid[key] else "stale"} if row else None,
                "history": history,
            }
        )
    incoming = [
        {"asset_id": row.asset_id, "decision": row.decision, "state": "current" if valid[key] else "stale"}
        for key, row in latest.items()
        if row.related_asset_id == asset.id
    ]
    return {
        "asset_id": asset.id,
        "pairs": pairs,
        "incoming": incoming,
        "usage": usage_state(db, asset, signals),
    }
