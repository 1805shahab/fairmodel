import hashlib
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pypdf import PdfReader
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from . import ai, audio
from .config import settings
from .db import (
    Analysis,
    Asset,
    Audit,
    Base,
    Invoice,
    License,
    LicenseVersion,
    PaymentEvent,
    Persona,
    ReferenceVoice,
    Report,
    Royalty,
    engine,
    get_session,
    now,
    serialize,
    uid,
)
from .payments import PAYMENT_NOTICE, provider
from .royalties import evaluate
from .schemas import (
    AnalysisResponse,
    AnalyticsResponse,
    AssetResponse,
    AuditResponse,
    Campaign,
    Decision,
    ExtractionCommand,
    InvoiceResponse,
    LicenseCreate,
    LicenseResponse,
    PaymentCommand,
    PersonaResponse,
    ReferenceResponse,
    ReportResponse,
    ReviewTerms,
    RoyaltyResponse,
    Terms,
)

DB = Annotated[Session, Depends(get_session)]


def seed(session: Session):
    for id_, role, name, email in [
        ("artist_demo", "artist", "Amara Reed", "amara@example.test"),
        ("studio_demo", "studio", "Northstar Studio", "studio@example.test"),
    ]:
        if not session.get(Persona, id_):
            session.add(Persona(id=id_, role=role, name=name, email=email))


@asynccontextmanager
async def lifespan(_):
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    with engine.connect() as connection:
        version = connection.exec_driver_sql("PRAGMA user_version").scalar()
        if version not in (0, 1):
            raise RuntimeError("Unsupported database schema version. Back up the database before migration.")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA user_version=1")
    with Session(engine) as session:
        seed(session)
        session.commit()
    yield


app = FastAPI(
    title="FairModel",
    version="0.1.0",
    lifespan=lifespan,
    description="Local demo personas; simulated payments only. No production authentication.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Content-Type", "X-Demo-Persona"],
)


@app.middleware("http")
async def private_responses(request, call_next):
    # A request-size guard also covers multipart overhead. Upload handlers enforce exact file limits.
    length = request.headers.get("content-length")
    if length:
        try:
            if int(length) > (settings.max_upload_mb + 1) * 1024 * 1024:
                return JSONResponse(
                    {"detail": "Upload exceeds the 24 MiB development limit."}, status_code=413
                )
        except ValueError:
            return JSONResponse({"detail": "Invalid Content-Length."}, status_code=400)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def current_actor(db: DB, x_demo_persona: Annotated[str | None, Header()] = None) -> Persona:
    actor = db.get(Persona, x_demo_persona or "")
    if not actor:
        raise HTTPException(
            401, "Select a demo persona using X-Demo-Persona. This is not production authentication."
        )
    return actor


Actor = Annotated[Persona, Depends(current_actor)]


def require_role(actor: Persona, role: str):
    if actor.role != role:
        raise HTTPException(403, f"This action requires the {role} demo persona.")


def owned(db: Session, model, id_: str, actor: Persona):
    item = db.get(model, id_)
    if not item:
        raise HTTPException(404, "Record not found.")
    if actor.id not in (getattr(item, "artist_id", None), getattr(item, "studio_id", None)):
        raise HTTPException(404, "Record not found.")
    return item


def asset_owned(db: Session, id_: str, actor: Persona) -> tuple[Asset, License]:
    asset = db.get(Asset, id_)
    if not asset:
        raise HTTPException(404, "Asset not found.")
    return asset, owned(db, License, asset.license_id, actor)


def audit(db, actor, license_, action, entity_id, detail=None):
    db.add(
        Audit(
            actor_id=actor.id,
            artist_id=license_.artist_id,
            studio_id=license_.studio_id,
            action=action,
            entity_id=entity_id,
            detail=detail or {},
        )
    )


def public(item) -> dict:
    result = serialize(item)
    for key in ("path", "contract_path", "normalized_path"):
        result.pop(key, None)
    return result


def save_upload(file: UploadFile, allowed: set[str]) -> tuple[Path, str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(422, "Unsupported file extension.")
    path = settings.storage_dir / f"{uid()}{suffix}"
    digest = hashlib.sha256()
    total = 0
    try:
        with path.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                total += len(chunk)
                if total > settings.max_upload_mb * 1024 * 1024:
                    raise HTTPException(413, "File exceeds the 24 MiB limit.")
                digest.update(chunk)
                output.write(chunk)
        if not total:
            raise HTTPException(422, "The uploaded file is empty.")
        return path, digest.hexdigest()
    except Exception:
        path.unlink(missing_ok=True)
        raise


def license_editable(license_):
    if license_.status == "ACTIVE":
        raise HTTPException(
            409, "An approved license version is immutable. Create a new agreement for revised terms."
        )


@app.get("/health")
def health():
    return {"status": "ok", "payment_provider": "mock", "demo_auth": True}


@app.get("/api/integrations")
def integrations(actor: Actor):
    return {
        "demo_mode": True,
        "payment_provider": "mock",
        "payment_notice": PAYMENT_NOTICE,
        "gemini": {
            "configured": bool(settings.gemini_api_key.get_secret_value()),
            "model": settings.gemini_model,
        },
        "groq": {
            "configured": bool(settings.groq_api_key.get_secret_value()),
            "model": settings.groq_whisper_model,
        },
        "audio_tools": audio.availability(),
        "speaker_verification": {
            "enabled": settings.enable_speaker_verification,
            "status": "optional worker required" if settings.enable_speaker_verification else "disabled",
        },
        "paypal": "Deferred — account access and explicit authorization required",
        "schema_version": 1,
        "fixtures_available": bool(ai.fixture_manifest()),
    }


@app.get("/api/personas", response_model=list[PersonaResponse])
def personas(db: DB):
    return [public(x) for x in db.scalars(select(Persona))]


@app.get("/api/artists", response_model=list[PersonaResponse])
def artists(db: DB, actor: Actor):
    return [public(x) for x in db.scalars(select(Persona).where(Persona.role == "artist"))]


@app.get("/api/studios", response_model=list[PersonaResponse])
def studios(db: DB, actor: Actor):
    return [public(x) for x in db.scalars(select(Persona).where(Persona.role == "studio"))]


@app.get("/api/licenses", response_model=list[LicenseResponse])
def licenses(db: DB, actor: Actor):
    return [
        public(x)
        for x in db.scalars(
            select(License)
            .where(or_(License.artist_id == actor.id, License.studio_id == actor.id))
            .order_by(License.created_at.desc())
        )
    ]


@app.post("/api/licenses", response_model=LicenseResponse, status_code=201)
def create_license(body: LicenseCreate, db: DB, actor: Actor):
    require_role(actor, "artist")
    studio = db.get(Persona, body.studio_id)
    if not studio or studio.role != "studio":
        raise HTTPException(422, "Choose an existing studio.")
    license_ = License(
        title=body.title, artist_id=actor.id, studio_id=body.studio_id, terms=Terms().model_dump(mode="json")
    )
    db.add(license_)
    db.flush()
    audit(db, actor, license_, "license.created", license_.id)
    return public(license_)


@app.get("/api/licenses/{id_}", response_model=LicenseResponse)
def get_license(id_: str, db: DB, actor: Actor):
    license_ = owned(db, License, id_, actor)
    return {
        **public(license_),
        "versions": [
            public(x) for x in db.scalars(select(LicenseVersion).where(LicenseVersion.license_id == id_))
        ],
    }


@app.post("/api/licenses/{id_}/contract", response_model=LicenseResponse)
def upload_contract(id_: str, db: DB, actor: Actor, file: UploadFile = File()):
    require_role(actor, "artist")
    license_ = owned(db, License, id_, actor)
    license_editable(license_)
    path, digest = save_upload(file, {".pdf"})
    try:
        with path.open("rb") as source:
            if source.read(5) != b"%PDF-":
                raise ValueError("Not a PDF")
        reader = PdfReader(path)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 30:
            raise ValueError("Encrypted or excessive pages")
        pages = [{"page": i + 1, "text": page.extract_text() or ""} for i, page in enumerate(reader.pages)]
        size = sum(len(x["text"]) for x in pages)
        if not 20 <= size <= 100000:
            raise ValueError("No text or too much text")
    except Exception:
        path.unlink(missing_ok=True)
        raise HTTPException(
            422,
            "Upload an unencrypted text PDF (1–30 pages, 20–100,000 text characters). Scanned PDFs need OCR first.",
        ) from None
    license_.contract_path, license_.contract_hash, license_.pages = str(path), digest, pages
    license_.status, license_.error, license_.extraction_provider = "DRAFT", None, "not_run"
    license_.terms = Terms().model_dump(mode="json")
    license_.version += 1
    db.flush()
    audit(db, actor, license_, "contract.uploaded", id_, {"pages": len(pages), "sha256": digest})
    # Old files remain private until explicit local retention cleanup; do not risk rollback breaking prior records.
    return public(license_)


@app.get("/api/licenses/{id_}/contract")
def download_contract(id_: str, db: DB, actor: Actor):
    license_ = owned(db, License, id_, actor)
    if not license_.contract_path:
        raise HTTPException(404, "No contract uploaded.")
    return FileResponse(
        license_.contract_path,
        media_type="application/pdf",
        filename="license-agreement.pdf",
        content_disposition_type="inline",
    )


@app.post("/api/licenses/{id_}/extract", response_model=LicenseResponse)
def extract(id_: str, body: ExtractionCommand, db: DB, actor: Actor):
    require_role(actor, "artist")
    license_ = owned(db, License, id_, actor)
    license_editable(license_)
    if not license_.contract_path:
        raise HTTPException(409, "Upload a PDF first.")
    try:
        terms, source = ai.extract_contract(
            Path(license_.contract_path), license_.pages, body.use_demo_fixture
        )
    except HTTPException as exc:
        license_.error = str(exc.detail)
        audit(db, actor, license_, "contract.extraction_failed", id_, {"status_code": exc.status_code})
        db.commit()
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    license_.terms, license_.extraction_provider = terms.model_dump(mode="json"), source
    license_.status, license_.error = "REVIEW", None
    license_.version += 1
    db.flush()
    audit(db, actor, license_, "contract.extracted", id_, {"provider": source})
    return public(license_)


def review_license(id_, body, db, actor, activate):
    require_role(actor, "artist")
    license_ = owned(db, License, id_, actor)
    license_editable(license_)
    if not license_.contract_path:
        raise HTTPException(409, "A source contract is required before reviewing terms.")
    if body.expected_version != license_.version:
        raise HTTPException(409, "Terms changed in another session. Refresh and review again.")
    terms = body.terms
    unknown = [x for x in Terms.model_fields if getattr(terms, x) is None]
    if activate and (unknown or terms.ambiguities) and not body.acknowledge_unknowns:
        raise HTTPException(
            422, "Resolve unknowns/ambiguities or explicitly acknowledge human-review-only activation."
        )
    license_.terms = terms.model_dump(mode="json")
    license_.version += 1
    license_.status = "ACTIVE" if activate else "REVIEW"
    if activate:
        license_.approved_at = now()
        db.add(
            LicenseVersion(
                license_id=id_, version=license_.version, terms=license_.terms, approved_by=actor.id
            )
        )
    db.flush()
    audit(
        db,
        actor,
        license_,
        "license.approved" if activate else "license.terms_edited",
        id_,
        {"note": body.note, "version": license_.version, "unknowns_acknowledged": body.acknowledge_unknowns},
    )
    return public(license_)


@app.put("/api/licenses/{id_}/terms", response_model=LicenseResponse)
def save_terms(id_: str, body: ReviewTerms, db: DB, actor: Actor):
    return review_license(id_, body, db, actor, False)


@app.post("/api/licenses/{id_}/approve", response_model=LicenseResponse)
def approve_license(id_: str, body: ReviewTerms, db: DB, actor: Actor):
    return review_license(id_, body, db, actor, True)


@app.get("/api/references", response_model=list[ReferenceResponse])
def references(db: DB, actor: Actor):
    require_role(actor, "artist")
    return [public(x) for x in db.scalars(select(ReferenceVoice).where(ReferenceVoice.artist_id == actor.id))]


@app.post("/api/references", response_model=ReferenceResponse, status_code=201)
def upload_reference(db: DB, actor: Actor, consent: bool = Form(), file: UploadFile = File()):
    require_role(actor, "artist")
    if not consent:
        raise HTTPException(
            422, "Explicit consent to store and compare this reference recording is required."
        )
    path, digest = save_upload(file, {".wav", ".mp3", ".m4a"})
    try:
        metadata = audio.probe(path)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    reference = ReferenceVoice(
        artist_id=actor.id, path=str(path), file_hash=digest, consent=True, metadata_json=metadata
    )
    db.add(reference)
    db.flush()
    db.add(
        Audit(
            actor_id=actor.id,
            artist_id=actor.id,
            studio_id="",
            action="reference.consented_upload",
            entity_id=reference.id,
            detail={"sha256": digest},
        )
    )
    return public(reference)


@app.get("/api/assets", response_model=list[AssetResponse])
def assets(db: DB, actor: Actor):
    query = (
        select(Asset).join(License).where(or_(License.artist_id == actor.id, License.studio_id == actor.id))
    )
    return [public(x) for x in db.scalars(query.order_by(Asset.created_at.desc()))]


@app.post("/api/assets", response_model=AssetResponse, status_code=201)
def upload_asset(
    db: DB, actor: Actor, license_id: str = Form(), campaign: str = Form(), file: UploadFile = File()
):
    require_role(actor, "studio")
    license_ = owned(db, License, license_id, actor)
    if license_.status != "ACTIVE":
        raise HTTPException(409, "An artist-approved active license is required.")
    try:
        metadata = Campaign.model_validate_json(campaign)
    except ValueError:
        raise HTTPException(422, "Invalid campaign metadata. Include a name and intended_use_date.") from None
    path, digest = save_upload(file, {".wav", ".mp3", ".m4a"})
    existing = db.scalar(select(Asset).where(Asset.license_id == license_id, Asset.file_hash == digest))
    if existing:
        path.unlink(missing_ok=True)
        return JSONResponse({**public(existing), "duplicate": True}, status_code=200)
    try:
        audio.probe(path)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    asset = Asset(
        license_id=license_id,
        studio_id=actor.id,
        license_version=license_.version,
        campaign=metadata.model_dump(mode="json"),
        path=str(path),
        file_hash=digest,
        original_name=Path(file.filename or "audio").name[:200],
    )
    db.add(asset)
    db.flush()
    audit(db, actor, license_, "asset.uploaded", asset.id, {"sha256": digest})
    return public(asset)


@app.get("/api/assets/{id_}", response_model=AssetResponse)
def get_asset(id_: str, db: DB, actor: Actor):
    asset, _ = asset_owned(db, id_, actor)
    analysis = db.scalar(select(Analysis).where(Analysis.asset_id == id_))
    report = db.scalar(select(Report).where(Report.asset_id == id_))
    royalty = db.scalar(select(Royalty).where(Royalty.asset_id == id_))
    return {
        **public(asset),
        "analysis": public(analysis) if analysis else None,
        "report": public(report) if report else None,
        "royalty": public(royalty) if royalty else None,
    }


@app.patch("/api/assets/{id_}/campaign", response_model=AssetResponse)
def correct_campaign(id_: str, body: Campaign, db: DB, actor: Actor):
    require_role(actor, "studio")
    asset, license_ = asset_owned(db, id_, actor)
    if db.scalar(select(Royalty).where(Royalty.asset_id == id_)):
        raise HTTPException(
            409, "Usage with an allocated royalty is immutable. Contact the artist for review."
        )
    asset.campaign = body.model_dump(mode="json")
    report = db.scalar(select(Report).where(Report.asset_id == id_))
    if report:
        db.delete(report)
    asset.status = "ANALYZED" if db.scalar(select(Analysis).where(Analysis.asset_id == id_)) else "UPLOADED"
    audit(db, actor, license_, "campaign.corrected", id_)
    db.flush()
    return public(asset)


@app.get("/api/assets/{id_}/audio")
def playback(id_: str, db: DB, actor: Actor):
    asset, _ = asset_owned(db, id_, actor)
    path = Path(asset.normalized_path or asset.path)
    media_type = {".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4"}.get(path.suffix)
    return FileResponse(path, media_type=media_type)


@app.post("/api/assets/{id_}/analyze", response_model=AnalysisResponse)
def analyze_audio(id_: str, body: ExtractionCommand, db: DB, actor: Actor):
    require_role(actor, "studio")
    asset, license_ = asset_owned(db, id_, actor)
    existing = db.scalar(select(Analysis).where(Analysis.asset_id == id_))
    if existing:
        return public(existing)
    normalized = settings.storage_dir / f"{asset.id}-normalized.wav"
    try:
        metadata = audio.probe(Path(asset.path))
        audio.normalize(Path(asset.path), normalized)
        speech = audio.speech_activity(normalized)
        transcript = ai.transcribe(normalized, Path(asset.path), body.use_demo_fixture)
    except HTTPException as exc:
        asset.status, asset.error = "FAILED", str(exc.detail)
        audit(db, actor, license_, "analysis.failed", id_, {"status_code": exc.status_code})
        db.commit()
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    asset.status, asset.error, asset.normalized_path = "ANALYZED", None, str(normalized)
    speaker = {
        "status": "unavailable" if settings.enable_speaker_verification else "disabled",
        "model": None,
        "score": None,
        "note": "Experimental worker has not run. No similarity score is claimed.",
    }
    analysis = Analysis(
        asset_id=id_,
        result={
            **metadata,
            **speech,
            **transcript,
            "speaker": speaker,
            "demo_fixture": body.use_demo_fixture,
        },
    )
    db.add(analysis)
    db.flush()
    audit(
        db,
        actor,
        license_,
        "analysis.completed",
        id_,
        {"provider": transcript["provider"], "vad": speech["vad"]},
    )
    return public(analysis)


@app.post("/api/assets/{id_}/evaluate", response_model=ReportResponse)
def evaluate_asset(id_: str, body: ExtractionCommand, db: DB, actor: Actor):
    asset, license_ = asset_owned(db, id_, actor)
    existing = db.scalar(select(Report).where(Report.asset_id == id_))
    if existing:
        return public(existing)
    analysis = db.scalar(select(Analysis).where(Analysis.asset_id == id_))
    if not analysis:
        raise HTTPException(409, "Analyze the audio before evaluating compliance.")
    version = db.scalar(
        select(LicenseVersion).where(
            LicenseVersion.license_id == license_.id, LicenseVersion.version == asset.license_version
        )
    )
    if not version:
        raise HTTPException(409, "Approved contract snapshot unavailable. Human review required.")
    terms = Terms.model_validate(version.terms)
    if body.use_demo_fixture and not analysis.result.get("demo_fixture"):
        raise HTTPException(422, "Live transcripts cannot use fixture content assessment.")
    try:
        findings, source = ai.content_findings(terms, analysis.result["transcript"], body.use_demo_fixture)
    except HTTPException as exc:
        asset.error = str(exc.detail)
        audit(db, actor, license_, "compliance.failed", id_, {"status_code": exc.status_code})
        db.commit()
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    prior_entries = list(db.scalars(select(Royalty).where(Royalty.license_id == license_.id)))
    prior = sum((Decimal(x.calculation["spoken_seconds"]) for x in prior_entries), Decimal(0))
    result = evaluate(
        terms,
        Campaign.model_validate(asset.campaign),
        analysis.result,
        findings,
        prior,
        analysis.result.get("speaker"),
    )
    result.update(
        {
            "provider": source,
            "license_version": asset.license_version,
            "source_pages": [x.model_dump() for x in terms.evidence],
        }
    )
    report = Report(asset_id=id_, status=result["status"], result=result)
    db.add(report)
    if result["status"] in {"COMPLIANT", "ADDITIONAL_ROYALTY_DUE"}:
        calc = result["calculation"]
        db.add(
            Royalty(
                asset_id=id_,
                artist_id=license_.artist_id,
                studio_id=license_.studio_id,
                license_id=license_.id,
                amount=calc["amount"],
                currency=calc["currency"],
                calculation=calc,
                status="NO_CHARGE" if Decimal(calc["amount"]) == 0 else "PENDING",
            )
        )
    asset.status, asset.error = result["status"], None
    db.flush()
    audit(db, actor, license_, "compliance.evaluated", id_, {"status": result["status"], "provider": source})
    return public(report)


@app.get("/api/royalties", response_model=list[RoyaltyResponse])
def royalties(db: DB, actor: Actor):
    return [
        public(x)
        for x in db.scalars(
            select(Royalty)
            .where(or_(Royalty.artist_id == actor.id, Royalty.studio_id == actor.id))
            .order_by(Royalty.created_at.desc())
        )
    ]


@app.post("/api/royalties/{id_}/decision", response_model=RoyaltyResponse)
def decide_royalty(id_: str, body: Decision, db: DB, actor: Actor):
    require_role(actor, "artist")
    royalty = owned(db, Royalty, id_, actor)
    target = "APPROVED" if body.approve else "REJECTED"
    if royalty.status == target:
        return public(royalty)
    if royalty.status != "PENDING":
        raise HTTPException(409, "Only pending charges can be approved or rejected.")
    royalty.status, royalty.decision_note, royalty.decided_at = target, body.note, now()
    license_ = owned(db, License, royalty.license_id, actor)
    audit(db, actor, license_, "royalty." + target.lower(), id_, {"note": body.note})
    db.flush()
    return public(royalty)


@app.get("/api/invoices", response_model=list[InvoiceResponse])
def invoices(db: DB, actor: Actor):
    return [{**public(x), "notice": PAYMENT_NOTICE} for x in provider.list_invoices(db, actor)]


@app.post("/api/royalties/{id_}/invoice", response_model=InvoiceResponse, status_code=201)
def create_invoice(id_: str, db: DB, actor: Actor):
    require_role(actor, "artist")
    royalty = owned(db, Royalty, id_, actor)
    invoice = provider.create_invoice(db, royalty)
    audit(db, actor, owned(db, License, royalty.license_id, actor), "invoice.simulated_created", invoice.id)
    return {**public(invoice), "notice": PAYMENT_NOTICE}


@app.get("/api/invoices/{id_}", response_model=InvoiceResponse)
def invoice_detail(id_: str, db: DB, actor: Actor):
    invoice = owned(db, Invoice, id_, actor)
    return {
        **public(invoice),
        "notice": PAYMENT_NOTICE,
        "events": [public(x) for x in db.scalars(select(PaymentEvent).where(PaymentEvent.invoice_id == id_))],
    }


@app.get("/api/invoices/{id_}/status")
def invoice_status(id_: str, db: DB, actor: Actor):
    owned(db, Invoice, id_, actor)
    return {"status": provider.get_payment_status(db, id_), "simulated": True, "notice": PAYMENT_NOTICE}


def invoice_command(id_, body, db, actor, kind):
    invoice = owned(db, Invoice, id_, actor)
    if kind == "SENT":
        require_role(actor, "artist")
        provider.send_invoice(db, invoice, actor, body.event_key)
    else:
        require_role(actor, "studio")
        provider.record_payment_event(db, invoice, actor, body.event_key, kind)
    royalty = db.get(Royalty, invoice.royalty_id)
    audit(db, actor, owned(db, License, royalty.license_id, actor), "invoice." + kind.lower(), id_)
    db.flush()
    return {**public(invoice), "notice": PAYMENT_NOTICE}


@app.post("/api/invoices/{id_}/send", response_model=InvoiceResponse)
def send_invoice(id_: str, body: PaymentCommand, db: DB, actor: Actor):
    return invoice_command(id_, body, db, actor, "SENT")


@app.post("/api/invoices/{id_}/simulate-payment", response_model=InvoiceResponse)
def simulate_payment(id_: str, body: PaymentCommand, db: DB, actor: Actor):
    return invoice_command(id_, body, db, actor, "PAID_SIMULATED")


@app.get("/api/audit", response_model=list[AuditResponse])
def audit_trail(db: DB, actor: Actor):
    return [
        public(x)
        for x in db.scalars(
            select(Audit)
            .where(or_(Audit.artist_id == actor.id, Audit.studio_id == actor.id))
            .order_by(Audit.created_at.desc())
            .limit(200)
        )
    ]


@app.get("/api/analytics", response_model=AnalyticsResponse)
def analytics(db: DB, actor: Actor):
    entries = royalties(db, actor)
    bills = provider.list_invoices(db, actor)
    currencies = sorted({x["currency"] for x in entries})
    totals = {}
    for currency in currencies:
        subset = [x for x in entries if x["currency"] == currency]
        totals[currency] = {
            "proposed": str(
                sum((Decimal(x["amount"]) for x in subset if x["status"] == "PENDING"), Decimal(0))
            ),
            "approved": str(
                sum((Decimal(x["amount"]) for x in subset if x["status"] == "APPROVED"), Decimal(0))
            ),
            "paid_simulated": str(
                sum(
                    (
                        Decimal(x.amount)
                        for x in bills
                        if x.currency == currency and x.status == "PAID_SIMULATED"
                    ),
                    Decimal(0),
                )
            ),
        }
    all_assets = assets(db, actor)
    return {
        "totals_by_currency": totals,
        "license_count": len(licenses(db, actor)),
        "asset_count": len(all_assets),
        "review_count": sum(x["status"] in {"NEEDS_REVIEW", "RESTRICTED_USAGE"} for x in all_assets),
        "pending_approvals": sum(x["status"] == "PENDING" for x in entries),
        "rows": entries,
        "notice": PAYMENT_NOTICE,
    }


@app.get("/api/demo/fixtures/{kind}")
def download_fixture(kind: str, actor: Actor):
    if kind not in {"contract", "audio"}:
        raise HTTPException(404, "Unknown fixture.")
    path = Path("fixtures") / ("sample-license.pdf" if kind == "contract" else "sample-narration.wav")
    if not path.exists():
        raise HTTPException(404, "Run scripts/create-demo.ps1 from the repository root first.")
    return FileResponse(
        path, filename=path.name, media_type="application/pdf" if kind == "contract" else "audio/wav"
    )
