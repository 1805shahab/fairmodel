from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .config import settings


def uid() -> str:
    return uuid4().hex


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    created_at: Mapped[str] = mapped_column(default=now)
    updated_at: Mapped[str] = mapped_column(default=now, onupdate=now)


class Persona(Record, Base):
    __tablename__ = "personas"
    role: Mapped[str]
    name: Mapped[str]
    email: Mapped[str]


class License(Record, Base):
    __tablename__ = "licenses"
    artist_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    studio_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    title: Mapped[str]
    status: Mapped[str] = mapped_column(default="DRAFT")
    version: Mapped[int] = mapped_column(default=1)
    terms: Mapped[dict] = mapped_column(JSON, default=dict)
    pages: Mapped[list] = mapped_column(JSON, default=list)
    contract_path: Mapped[str | None]
    contract_hash: Mapped[str | None]
    extraction_provider: Mapped[str] = mapped_column(default="not_run")
    error: Mapped[str | None]
    approved_at: Mapped[str | None]


class LicenseVersion(Record, Base):
    __tablename__ = "license_versions"
    __table_args__ = (UniqueConstraint("license_id", "version"),)
    license_id: Mapped[str] = mapped_column(ForeignKey("licenses.id"))
    version: Mapped[int]
    terms: Mapped[dict] = mapped_column(JSON)
    approved_by: Mapped[str] = mapped_column(ForeignKey("personas.id"))


class ReferenceVoice(Record, Base):
    __tablename__ = "reference_voices"
    artist_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    path: Mapped[str]
    file_hash: Mapped[str]
    consent: Mapped[bool]
    metadata_json: Mapped[dict] = mapped_column(JSON)


class Asset(Record, Base):
    __tablename__ = "media_assets"
    __table_args__ = (UniqueConstraint("license_id", "file_hash"),)
    license_id: Mapped[str] = mapped_column(ForeignKey("licenses.id"))
    studio_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    license_version: Mapped[int]
    campaign: Mapped[dict] = mapped_column(JSON)
    original_name: Mapped[str]
    path: Mapped[str]
    normalized_path: Mapped[str | None]
    file_hash: Mapped[str]
    status: Mapped[str] = mapped_column(default="UPLOADED")
    error: Mapped[str | None]


class Analysis(Record, Base):
    __tablename__ = "audio_analyses"
    asset_id: Mapped[str] = mapped_column(ForeignKey("media_assets.id"), unique=True)
    result: Mapped[dict] = mapped_column(JSON)


class UsageAuthorization(Record, Base):
    __tablename__ = "usage_authorizations"
    asset_id: Mapped[str] = mapped_column(ForeignKey("media_assets.id"), unique=True)
    artist_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    license_version: Mapped[int]
    evidence_hash: Mapped[str]
    identity_confirmed: Mapped[bool]
    use_authorized: Mapped[bool]
    note: Mapped[str]


class OverlapReview(Record, Base):
    __tablename__ = "overlap_reviews"
    asset_id: Mapped[str] = mapped_column(ForeignKey("media_assets.id"), index=True)
    related_asset_id: Mapped[str] = mapped_column(ForeignKey("media_assets.id"))
    license_id: Mapped[str] = mapped_column(ForeignKey("licenses.id"), index=True)
    license_version: Mapped[int]
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    decision: Mapped[str]
    note: Mapped[str]
    evidence_hash: Mapped[str]
    canonical_asset_id: Mapped[str] = mapped_column(ForeignKey("media_assets.id"))
    previous_id: Mapped[str | None] = mapped_column(ForeignKey("overlap_reviews.id"))


class RoyaltyApproval(Record, Base):
    __tablename__ = "royalty_approvals"
    __table_args__ = (UniqueConstraint("royalty_id", "evidence_hash"),)
    royalty_id: Mapped[str] = mapped_column(ForeignKey("royalty_entries.id"))
    artist_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    evidence_hash: Mapped[str]
    note: Mapped[str]


class Report(Record, Base):
    __tablename__ = "compliance_reports"
    asset_id: Mapped[str] = mapped_column(ForeignKey("media_assets.id"), unique=True)
    status: Mapped[str]
    result: Mapped[dict] = mapped_column(JSON)


class Royalty(Record, Base):
    __tablename__ = "royalty_entries"
    asset_id: Mapped[str] = mapped_column(ForeignKey("media_assets.id"), unique=True)
    artist_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    studio_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    license_id: Mapped[str] = mapped_column(ForeignKey("licenses.id"))
    amount: Mapped[str]
    currency: Mapped[str]
    status: Mapped[str] = mapped_column(default="PENDING")
    calculation: Mapped[dict] = mapped_column(JSON)
    decision_note: Mapped[str | None]
    decided_at: Mapped[str | None]


class Invoice(Record, Base):
    __tablename__ = "invoices"
    royalty_id: Mapped[str] = mapped_column(ForeignKey("royalty_entries.id"), unique=True)
    provider_id: Mapped[str] = mapped_column(unique=True)
    provider: Mapped[str] = mapped_column(default="mock")
    simulated: Mapped[bool] = mapped_column(default=True)
    artist_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    studio_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    recipient: Mapped[str]
    amount: Mapped[str]
    currency: Mapped[str]
    status: Mapped[str] = mapped_column(default="DRAFT")


class PaymentEvent(Record, Base):
    __tablename__ = "payment_events"
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"))
    event_key: Mapped[str] = mapped_column(unique=True)
    kind: Mapped[str]
    actor_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    simulated: Mapped[bool] = mapped_column(default=True)


class SandboxInvoiceDetail(Record, Base):
    __tablename__ = "sandbox_invoice_details"
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), unique=True)
    merchant_key: Mapped[str]
    issuer: Mapped[str]
    invoice_number: Mapped[str]
    provider_status: Mapped[str] = mapped_column(default="DRAFT")
    payment_url: Mapped[str | None]
    due_date: Mapped[str | None]
    paid_amount: Mapped[str] = mapped_column(default="0.00")
    due_amount: Mapped[str | None]
    refunded_amount: Mapped[str] = mapped_column(default="0.00")
    last_synced_at: Mapped[str | None]
    provider_updated_at: Mapped[str | None]
    error: Mapped[str | None]
    transactions: Mapped[list] = mapped_column(JSON, default=list)


class PaymentOperation(Record, Base):
    """Durable claim saved BEFORE a remote write; uncertain writes reconcile without replay."""

    __tablename__ = "payment_operations"
    __table_args__ = (UniqueConstraint("royalty_id", "provider", "kind"),)
    royalty_id: Mapped[str] = mapped_column(ForeignKey("royalty_entries.id"))
    provider: Mapped[str] = mapped_column(default="paypal_sandbox")
    kind: Mapped[str]
    state: Mapped[str] = mapped_column(default="PREPARED")
    merchant_key: Mapped[str]
    evidence_hash: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    remote_id: Mapped[str | None]
    error: Mapped[str | None]


class WebhookReceipt(Record, Base):
    __tablename__ = "paypal_webhook_receipts"
    event_id: Mapped[str] = mapped_column(unique=True)
    invoice_id: Mapped[str | None] = mapped_column(ForeignKey("invoices.id"))
    event_type: Mapped[str]
    state: Mapped[str] = mapped_column(default="VERIFIED")
    error: Mapped[str | None]


class Audit(Record, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[str] = mapped_column(ForeignKey("personas.id"))
    artist_id: Mapped[str]
    studio_id: Mapped[str]
    action: Mapped[str]
    entity_id: Mapped[str]
    detail: Mapped[dict] = mapped_column(JSON, default=dict)


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False, "timeout": 60})


@event.listens_for(engine, "connect")
def sqlite_pragmas(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")


def get_session():
    with Session(engine, expire_on_commit=False) as session:
        # Serialize local transactions, including allowance allocation and idempotency checks.
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def serialize(record) -> dict:
    return {column.name: getattr(record, column.name) for column in record.__table__.columns}
