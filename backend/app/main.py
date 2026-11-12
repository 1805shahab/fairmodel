import errno
import hashlib
import sqlite3
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Annotated

from fastapi import Body, Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pypdf import PdfReader
from sqlalchemy import or_, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from . import ai, audio
from .config import settings
from .db import (
    Analysis,
    Asset,
    Audit,
    Invoice,
    License,
    LicenseVersion,
    PaymentEvent,
    Persona,
    ReferenceVoice,
    Report,
    Royalty,
    RoyaltyApproval,
    SandboxInvoiceDetail,
    UsageAuthorization,
    engine,
    get_session,
    now,
    serialize,
    uid,
    UsageCase,
    CaseEvent,
)
from .passports import (
    capture_revision,
    passport,
    case_view,
    review_fingerprint,
    review_context,
    estimate,
    provenance,
)
from .payments import provider, payment_notice, sandbox_provider, settled_amount, outstanding_amount
from .paypal_client import paypal_client
from .eligibility import (
    POLICY_VERSION,
    approved_version,
    assessment_hash,
    authorization_state,
    digest,
    evidence_hash,
    royalty_is_eligible,
    approval_is_current,
)
from .royalties import evaluate
from .compliance_evidence import evidence_context
from .contract_rules import source_evidence
from .evidence import content_inputs_hash
from .migrations import migrate, SCHEMA_VERSION
from .overlap_resolution import comparison, save_review
from .compliance_evidence import overlapping_assets
from .presentation import explain_report
from .schemas import (
    AnalysisResponse,
    AuthorizationResponse,
    AuthorizationReview,
    AnalyticsResponse,
    AssetResponse,
    AuditResponse,
    Campaign,
    Decision,
    ExtractionCommand,
    InvoiceResponse,
    InvoiceCommand,
    LicenseCreate,
    LicenseResponse,
    PaymentCommand,
    OverlapDecision,
    OverlapResponse,
    PersonaResponse,
    ReferenceResponse,
    ReportResponse,
    ReviewTerms,
    RoyaltyResponse,
    Terms,
    ContentFindings,
    PassportResponse,
    UsageCaseCommand,
    CaseEventCommand,
    CaseResponse,
    EstimateCommand,
    EstimateResponse,
)

DB = Annotated[Session, Depends(get_session, scope="function")]


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
    migrate(engine)
    with Session(engine) as session:
        seed(session)
        session.commit()
    yield


app = FastAPI(
    title="FairModel",
    version="0.1.0",
    lifespan=lifespan,
    description="Local demo personas; separate mock and PayPal Sandbox payment providers. No production authentication or real-money endpoints.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Content-Type", "X-Demo-Persona"],
)


@app.exception_handler(OSError)
async def storage_error(_request, error: OSError):
    if error.errno == errno.ENOSPC:
        return JSONResponse(
            {"detail": "Local storage is full. Free disk space, then retry. No payment was performed."},
            status_code=507,
        )
    return JSONResponse(
        {"detail": "Local file storage is unavailable. Retry after checking storage."}, status_code=503
    )


@app.exception_handler(OperationalError)
async def database_error(_request, error: OperationalError):
    if getattr(error.orig, "sqlite_errorcode", None) == sqlite3.SQLITE_FULL:
        return await storage_error(_request, OSError(errno.ENOSPC, "Storage full"))
    return JSONResponse(
        {"detail": "The local database is temporarily unavailable. Retry after checking storage."},
        status_code=503,
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
    # Record successful/failed revisions alongside the audit, within the same transaction.
    if action.startswith(("analysis.", "compliance.", "usage.authorization")):
        for model, kind in (
            (Analysis, "analysis"),
            (Report, "compliance"),
            (UsageAuthorization, "authorization"),
        ):
            capture_revision(db, kind, db.scalar(select(model).where(model.asset_id == entity_id)))
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


def royalty_public(db, item):
    invoice = db.scalar(select(Invoice).where(Invoice.royalty_id == item.id))
    report = db.scalar(select(Report).where(Report.asset_id == item.asset_id))
    asset = db.get(Asset, item.asset_id)
    license_ = db.get(License, item.license_id)
    received = settled_amount(db, invoice) if invoice else Decimal("0")
    return {
        **public(item),
        "eligible_for_charge": royalty_is_eligible(db, item),
        "approval_current": approval_is_current(db, item),
        "artist_name": db.get(Persona, item.artist_id).name,
        "studio_name": db.get(Persona, item.studio_id).name,
        "license_title": license_.title,
        "campaign_name": asset.campaign.get("name", ""),
        "compliance_status": report.status if report else "PENDING",
        "invoice_status": invoice.status if invoice else "NOT_CREATED",
        "payment_provider": invoice.provider if invoice else "NOT_CREATED",
        "received_amount": str(received),
        "outstanding_amount": str(outstanding_amount(db, invoice) if invoice else Decimal(item.amount))
        if item.status == "APPROVED"
        else "0",
    }


def require_charge_eligibility(db, royalty):
    if not royalty_is_eligible(db, royalty):
        raise HTTPException(
            409,
            "Current compliance and artist identity/authorization review are required before approving or invoicing this charge.",
        )


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
    return {"status": "ok", "payment_provider": settings.payment_provider, "demo_auth": True}


@app.get("/api/integrations")
def integrations(actor: Actor):
    return {
        "demo_mode": True,
        "payment_provider": settings.payment_provider,
        "payment_notice": payment_notice(),
        "gemini": {
            "configured": bool(settings.gemini_api_key.get_secret_value()),
            "model": settings.gemini_model,
        },
        "groq": {
            "configured": bool(settings.groq_api_key.get_secret_value()),
            "model": settings.groq_whisper_model,
        },
        "voice_generation": {
            "diagnostics_version": 1,
            "enabled": settings.enable_voice_generation,
            "configured": bool(settings.gemini_api_key.get_secret_value()),
            "model": settings.gemini_tts_model,
            "replication_model": settings.gemini_voice_replication_model,
            "provider": "Gemini TTS",
            "voice_mode": "replicated; separate authentic consent recording required",
            "access_note": "Paid-tier project required; configured status does not verify provider access.",
            "fish": {
                "output_audio_pipeline": "mp3-complete-probe-normalize-v5",
                "enabled": settings.enable_voice_generation and settings.enable_fish_generation,
                "configured": bool(settings.fish_api_key.get_secret_value()),
                "model": settings.fish_tts_model,
                "access_note": "Free model under fair-use limits; no DPA/zero-retention guarantee. Separate Fish artist consent required. No live access verification implied.",
            },
        },
        "audio_tools": audio.availability(),
        "speaker_verification": {
            "enabled": settings.enable_speaker_verification,
            "status": "optional worker required" if settings.enable_speaker_verification else "disabled",
        },
        "paypal": "Sandbox adapter available; authentication and invoice actions are verified separately",
        "paypal_configuration": {
            "credentials_configured": paypal_client.configured,
            "merchant_configured": bool(settings.paypal_sandbox_merchant_email),
            "buyer_configured": bool(settings.paypal_sandbox_buyer_email),
            "drafts_enabled": settings.paypal_allow_drafts,
            "sending_enabled": settings.paypal_allow_sending,
            "webhook_configured": bool(settings.paypal_webhook_id.get_secret_value()),
        },
        "schema_version": SCHEMA_VERSION,
        "compliance_policy_version": POLICY_VERSION,
        "fixtures_available": bool(ai.fixture_manifest()),
    }


@app.get("/api/personas", response_model=list[PersonaResponse])
def personas(db: DB):
    return [public(x) for x in db.scalars(select(Persona).where(Persona.role.in_(["artist", "studio"])))]


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
        "source_review": source_evidence(Terms.model_validate(license_.terms), license_.pages),
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
    audit(
        db,
        actor,
        license_,
        "contract.extracted",
        id_,
        {"provider": source, "provider_receipt": terms._provider_receipt},
    )
    return public(license_)


def review_license(id_, body, db, actor, activate):
    require_role(actor, "artist")
    license_ = owned(db, License, id_, actor)
    license_editable(license_)
    if not license_.contract_path:
        raise HTTPException(409, "A source contract is required before reviewing terms.")
    if body.expected_version != license_.version:
        raise HTTPException(409, "Terms changed in another session. Refresh and review again.")
    terms = ai.validate_evidence(body.terms, license_.pages)
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
    return [asset_view(db, x) for x in db.scalars(query.order_by(Asset.created_at.desc()))]


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
    asset, license_ = asset_owned(db, id_, actor)
    return asset_view(db, asset, detail=True)


def asset_view(db, asset, detail=False):
    id_ = asset.id
    license_ = db.get(License, asset.license_id)
    analysis = db.scalar(select(Analysis).where(Analysis.asset_id == id_))
    report = db.scalar(select(Report).where(Report.asset_id == id_))
    royalty = db.scalar(select(Royalty).where(Royalty.asset_id == id_))
    review, state = authorization_state(db, asset, analysis, license_) if analysis else (None, {})
    invoice = db.scalar(select(Invoice).where(Invoice.royalty_id == royalty.id)) if royalty else None
    shown_report = public(report) if report else None
    if report and analysis:
        try:
            version = approved_version(db, asset, license_)
            current = assessment_hash(
                asset, analysis, version, state, evidence_context(db, asset, analysis, license_, version)
            )
            stale = (
                report.result.get("input_hash") != current
                or report.result.get("policy_version") != POLICY_VERSION
            )
        except HTTPException:
            stale = True
        if stale:
            shown_report = {
                **shown_report,
                "status": "NEEDS_REVIEW",
                "result": {
                    **report.result,
                    "status": "NEEDS_REVIEW",
                    "eligible_for_charge": False,
                    "stale": True,
                    "primary_reason": "Inputs or review decisions changed; this historical report needs reevaluation.",
                    "reasons": [
                        "Inputs or review decisions changed; reevaluate compliance before approving charges."
                    ],
                    "next_action": "Reevaluate compliance using the current approved inputs.",
                },
            }
    processing = "ANALYZED" if analysis else "FAILED" if asset.status == "FAILED" else "UPLOADED"
    compliance = shown_report["status"] if shown_report else "PENDING"
    stage = (
        compliance
        if compliance in {"NEEDS_REVIEW", "RESTRICTED_USAGE"}
        else (
            "PAID_SIMULATED"
            if invoice and invoice.status == "PAID_SIMULATED"
            else "INVOICE_" + invoice.status
            if invoice
            else "ROYALTY_APPROVED"
            if royalty and approval_is_current(db, royalty)
            else "COMPLIANCE_EVALUATED"
            if report
            else "AUTHORIZED"
            if state.get("status") == "artist_confirmed"
            else "AUDIO_ANALYZED"
            if analysis
            else processing
        )
    )
    action = (
        shown_report["result"].get("next_action", "Evaluate compliance.")
        if shown_report
        else "Evaluate compliance."
        if analysis
        else "Studio: run audio analysis."
    )
    if compliance in {"COMPLIANT", "ADDITIONAL_ROYALTY_DUE"}:
        if invoice and invoice.status == "PAID_SIMULATED":
            action = "Simulated payment completed. Review the invoice/event history; no real funds were transferred."
        elif invoice and invoice.status == "SENT":
            action = "Studio: deliberately simulate payment completion. No real funds are transferred."
        elif invoice and invoice.status == "DRAFT":
            action = (
                "Artist: simulate sending the approved invoice. No email or real funds are sent."
                if approval_is_current(db, royalty)
                else "Artist: renew current charge approval before sending this unchanged simulated invoice."
            )
        elif royalty and royalty.status == "APPROVED":
            action = (
                "Artist: create an invoice with the selected payment provider for this current approved charge."
                if approval_is_current(db, royalty)
                else "Artist: renew charge approval for the current reviewed evidence before invoicing."
            )
        elif royalty and royalty.status == "NO_CHARGE":
            action = "Included usage: no additional royalty or payable invoice."
    if (
        invoice
        and invoice.provider == "paypal_sandbox"
        and compliance in {"COMPLIANT", "ADDITIONAL_ROYALTY_DUE"}
    ):
        if invoice.status == "PAID":
            action = "PayPal Sandbox settlement verified from provider status and payment evidence. No real money was transferred."
        elif invoice.status == "DRAFT":
            action = (
                "Artist: review this actual Sandbox draft and explicitly send it when authorized."
                if approval_is_current(db, royalty)
                else "Artist: resolve eligibility and renew charge approval before sending the unchanged Sandbox draft."
            )
        else:
            action = "Review the actual Sandbox invoice/payment history. The test buyer pays manually through the provider-returned link; refresh status afterward."
    cases = review_context(
        db, asset, (report.result.get("billing_usage") or {}).get("member_asset_ids") if report else None
    )
    if cases["blocked"]:
        compliance = "RESTRICTED_USAGE" if compliance == "RESTRICTED_USAGE" else "NEEDS_REVIEW"
        stage = "NEEDS_REVIEW"
        action = "Open the Review Center: an open or stale artist decision requires resolution and compliance reevaluation. Existing invoices remain unchanged and require reconciliation."
    return {
        **public(asset),
        "status": compliance if report else processing,
        "processing_state": processing,
        "compliance_state": compliance,
        "authorization_state": state.get("status", "unresolved"),
        "royalty_state": royalty.status if royalty else "NOT_ALLOCATED",
        "invoice_state": invoice.status if invoice else "NOT_CREATED",
        "workflow_stage": stage,
        "next_action": action,
        "provenance": provenance(
            analysis.result if analysis else None, shown_report["result"] if shown_report else None
        ),
        "review_cases": cases,
        **(
            {
                "analysis": public(analysis) if analysis else None,
                "report": shown_report,
                "royalty": royalty_public(db, royalty) if royalty else None,
                "invoice": invoice_public(db, invoice) if invoice else None,
                "authorization": {**public(review), "status": state["status"]} if review else None,
            }
            if detail
            else {}
        ),
    }


@app.get("/api/assets/{id_}/overlap", response_model=OverlapResponse)
def overlap_detail(id_: str, db: DB, actor: Actor):
    asset, _ = asset_owned(db, id_, actor)
    analysis = db.scalar(select(Analysis).where(Analysis.asset_id == id_))
    if not analysis:
        return {"asset_id": id_, "pairs": [], "incoming": [], "usage": None}
    return comparison(db, asset, analysis, overlapping_assets(db, asset, analysis))


@app.post("/api/assets/{id_}/overlap", response_model=OverlapResponse)
def overlap_decision(id_: str, body: OverlapDecision, db: DB, actor: Actor):
    require_role(actor, "artist")
    asset, license_ = asset_owned(db, id_, actor)
    related, _ = asset_owned(db, body.related_asset_id, actor)
    approved_version(db, asset, license_)
    row, created = save_review(db, asset, related, actor, body)
    if created:
        audit(
            db,
            actor,
            license_,
            "usage.overlap_reviewed",
            id_,
            {
                "review_id": row.id,
                "related_asset_id": related.id,
                "decision": row.decision,
                "previous_id": row.previous_id,
                "note": row.note,
                "evidence_hash": row.evidence_hash,
            },
        )
    refreshed = False
    saved_report = db.scalar(select(Report).where(Report.asset_id == id_))
    saved_analysis = db.scalar(select(Analysis).where(Analysis.asset_id == id_))
    version = approved_version(db, asset, license_)
    if saved_report and not saved_report.result.get("latest_attempt_failed"):
        mode = bool(saved_report.result.get("assessment_fixture"))
        expected = content_inputs_hash(
            Terms.model_validate(version.terms), saved_analysis.result["transcript"], asset.campaign, mode
        )
        if saved_report.result.get("content_input_hash") == expected:
            # Same validated content evidence: update deterministic/workflow checks,
            # retaining the original provider receipt. Never a provider-error fallback.
            evaluate_asset(id_, ExtractionCommand(use_demo_fixture=mode), db, actor)
            refreshed = True
    result = overlap_detail(id_, db, actor)
    return {"review": public(row), "created": created, "evaluation_refreshed": refreshed, **result}


@app.post("/api/assets/{id_}/authorization", response_model=AuthorizationResponse)
def review_usage(id_: str, body: AuthorizationReview, db: DB, actor: Actor):
    require_role(actor, "artist")
    asset, license_ = asset_owned(db, id_, actor)
    analysis = db.scalar(select(Analysis).where(Analysis.asset_id == id_))
    if not analysis:
        raise HTTPException(409, "Analyze the audio before reviewing identity and authorization.")
    approved_version(db, asset, license_)
    review = db.scalar(select(UsageAuthorization).where(UsageAuthorization.asset_id == id_))
    capture_revision(db, "authorization", review)
    if (
        review
        and review.identity_confirmed == body.identity_confirmed
        and review.use_authorized == body.use_authorized
        and review.note == body.note
        and review.evidence_hash
        in {evidence_hash(asset, analysis), evidence_hash(asset, analysis, legacy=True)}
    ):
        _, state = authorization_state(db, asset, analysis, license_)
        return {**public(review), "status": state["status"]}
    if not review:
        review = UsageAuthorization(asset_id=id_, artist_id=actor.id, license_version=asset.license_version)
        db.add(review)
    review.identity_confirmed, review.use_authorized, review.note = (
        body.identity_confirmed,
        body.use_authorized,
        body.note,
    )
    review.evidence_hash, review.updated_at = evidence_hash(asset, analysis), now()
    report = db.scalar(select(Report).where(Report.asset_id == id_))
    capture_revision(db, "compliance", report)
    if report:
        asset.status = "NEEDS_REVIEW"
        report.status = "NEEDS_REVIEW"
        report.result = {
            **report.result,
            "status": "NEEDS_REVIEW",
            "eligible_for_charge": False,
            "reasons": [
                "Artist identity/authorization review changed. Reevaluate compliance before proposing charges."
            ],
        }
    db.flush()
    audit(
        db,
        actor,
        license_,
        "usage.authorization_reviewed",
        id_,
        {
            "review_id": review.id,
            "identity_confirmed": body.identity_confirmed,
            "use_authorized": body.use_authorized,
            "note": body.note,
            "evidence_hash": review.evidence_hash,
        },
    )
    _, state = authorization_state(db, asset, analysis, license_)
    return {**public(review), "status": state["status"]}


@app.patch("/api/assets/{id_}/campaign", response_model=AssetResponse)
def correct_campaign(id_: str, body: Campaign, db: DB, actor: Actor):
    require_role(actor, "studio")
    asset, license_ = asset_owned(db, id_, actor)
    if asset.campaign == body.model_dump(mode="json"):
        return asset_view(db, asset)
    if db.scalar(select(Royalty).where(Royalty.asset_id == id_)):
        raise HTTPException(
            409, "Usage with an allocated royalty is immutable. Contact the artist for review."
        )
    asset.campaign = body.model_dump(mode="json")
    report = db.scalar(select(Report).where(Report.asset_id == id_))
    capture_revision(db, "compliance", report)
    if report:
        db.delete(report)
    # Keep the recorded attestation for history; changed evidence makes its status stale.
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
    capture_revision(db, "analysis", existing)
    capture_revision(db, "compliance", db.scalar(select(Report).where(Report.asset_id == id_)))
    if existing and not body.reprocess and existing.result.get("demo_fixture") is body.use_demo_fixture:
        return public(existing)
    if existing and db.scalar(select(Royalty).where(Royalty.asset_id == id_)):
        raise HTTPException(
            409,
            "Transcription evidence with a royalty allocation is immutable. Use a new agreement/asset for a new live run.",
        )
    normalized = settings.storage_dir / f"{asset.id}-normalized.wav"
    try:
        metadata = audio.probe(Path(asset.path))
        audio.normalize(Path(asset.path), normalized)
        speech = audio.speech_activity(normalized)
        transcript = ai.transcribe(normalized, Path(asset.path), body.use_demo_fixture)
    except HTTPException as exc:
        asset.status, asset.error = "ANALYZED" if existing else "FAILED", str(exc.detail)
        audit(db, actor, license_, "analysis.failed", id_, {"status_code": exc.status_code})
        db.commit()
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    asset.status, asset.error, asset.normalized_path = "ANALYZED", None, str(normalized)
    speaker = {
        "status": "unavailable" if settings.enable_speaker_verification else "disabled",
        "model": None,
        "score": None,
        "note": "Identity has not been automatically verified. The optional worker has not run; no similarity score is claimed. Artist review is required before proposing a charge.",
    }
    result = {
        **metadata,
        **speech,
        **transcript,
        **audio.normalized_fingerprint(normalized),
        "speaker": speaker,
        "demo_fixture": body.use_demo_fixture,
    }
    if existing:
        analysis = existing
        previous_hash = evidence_hash(asset, analysis)
        review, _ = authorization_state(db, asset, analysis, license_)
        old_valid = bool(
            review and review.evidence_hash in {previous_hash, evidence_hash(asset, analysis, legacy=True)}
        )
        analysis.result, analysis.updated_at = result, now()
        if old_valid and previous_hash == evidence_hash(asset, analysis):
            review.evidence_hash = previous_hash
        elif previous_hash != evidence_hash(asset, analysis):
            old_report = db.scalar(select(Report).where(Report.asset_id == id_))
            if old_report:
                db.delete(old_report)
    else:
        analysis = Analysis(asset_id=id_, result=result)
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
    capture_revision(db, "compliance", existing)
    analysis = db.scalar(select(Analysis).where(Analysis.asset_id == id_))
    if not analysis:
        raise HTTPException(409, "Analyze the audio before evaluating compliance.")
    version = approved_version(db, asset, license_)
    terms = Terms.model_validate(version.terms)
    if not db.scalar(select(Audit).where(Audit.entity_id == id_, Audit.action == "compliance.requested")):
        audit(db, actor, license_, "compliance.requested", id_, {"license_version": asset.license_version})
        db.flush()
    context = evidence_context(db, asset, analysis, license_, version)
    _, authorization = authorization_state(db, asset, analysis, license_)
    current_hash = assessment_hash(asset, analysis, version, authorization, context)
    if (
        existing
        and not body.reprocess
        and not existing.result.get("latest_attempt_failed")
        and existing.result.get("policy_version") == POLICY_VERSION
        and existing.result.get("assessment_fixture") is body.use_demo_fixture
        and existing.result.get("input_hash") == current_hash
    ):
        return public(existing)
    if body.use_demo_fixture and not analysis.result.get("demo_fixture"):
        raise HTTPException(422, "Live transcripts cannot use fixture content assessment.")
    try:
        content_hash = content_inputs_hash(
            terms, analysis.result["transcript"], asset.campaign, body.use_demo_fixture
        )
        reused = bool(
            existing
            and not body.reprocess
            and not existing.result.get("latest_attempt_failed")
            and existing.result.get("content_input_hash") == content_hash
            and existing.result.get("assessment_fixture") is body.use_demo_fixture
        )
        if reused:
            findings = ContentFindings.model_validate(existing.result["findings"])
            findings._provider_receipt = existing.result.get("provider_receipt", {})
            source = existing.result["provider"]
        else:
            findings, source = ai.content_findings(
                terms, analysis.result["transcript"], body.use_demo_fixture, campaign=asset.campaign
            )
    except HTTPException as exc:
        asset.error = str(exc.detail)
        if existing:
            asset.status = existing.status = "NEEDS_REVIEW"
            existing.result = {
                **existing.result,
                "status": "NEEDS_REVIEW",
                "eligible_for_charge": False,
                "latest_attempt_failed": True,
                "reasons": [
                    *existing.result.get("reasons", []),
                    "Latest compliance request failed. Previous findings are retained as history; retry before proposing charges.",
                ],
            }
        audit(db, actor, license_, "compliance.failed", id_, {"status_code": exc.status_code})
        db.commit()
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    royalty = db.scalar(select(Royalty).where(Royalty.asset_id == id_))
    prior_entries = list(
        db.scalars(select(Royalty).where(Royalty.license_id == license_.id, Royalty.asset_id != id_))
    )
    prior = sum((Decimal(x.calculation["spoken_seconds"]) for x in prior_entries), Decimal(0))
    if royalty:
        prior = Decimal(royalty.calculation["prior_seconds"])
    result = evaluate(
        terms,
        Campaign.model_validate(asset.campaign),
        analysis.result,
        findings,
        prior,
        analysis.result.get("speaker"),
        authorization=authorization,
        evidence_is_fixture=bool(analysis.result.get("demo_fixture")),
        assessment_is_fixture=body.use_demo_fixture,
        source_review=context["source"],
        workflow=context["workflow"],
        overlap=context["usage"]["unresolved"],
    )
    result["overlap"] = context["overlap"]
    result["billing_usage"] = context["usage"]
    if context.get("review_cases", {}).get("blocked"):
        if result["status"] != "RESTRICTED_USAGE":
            result["status"] = "NEEDS_REVIEW"
        result["eligible_for_charge"] = False
        result["reasons"].append(
            "An open or stale artist review/dispute blocks financial approval. Resolve it in the Review Center, then reevaluate. Existing invoices require reconciliation; no provider action was performed."
        )
        result["review_cases"] = context["review_cases"]
    if context["usage"]["reconciliation_required"] or context["cumulative_reconciliation_required"]:
        if result["status"] != "RESTRICTED_USAGE":
            result["status"] = "NEEDS_REVIEW"
        result["eligible_for_charge"] = False
        result["reasons"].append(
            "Linked historical allocations or a longer edit require financial reconciliation. No charge or invoice was changed."
        )
    if context["usage"]["disposition"] == "SAME_USAGE":
        result["eligible_for_charge"] = False
        if result["status"] == "ADDITIONAL_ROYALTY_DUE":
            result["status"] = "COMPLIANT"
        result["separate_allocation"] = False
    transcription_mode = (
        "fixture"
        if analysis.result.get("demo_fixture")
        else ("live" if analysis.result.get("provider", "").startswith("groq:") else "unknown")
    )
    if transcription_mode == "unknown":
        result["status"], result["eligible_for_charge"] = "NEEDS_REVIEW", False
        result["reasons"].append("Transcription provenance could not be verified.")
    if (
        royalty
        and result["calculation"]
        and (
            result["calculation"]["amount"] != royalty.amount
            or result["calculation"]["currency"] != royalty.currency
        )
    ):
        result["status"], result["eligible_for_charge"] = "NEEDS_REVIEW", False
        result["reasons"].append(
            "This calculation differs from the historical royalty. Financial reconciliation is required; no replacement charge was created."
        )
    result.update(
        {
            "provider": source,
            "assessment_reused": reused,
            "content_input_hash": content_hash,
            "license_version": asset.license_version,
            "source_pages": context["source"]["citations"],
            "source_review": {
                "missing_fields": context["source"]["missing_fields"],
                "review_reasons": context["source"]["review_reasons"],
                "approved_snapshot_unchanged": True,
                "recovered_condition_citations": sum(
                    x["origin"] == "source_text_match" for x in context["source"]["citations"]
                ),
            },
            "workflow": context["workflow"],
            "provider_receipt": findings._provider_receipt,
            "policy_version": POLICY_VERSION,
            "input_hash": current_hash,
            "terms_hash": digest(version.terms),
            "assessment_fixture": body.use_demo_fixture,
            "transcription_provider": analysis.result.get("provider", "unknown"),
            "transcription_mode": transcription_mode,
        }
    )
    explain_report(result)
    if existing:
        report = existing
        report.status, report.result, report.updated_at = result["status"], result, now()
    else:
        report = Report(asset_id=id_, status=result["status"], result=result)
        db.add(report)
    if result["eligible_for_charge"] and not royalty:
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
    if result["eligible_for_charge"] and not royalty:
        allocation = db.scalar(select(Royalty).where(Royalty.asset_id == id_))
        audit(
            db,
            actor,
            license_,
            "royalty.calculated",
            allocation.id,
            {
                "asset_id": id_,
                "amount": allocation.amount,
                "currency": allocation.currency,
                "method": "deterministic_decimal",
            },
        )
    audit(db, actor, license_, "compliance.evaluated", id_, {"status": result["status"], "provider": source})
    return public(report)


@app.get("/api/royalties", response_model=list[RoyaltyResponse])
def royalties(db: DB, actor: Actor):
    return [
        royalty_public(db, x)
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
    if body.approve:
        require_charge_eligibility(db, royalty)
    target = "APPROVED" if body.approve else "REJECTED"
    if royalty.status == target and (not body.approve or approval_is_current(db, royalty)):
        return royalty_public(db, royalty)
    if royalty.status != "PENDING" and not (body.approve and royalty.status == "APPROVED"):
        raise HTTPException(409, "Only pending charges can be approved or rejected.")
    if body.approve:
        invoice = db.scalar(select(Invoice).where(Invoice.royalty_id == royalty.id))
        if invoice and (invoice.amount != royalty.amount or invoice.currency != royalty.currency):
            raise HTTPException(
                409, "The immutable invoice differs from this charge. Financial reconciliation is required."
            )
        report = db.scalar(select(Report).where(Report.asset_id == royalty.asset_id))
        if not db.scalar(
            select(RoyaltyApproval).where(
                RoyaltyApproval.royalty_id == royalty.id,
                RoyaltyApproval.evidence_hash == report.result["input_hash"],
            )
        ):
            db.add(
                RoyaltyApproval(
                    royalty_id=royalty.id,
                    artist_id=actor.id,
                    evidence_hash=report.result["input_hash"],
                    note=body.note,
                )
            )
    royalty.status, royalty.decision_note, royalty.decided_at = target, body.note, now()
    license_ = owned(db, License, royalty.license_id, actor)
    audit(db, actor, license_, "royalty." + target.lower(), id_, {"note": body.note})
    db.flush()
    return royalty_public(db, royalty)


def invoice_public(db, invoice, events=False):
    result = {
        **public(invoice),
        "notice": payment_notice(invoice),
        "eligible_for_send": approval_is_current(db, db.get(Royalty, invoice.royalty_id)),
    }
    detail = db.scalar(select(SandboxInvoiceDetail).where(SandboxInvoiceDetail.invoice_id == invoice.id))
    if detail:
        result["sandbox"] = {
            key: getattr(detail, key)
            for key in (
                "issuer",
                "invoice_number",
                "provider_status",
                "payment_url",
                "due_date",
                "paid_amount",
                "due_amount",
                "refunded_amount",
                "last_synced_at",
                "error",
                "transactions",
            )
        }
    if events:
        result["events"] = [
            public(row)
            for row in db.scalars(
                select(PaymentEvent)
                .where(PaymentEvent.invoice_id == invoice.id)
                .order_by(PaymentEvent.created_at)
            )
        ]
    return result


@app.post("/api/paypal/diagnostic")
def paypal_diagnostic(actor: Actor):
    require_role(actor, "artist")
    return paypal_client.diagnostic(capability=True)


@app.get("/api/royalties/{id_}/invoice-preview")
def invoice_preview(id_: str, db: DB, actor: Actor):
    require_role(actor, "artist")
    royalty = owned(db, Royalty, id_, actor)
    require_charge_eligibility(db, royalty)
    return {
        "provider": settings.payment_provider,
        "amount": royalty.amount,
        "currency": royalty.currency,
        "sandbox_payload": sandbox_provider.payload(db, royalty)
        if settings.payment_provider == "paypal_sandbox"
        else None,
        "notice": payment_notice(),
    }


@app.get("/api/invoices", response_model=list[InvoiceResponse])
def invoices(db: DB, actor: Actor):
    return [invoice_public(db, invoice) for invoice in provider.list_invoices(db, actor)]


@app.post("/api/royalties/{id_}/invoice", response_model=InvoiceResponse, status_code=201)
def create_invoice(id_: str, db: DB, actor: Actor, body: InvoiceCommand | None = Body(default=None)):
    require_role(actor, "artist")
    royalty = owned(db, Royalty, id_, actor)
    require_charge_eligibility(db, royalty)
    if not approval_is_current(db, royalty):
        raise HTTPException(
            409,
            "Artist charge approval is stale or missing. Review and approve the current calculation before invoicing.",
        )
    if settings.payment_provider == "paypal_sandbox":
        _, buyer = sandbox_provider.profile()
        if (
            not body
            or not body.confirm_sandbox
            or body.expected_amount != royalty.amount
            or body.expected_currency != royalty.currency
            or body.expected_recipient != buyer
        ):
            raise HTTPException(
                409,
                "Explicit Sandbox draft confirmation must match this case's amount, currency and configured buyer.",
            )
    invoice = provider.create_invoice(db, royalty)
    action = "invoice.simulated_created" if invoice.simulated else "invoice.paypal_sandbox_created"
    if not db.scalar(select(Audit).where(Audit.entity_id == invoice.id, Audit.action == action)):
        audit(db, actor, owned(db, License, royalty.license_id, actor), action, invoice.id)
    return invoice_public(db, invoice)


@app.get("/api/invoices/{id_}", response_model=InvoiceResponse)
def invoice_detail(id_: str, db: DB, actor: Actor):
    return invoice_public(db, owned(db, Invoice, id_, actor), events=True)


@app.get("/api/invoices/{id_}/status")
def invoice_status(id_: str, db: DB, actor: Actor):
    invoice = owned(db, Invoice, id_, actor)
    status = provider.get_payment_status(db, id_)
    return {"status": status, "simulated": invoice.simulated, "notice": payment_notice(invoice)}


@app.post("/api/invoices/{id_}/refresh", response_model=InvoiceResponse)
def refresh_invoice(id_: str, db: DB, actor: Actor):
    invoice = owned(db, Invoice, id_, actor)
    if invoice.provider == "paypal_sandbox":
        sandbox_provider.refresh(db, invoice)
        royalty = db.get(Royalty, invoice.royalty_id)
        audit(
            db,
            actor,
            owned(db, License, royalty.license_id, actor),
            "invoice.status_synchronized",
            invoice.id,
            {"status": invoice.status, "provider": invoice.provider},
        )
    return invoice_public(db, invoice, events=True)


def invoice_command(id_, body, db, actor, kind):
    invoice = owned(db, Invoice, id_, actor)
    if kind == "SENT":
        require_role(actor, "artist")
        royalty = db.get(Royalty, invoice.royalty_id)
        require_charge_eligibility(db, royalty)
        if not approval_is_current(db, royalty):
            raise HTTPException(409, "Current artist approval is required before sending this invoice.")
        if invoice.provider == "paypal_sandbox" and not body.confirm_sandbox:
            raise HTTPException(
                409, "Explicit confirmation is required before sending this actual Sandbox invoice."
            )
        provider.send_invoice(db, invoice, actor, body.event_key)
    else:
        require_role(actor, "studio")
        provider.record_payment_event(db, invoice, actor, body.event_key, kind)
    royalty = db.get(Royalty, invoice.royalty_id)
    audit(db, actor, owned(db, License, royalty.license_id, actor), "invoice." + kind.lower(), id_)
    db.flush()
    return invoice_public(db, invoice)


@app.post("/api/invoices/{id_}/send", response_model=InvoiceResponse)
def send_invoice(id_: str, body: PaymentCommand, db: DB, actor: Actor):
    return invoice_command(id_, body, db, actor, "SENT")


@app.post("/api/invoices/{id_}/simulate-payment", response_model=InvoiceResponse)
def simulate_payment(id_: str, body: PaymentCommand, db: DB, actor: Actor):
    return invoice_command(id_, body, db, actor, "PAID_SIMULATED")


@app.post("/api/paypal/webhook")
async def paypal_webhook(request: Request, db: DB):
    from .paypal_webhooks import handle_webhook

    data = await request.body()
    return handle_webhook(db, dict(request.headers), data, sandbox_provider)


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
            "outstanding": str(
                sum(
                    (Decimal(x["outstanding_amount"]) for x in subset if x["status"] == "APPROVED"),
                    Decimal(0),
                )
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
            "paid_sandbox": str(
                sum(
                    (
                        settled_amount(db, b)
                        for b in bills
                        if b.currency == currency and b.provider == "paypal_sandbox"
                    ),
                    Decimal("0"),
                )
            ),
        }
    all_assets = assets(db, actor)
    queue = [
        x
        for x in all_assets
        if x["compliance_state"] in {"PENDING", "NEEDS_REVIEW", "RESTRICTED_USAGE"}
        or x["royalty_state"] == "PENDING"
        or x["invoice_state"]
        in {
            "DRAFT",
            "SENT",
            "VIEWED",
            "SCHEDULED",
            "PAYMENT_PENDING",
            "PARTIALLY_PAID",
            "NEEDS_RECONCILIATION",
        }
    ]
    return {
        "totals_by_currency": totals,
        "license_count": len(licenses(db, actor)),
        "asset_count": len(all_assets),
        "active_license_count": sum(x["status"] == "ACTIVE" for x in licenses(db, actor)),
        "outstanding_invoice_count": sum(outstanding_amount(db, x) > 0 for x in bills),
        "included_usage_count": sum(Decimal(x["amount"]) == 0 for x in entries),
        "review_queue": [
            {
                key: x[key]
                for key in (
                    "id",
                    "original_name",
                    "campaign",
                    "processing_state",
                    "compliance_state",
                    "workflow_stage",
                    "next_action",
                )
            }
            for x in queue[:8]
        ],
        "review_count": sum(x["status"] in {"NEEDS_REVIEW", "RESTRICTED_USAGE"} for x in all_assets),
        "pending_approvals": sum(x["status"] == "PENDING" for x in entries),
        "rows": entries,
        "notice": payment_notice(),
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


@app.get("/api/assets/{id_}/passport", response_model=PassportResponse)
def get_passport(id_: str, db: DB, actor: Actor):
    asset, license_ = asset_owned(db, id_, actor)
    view = asset_view(db, asset, detail=True)
    if view.get("invoice"):
        view["invoice"] = invoice_public(db, db.get(Invoice, view["invoice"]["id"]), events=True)
    return passport(db, asset, license_, view)


@app.get("/api/review-cases", response_model=list[CaseResponse])
def review_cases(db: DB, actor: Actor):
    rows = db.scalars(
        select(UsageCase)
        .where(or_(UsageCase.artist_id == actor.id, UsageCase.studio_id == actor.id))
        .order_by(UsageCase.created_at.desc())
    )
    return [
        {
            **case_view(
                db,
                row,
                db.get(Asset, row.asset_id),
                db.scalar(select(Analysis).where(Analysis.asset_id == row.asset_id)),
            ),
            "asset_name": db.get(Asset, row.asset_id).original_name,
            "campaign_name": db.get(Asset, row.asset_id).campaign.get("name"),
        }
        for row in rows
    ]


@app.post("/api/assets/{id_}/review-cases", response_model=CaseResponse, status_code=201)
def create_review_case(id_: str, body: UsageCaseCommand, db: DB, actor: Actor):
    require_role(actor, "artist")
    asset, license_ = asset_owned(db, id_, actor)
    approved_version(db, asset, license_)
    analysis = db.scalar(select(Analysis).where(Analysis.asset_id == id_))
    fingerprint = review_fingerprint(asset, analysis)
    existing = db.scalar(
        select(UsageCase).where(UsageCase.asset_id == id_, UsageCase.request_key == body.request_key)
    )
    if existing:
        if (existing.decision, existing.category, existing.note, existing.evidence_refs) != (
            body.decision,
            body.category,
            body.note,
            body.evidence_refs,
        ):
            raise HTTPException(409, "This request key already identifies a different decision.")
        return case_view(db, existing, asset, analysis)
    evidence = passport(db, asset, license_, asset_view(db, asset, detail=True))
    allowed_refs = {row["id"] for row in evidence["history"] + evidence["audit"]}
    allowed_refs.update(
        "contract:" + item["field"] for item in evidence["license"]["source_review"]["citations"]
    )
    for key in ("analysis", "report", "authorization", "royalty", "invoice"):
        if evidence["asset"].get(key):
            allowed_refs.add(evidence["asset"][key]["id"])
    if not set(body.evidence_refs).issubset(allowed_refs):
        raise HTTPException(422, "Supporting references must belong to this asset and approved contract.")
    row = UsageCase(
        asset_id=id_,
        artist_id=actor.id,
        studio_id=asset.studio_id,
        license_version=asset.license_version,
        request_key=body.request_key,
        decision=body.decision,
        category=body.category,
        note=body.note,
        evidence_refs=body.evidence_refs,
        evidence_hash=fingerprint,
        status="RESOLVED" if body.decision == "APPROVE_USAGE" else "OPEN",
    )
    db.add(row)
    db.flush()
    db.add(
        CaseEvent(
            case_id=row.id,
            actor_id=actor.id,
            request_key=body.request_key,
            kind="OPENED" if row.status == "OPEN" else "APPROVED_USAGE",
            note=body.note,
            evidence_hash=fingerprint,
        )
    )
    audit(
        db,
        actor,
        license_,
        "usage.review_recorded",
        id_,
        {"case_id": row.id, "decision": row.decision, "category": row.category},
    )
    db.flush()
    return case_view(db, row, asset, analysis)


@app.post("/api/review-cases/{id_}/events", response_model=CaseResponse)
def update_review_case(id_: str, body: CaseEventCommand, db: DB, actor: Actor):
    row = owned(db, UsageCase, id_, actor)
    asset, license_ = asset_owned(db, row.asset_id, actor)
    if body.kind == "RESOLVE":
        require_role(actor, "artist")
    existing = db.scalar(
        select(CaseEvent).where(CaseEvent.case_id == row.id, CaseEvent.request_key == body.request_key)
    )
    analysis = db.scalar(select(Analysis).where(Analysis.asset_id == asset.id))
    if existing:
        if (existing.kind, existing.note, existing.actor_id) != (body.kind, body.note, actor.id):
            raise HTTPException(409, "This request key already identifies a different response.")
        return case_view(db, row, asset, analysis)
    if body.kind == "RESPONSE" and row.status == "RESOLVED":
        raise HTTPException(
            409, "This case is resolved. The artist must open a new concern for further discussion."
        )
    db.add(
        CaseEvent(
            case_id=row.id,
            actor_id=actor.id,
            request_key=body.request_key,
            kind=body.kind,
            note=body.note,
            evidence_hash=review_fingerprint(asset, analysis),
        )
    )
    if body.kind == "RESOLVE":
        row.status = "RESOLVED"
    row.updated_at = now()
    audit(
        db,
        actor,
        license_,
        "usage.dispute_resolved" if body.kind == "RESOLVE" else "usage.dispute_response",
        asset.id,
        {"case_id": row.id},
    )
    db.flush()
    return case_view(db, row, asset, analysis)


@app.post("/api/licenses/{id_}/estimate", response_model=EstimateResponse)
def estimate_usage(id_: str, body: EstimateCommand, db: DB, actor: Actor):
    require_role(actor, "studio")
    license_ = owned(db, License, id_, actor)
    version = db.scalar(
        select(LicenseVersion).where(
            LicenseVersion.license_id == id_, LicenseVersion.version == license_.version
        )
    )
    if not version or license_.status != "ACTIVE" or version.approved_by != license_.artist_id:
        raise HTTPException(409, "An active artist-approved contract is required for an estimate.")
    return estimate(db, license_, version, body)


from .voice_routes import router as voice_router  # noqa: E402 - existing workflow helpers are defined first.

app.include_router(voice_router)
