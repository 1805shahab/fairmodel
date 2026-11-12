"""Database workflow receipts and conservative overlap signals, separate from AI."""

import re
from difflib import SequenceMatcher
from sqlalchemy import select
from .db import Analysis, Asset, Audit
from .contract_rules import source_evidence
from .schemas import Terms
from .overlap_resolution import usage_state
from .db import Royalty


def tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold())


def overlapping_assets(db, asset, analysis) -> list[dict]:
    matches = []
    words = tokens(analysis.result.get("transcript", ""))
    candidates = db.execute(
        select(Asset, Analysis)
        .join(Analysis, Analysis.asset_id == Asset.id)
        .where(
            Asset.license_id == asset.license_id, Asset.id != asset.id, Asset.created_at < asset.created_at
        )
    ).all()
    for older, other in candidates:
        pcm_hash = analysis.result.get("pcm_sha256")
        if pcm_hash and pcm_hash == other.result.get("pcm_sha256"):
            matches.append(
                {
                    "asset_id": older.id,
                    "kind": "decoded_audio_duplicate",
                    "basis": "identical normalized PCM SHA-256",
                    "needs_review": True,
                }
            )
            continue
        previous = tokens(other.result.get("transcript", ""))
        if min(len(words), len(previous)) < 12:
            continue
        blocks = SequenceMatcher(None, words, previous, autojunk=False).get_matching_blocks()
        match = max(blocks, key=lambda block: block.size)
        longest = match.size
        if longest >= 12 and longest / min(len(words), len(previous)) >= 0.7:
            matches.append(
                {
                    "asset_id": older.id,
                    "kind": "possible_overlap",
                    "basis": "shared transcript sequence",
                    "matched_words": longest,
                    "current_excerpt": excerpt(
                        analysis.result.get("transcript", ""), match.a, min(match.size, 60)
                    ),
                    "related_excerpt": excerpt(
                        other.result.get("transcript", ""), match.b, min(match.size, 60)
                    ),
                    "needs_review": True,
                }
            )
    return matches


def excerpt(text, start, size):
    spans = list(re.finditer(r"\w+", text))
    return text[spans[start].start() : spans[start + size - 1].end()] if size else ""


def evidence_context(db, asset, analysis, license_, version) -> dict:
    upload = db.scalar(
        select(Audit).where(
            Audit.entity_id == asset.id,
            Audit.action == "asset.uploaded",
            Audit.actor_id == asset.studio_id,
            Audit.studio_id == asset.studio_id,
            Audit.artist_id == license_.artist_id,
        )
    )
    request = db.scalar(
        select(Audit).where(
            Audit.entity_id == asset.id,
            Audit.action == "compliance.requested",
            Audit.studio_id == asset.studio_id,
            Audit.artist_id == license_.artist_id,
        )
    )
    signals = overlapping_assets(db, asset, analysis)
    usage = usage_state(db, asset, signals)
    cumulative_conflict = False
    if version.terms.get("billing_basis") == "cumulative":
        for prior in db.scalars(select(Royalty).where(Royalty.license_id == asset.license_id)):
            prior_asset = db.get(Asset, prior.asset_id)
            if usage_state(db, prior_asset, [])["reconciliation_required"]:
                cumulative_conflict = True
                break
    from .passports import review_context

    case_context = review_context(db, asset, usage.get("member_asset_ids", [asset.id]))
    return {
        "source": source_evidence(Terms.model_validate(version.terms), license_.pages),
        "workflow": {
            "submission_recorded": bool(upload and request and analysis),
            "upload_event_id": upload.id if upload else None,
            "review_request_event_id": request.id if request else None,
            "publication_verified": False,
        },
        "overlap": signals,
        "usage": usage,
        "cumulative_reconciliation_required": cumulative_conflict,
        **({"review_cases": case_context} if case_context["cases"] else {}),
    }
