"""Stable business evidence; provider request timestamps do not change reviewed usage."""

import hashlib
import json


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def analysis_evidence(result: dict) -> dict:
    fields = (
        "duration_seconds",
        "spoken_seconds",
        "format",
        "codec",
        "sample_rate",
        "channels",
        "speech_segments",
        "transcript",
        "provider",
        "vad",
        "measurement_uncertain",
        "demo_fixture",
        "pcm_sha256",
        "language",
    )
    selected = {field: result.get(field) for field in fields}
    selected["timestamps"] = [
        {key: segment.get(key) for key in ("start", "end", "text")}
        for segment in result.get("timestamps", [])
    ]
    selected["speaker"] = {
        key: result.get("speaker", {}).get(key) for key in ("status", "model", "score", "threshold")
    }
    return selected


def evidence_hash(asset, analysis, legacy=False) -> str:
    return digest(
        {
            "asset_id": asset.id,
            "file_hash": asset.file_hash,
            "license_id": asset.license_id,
            "license_version": asset.license_version,
            "campaign": asset.campaign,
            "analysis": analysis.result if legacy else analysis_evidence(analysis.result),
        }
    )


def content_inputs_hash(terms, transcript, campaign, fixture):
    from .contract_rules import condition_plan

    return digest(
        {
            "transcript": transcript,
            "restrictions": terms.restricted_categories,
            "conditions": [c for c in condition_plan(terms) if c["kind"] == "content"],
            "category": campaign.get("category"),
            "fixture": fixture,
        }
    )
