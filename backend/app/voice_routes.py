"""Artist grants and studio speech jobs. No financial side effects."""

import hashlib
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import audio, voice_generation, fish_generation
from .config import settings
from .db import Asset, License, LicenseVersion, ReferenceVoice, SpeechGeneration, VoiceGrant, get_session, now
from .evidence import digest
from .main import Actor, audit, owned, require_role, save_upload
from .passports import estimate
from .schemas import Campaign, EstimateCommand, Schema

router = APIRouter(prefix="/api", tags=["Licensed voice generation"])
DB = Annotated[Session, Depends(get_session, scope="function")]


class GenerationCommand(Schema):
    provider: Literal["gemini", "fish"] = "gemini"
    grant_id: str = Field(min_length=1, max_length=64)
    request_key: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    script: str = Field(min_length=10, max_length=4000)
    campaign: Campaign
    confirm_provider_use: bool


def current_grant(db, grant):
    license_ = db.get(License, grant.license_id)
    version = db.scalar(
        select(LicenseVersion).where(
            LicenseVersion.license_id == grant.license_id,
            LicenseVersion.version == grant.license_version,
        )
    )
    if (
        grant.revoked_at
        or not license_
        or license_.status != "ACTIVE"
        or license_.version != grant.license_version
        or not version
        or version.approved_by != grant.artist_id
        or license_.artist_id != grant.artist_id
        or license_.studio_id != grant.studio_id
    ):
        raise HTTPException(
            409,
            "The artist's generation grant is revoked or its approved license version is no longer current.",
        )
    reference = db.get(ReferenceVoice, grant.reference_id)
    if not reference or reference.artist_id != grant.artist_id or not reference.consent:
        raise HTTPException(409, "An owned consented reference recording is required.")
    return license_, version, reference


def grant_view(db, grant):
    try:
        current_grant(db, grant)
        status = "ACTIVE"
    except HTTPException:
        status = "REVOKED" if grant.revoked_at else "STALE"
    license_ = db.get(License, grant.license_id)
    return {
        key: getattr(grant, key)
        for key in (
            "id",
            "reference_id",
            "license_id",
            "license_version",
            "artist_id",
            "studio_id",
            "created_at",
            "revoked_at",
            "note",
        )
    } | {
        "status": status,
        "license_title": license_.title,
        "provider": grant.provider,
        "scope": fish_generation.CONSENT_NOTE
        if grant.provider == "fish"
        else "Adult speaker explicitly consented to reference/consent transfer to Google and licensed studio generation. Final asset authorization is separate.",
    }


def job_view(job):
    return {
        key: getattr(job, key)
        for key in (
            "id",
            "grant_id",
            "studio_id",
            "request_key",
            "status",
            "asset_id",
            "created_at",
            "updated_at",
            "error",
            "receipt",
            "provider",
        )
    }


@router.get("/references/{id_}/audio")
def reference_audio(id_: str, db: DB, actor: Actor):
    require_role(actor, "artist")
    reference = owned(db, ReferenceVoice, id_, actor)
    path = Path(reference.path)
    if not path.is_file():
        raise HTTPException(404, "The stored reference file is unavailable.")
    return FileResponse(
        path,
        media_type={".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4"}.get(path.suffix.lower()),
        headers={"Cache-Control": "no-store"},
    )


@router.get("/voice-grants")
def grants(db: DB, actor: Actor):
    owner = VoiceGrant.artist_id if actor.role == "artist" else VoiceGrant.studio_id
    return [
        grant_view(db, grant)
        for grant in db.scalars(
            select(VoiceGrant).where(owner == actor.id).order_by(VoiceGrant.created_at.desc())
        )
    ]


@router.post("/voice-grants", status_code=201)
def create_grant(
    db: DB,
    actor: Actor,
    reference_id: str = Form(),
    license_id: str = Form(),
    owner_confirmed: bool = Form(),
    provider_transfer_consent: bool = Form(),
    note: str = Form(min_length=10, max_length=2000),
    file: UploadFile | None = File(default=None),
    provider: Literal["gemini", "fish"] = Form(default="gemini"),
    reference_text: str = Form(default="", max_length=4000),
    provider_policy_ack: bool = Form(default=False),
):
    require_role(actor, "artist")
    if not owner_confirmed or not provider_transfer_consent or len(note.strip()) < 10:
        raise HTTPException(
            422,
            "Adult speaker ownership, selected-provider replication/transfer consent and a meaningful review note are required.",
        )
    reference = owned(db, ReferenceVoice, reference_id, actor)
    license_ = owned(db, License, license_id, actor)
    version = db.scalar(
        select(LicenseVersion).where(
            LicenseVersion.license_id == license_id, LicenseVersion.version == license_.version
        )
    )
    if license_.status != "ACTIVE" or not version or version.approved_by != actor.id:
        raise HTTPException(409, "Approve the contract before granting studio voice generation.")
    voice_generation.checked_recording(Path(reference.path), 10, 30, "Selected artist reference sample")
    if provider == "fish":
        if not provider_policy_ack or not reference_text.strip():
            raise HTTPException(
                422,
                "Fish requires the exact artist-reviewed reference transcript and acknowledgment of provider retention/terms and no DPA guarantee.",
            )
        path, consent_hash = Path(reference.path), reference.file_hash
    else:
        if file is None:
            raise HTTPException(422, "Google Gemini requires the separate speaker consent recording.")
        path, consent_hash = save_upload(file, {".wav", ".mp3", ".m4a"})
    keep = False
    try:
        if provider == "gemini":
            voice_generation.checked_recording(path, 2, 30, "Uploaded consent recording")
        existing = db.scalar(
            select(VoiceGrant).where(
                VoiceGrant.reference_id == reference_id,
                VoiceGrant.license_id == license_id,
                VoiceGrant.license_version == license_.version,
                VoiceGrant.provider == provider,
            )
        )
        if existing:
            if (
                existing.consent_hash != consent_hash
                or existing.note != note.strip()
                or existing.revoked_at
                or (provider == "fish" and existing.reference_text != reference_text.strip())
            ):
                raise HTTPException(
                    409,
                    "A different or revoked grant already exists for this reference/version. Upload a new reference for a new grant; history is preserved.",
                )
            return grant_view(db, existing)
        grant = VoiceGrant(
            reference_id=reference_id,
            license_id=license_id,
            license_version=license_.version,
            artist_id=actor.id,
            studio_id=license_.studio_id,
            consent_path=str(path),
            consent_hash=consent_hash,
            note=note.strip(),
            provider=provider,
            reference_text=reference_text.strip() if provider == "fish" else None,
        )
        db.add(grant)
        db.flush()
        audit(
            db,
            actor,
            license_,
            "voice.generation_granted",
            grant.id,
            {
                "reference_id": reference_id,
                "license_version": license_.version,
                "provider": provider,
                "consent_policy": fish_generation.POLICY if provider == "fish" else "gemini-recorded-consent",
                "consent_sha256": consent_hash,
            },
        )
        result = grant_view(db, grant)
        keep = True
        return result
    finally:
        if not keep and provider == "gemini":
            path.unlink(missing_ok=True)


@router.post("/voice-grants/{id_}/revoke")
def revoke_grant(id_: str, db: DB, actor: Actor):
    require_role(actor, "artist")
    grant = owned(db, VoiceGrant, id_, actor)
    if not grant.revoked_at:
        grant.revoked_at = now()
        audit(db, actor, owned(db, License, grant.license_id, actor), "voice.generation_revoked", grant.id)
    return grant_view(db, grant)


@router.get("/generations")
def generations(db: DB, actor: Actor):
    query = select(SpeechGeneration).join(VoiceGrant)
    owner = VoiceGrant.artist_id if actor.role == "artist" else SpeechGeneration.studio_id
    return [
        job_view(job)
        for job in db.scalars(query.where(owner == actor.id).order_by(SpeechGeneration.created_at.desc()))
    ]


@router.post("/generations", status_code=201)
def generate(body: GenerationCommand, db: DB, actor: Actor):
    require_role(actor, "studio")
    if not body.confirm_provider_use:
        raise HTTPException(
            422,
            "Confirm this explicit selected-provider replication/TTS request and provider processing terms.",
        )
    # Retain the original Gemini input hash for saved legacy request keys.
    excluded = {"request_key", "confirm_provider_use"} | (
        {"provider"} if body.provider == "gemini" else set()
    )
    inputs = digest(body.model_dump(mode="json", exclude=excluded))
    existing = db.scalar(
        select(SpeechGeneration).where(
            SpeechGeneration.studio_id == actor.id, SpeechGeneration.request_key == body.request_key
        )
    )
    if existing:
        if existing.input_hash != inputs:
            raise HTTPException(409, "Request key already belongs to different generation inputs.")
        return job_view(existing)
    adapter = fish_generation if body.provider == "fish" else voice_generation
    adapter.require_available()
    grant = owned(db, VoiceGrant, body.grant_id, actor)
    if grant.provider != body.provider:
        raise HTTPException(
            409,
            "This artist grant authorizes a different provider. Obtain explicit consent for the selected provider; no provider switch is allowed.",
        )
    license_, version, reference = current_grant(db, grant)
    # Scope restrictions remain deterministic. Generation does not establish compliance.
    preview = estimate(
        db, license_, version, EstimateCommand(campaign=body.campaign, spoken_seconds=Decimal(0))
    )
    if preview["scope_status"] != "SCOPE_APPEARS_PERMITTED":
        raise HTTPException(
            409,
            "Declared campaign scope requires correction/review before generation: "
            + "; ".join(
                dict.fromkeys(
                    preview["reasons"]
                    + [
                        x["explanation"]
                        for x in preview["checks"]
                        if x["outcome"] in {"needs_review", "violation"}
                    ]
                )
            ),
        )
    source, consent = Path(reference.path), Path(grant.consent_path)
    for path, expected in ((source, reference.file_hash), (consent, grant.consent_hash)):
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise HTTPException(
                409, "Reference or consent audio is missing/changed. Obtain a new artist generation grant."
            )
    voice_generation.checked_recording(source, 10, 30, "Selected artist reference sample")
    if body.provider == "gemini":
        voice_generation.checked_recording(consent, 2, 30, "Saved consent recording")
    elif not grant.reference_text:
        raise HTTPException(409, "The Fish grant has no artist-reviewed reference transcript.")
    campaign = body.campaign.model_dump(mode="json") | {
        "generation_provider": "Fish Audio / inline reference cloning"
        if body.provider == "fish"
        else "Gemini TTS / replicated voice"
    }
    job = SpeechGeneration(
        grant_id=grant.id,
        studio_id=actor.id,
        request_key=body.request_key,
        input_hash=inputs,
        script=body.script,
        campaign=campaign,
        provider=body.provider,
    )
    db.add(job)
    db.flush()
    job_id = job.id
    audit(
        db,
        actor,
        license_,
        "voice.generation_requested",
        job_id,
        {"grant_id": grant.id, "license_version": grant.license_version, "provider": body.provider},
    )
    # Persist intent before provider calls and release SQLite's writer lock.
    db.commit()
    output = settings.storage_dir / f"{job_id}-generated.wav"
    try:
        if body.provider == "fish":
            data, receipt = fish_generation.synthesize(source, grant.reference_text, body.script, job_id)
        else:
            data, receipt = voice_generation.synthesize(source, consent, body.script, job_id)
        voice_generation.validate_wav(data, provider="Fish Audio" if body.provider == "fish" else "Gemini")
        output.write_bytes(data)
        audio.probe(output)
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        db.expire_all()
        job = db.get(SpeechGeneration, job_id)
        grant = db.get(VoiceGrant, job.grant_id)
        license_, current_version, reference = current_grant(db, grant)
        # Recheck scope and permission after remote processing, before persisting output.
        refreshed = estimate(
            db, license_, current_version, EstimateCommand(campaign=body.campaign, spoken_seconds=Decimal(0))
        )
        if grant.provider != body.provider or refreshed["scope_status"] != "SCOPE_APPEARS_PERMITTED":
            raise HTTPException(
                409, "Generation permission or campaign eligibility changed during provider processing."
            )
        # A revocation/version/input change during the remote call cannot create an asset.
        for path, expected in ((source, reference.file_hash), (consent, grant.consent_hash)):
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise HTTPException(409, "Generation inputs changed while the provider was running.")
        file_hash = hashlib.sha256(data).hexdigest()
        asset = db.scalar(
            select(Asset).where(Asset.license_id == grant.license_id, Asset.file_hash == file_hash)
        )
        if asset and asset.campaign != campaign:
            raise HTTPException(
                409,
                "Generated output duplicates an existing recording with different campaign metadata; resolve it on the existing submission.",
            )
        if not asset:
            asset = Asset(
                license_id=grant.license_id,
                studio_id=actor.id,
                license_version=grant.license_version,
                campaign=campaign,
                path=str(output),
                file_hash=file_hash,
                original_name=f"{body.provider}-ad-{job_id[:8]}.wav",
            )
            db.add(asset)
            db.flush()
            audit(
                db,
                actor,
                license_,
                "asset.uploaded",
                asset.id,
                {"sha256": file_hash, "generation_id": job_id, "reference_id": grant.reference_id},
            )
        else:
            output.unlink(missing_ok=True)
        job.status, job.asset_id, job.receipt = "SUCCEEDED", asset.id, receipt
        audit(
            db,
            actor,
            license_,
            "voice.generation_succeeded",
            asset.id,
            {"generation_id": job_id, "grant_id": grant.id, "receipt": receipt},
        )
        db.flush()
        return job_view(job)
    except Exception as error:
        db.rollback()
        output.unlink(missing_ok=True)
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        job = db.get(SpeechGeneration, job_id)
        job.status = "FAILED"
        if isinstance(error, voice_generation.VoiceProviderFailure):
            job.receipt = {
                "service": "Gemini TTS",
                "mode": "live",
                "requested_model": settings.gemini_tts_model,
                "requested_replication_model": settings.gemini_voice_replication_model,
                "failed_at": now(),
                "failure": error.diagnostic,
            }
        elif body.provider == "fish":
            job.receipt = {
                "provider": "fish",
                "service": "Fish Audio",
                "mode": "live",
                "requested_model": fish_generation.MODEL,
                "failed_at": now(),
                "failure": error.diagnostic
                if isinstance(error, (fish_generation.FishProviderFailure, fish_generation.FishAudioFailure))
                else {"stage": "output_validation_or_persistence", "category": "LOCAL_FAILURE"},
            }
        job.error = (
            error.detail
            if isinstance(error, HTTPException)
            else "Generation output could not be saved. No automatic retry or fixture fallback occurred."
        )
        db.commit()
        raise HTTPException(
            error.status_code if isinstance(error, HTTPException) else 502,
            f"Generation {job_id}: {job.error}",
        ) from None
