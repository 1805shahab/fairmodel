from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Evidence(Schema):
    field: str = Field(max_length=100)
    page: int = Field(ge=1)
    quote: str = Field(min_length=1, max_length=2000)


class Terms(Schema):
    artist: str | None = None
    studio: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    permitted_media: list[str] | None = None
    territories: list[str] | None = None
    languages: list[str] | None = None
    campaigns: list[str] | None = None
    included_seconds: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=3)
    billing_basis: Literal["per_asset", "cumulative"] | None = None
    additional_rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=4)
    currency: Literal["USD", "EUR", "GBP"] | None = None
    additional_usage_permitted: bool | None = None
    restricted_categories: list[str] | None = None
    special_conditions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("License end date must follow its start date.")
        return self

    @field_validator("permitted_media", "territories", "languages", "campaigns", "restricted_categories")
    @classmethod
    def valid_rules(cls, value):
        if value is not None and any(not x.strip() or len(x) > 200 for x in value):
            raise ValueError("Rules must be nonempty strings of at most 200 characters.")
        return value


class LicenseCreate(Schema):
    title: str = Field(min_length=3, max_length=160)
    studio_id: str


class ReviewTerms(Schema):
    terms: Terms
    note: str = Field(min_length=5, max_length=2000)
    expected_version: int = Field(ge=1)
    acknowledge_unknowns: bool = False


class Campaign(Schema):
    name: str = Field(min_length=2, max_length=160)
    region: str | None = Field(default=None, max_length=100)
    medium: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    generation_provider: str | None = Field(default=None, max_length=120)
    intended_use_date: date


class Finding(Schema):
    category: str
    passage: str
    explanation: str
    possible_conflict: bool
    needs_review: bool


class ContentFindings(Schema):
    findings: list[Finding]
    uncertainty: list[str]


class Decision(Schema):
    approve: bool
    note: str = Field(min_length=5, max_length=2000)


class PaymentCommand(Schema):
    event_key: str = Field(min_length=8, max_length=120, pattern=r"^[a-zA-Z0-9_-]+$")


class ExtractionCommand(Schema):
    use_demo_fixture: bool = False


class ObjectResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    created_at: str
    updated_at: str


class PersonaResponse(ObjectResponse):
    role: Literal["artist", "studio"]
    name: str
    email: str


class LicenseResponse(ObjectResponse):
    artist_id: str
    studio_id: str
    title: str
    status: Literal["DRAFT", "REVIEW", "ACTIVE"]
    version: int
    terms: Terms
    pages: list[dict]
    contract_hash: str | None
    extraction_provider: str
    error: str | None
    approved_at: str | None
    versions: list[dict] | None = None


class CalculationResponse(Schema):
    spoken_seconds: str
    prior_seconds: str
    included_seconds: str
    allowance_remaining: str
    additional_seconds: str
    rate: str
    amount: str
    currency: str
    billing_basis: Literal["per_asset", "cumulative"]
    rounding: str
    explanation: str


class RoyaltyResponse(ObjectResponse):
    asset_id: str
    artist_id: str
    studio_id: str
    license_id: str
    amount: str
    currency: str
    status: Literal["PENDING", "APPROVED", "REJECTED", "NO_CHARGE"]
    calculation: CalculationResponse
    decision_note: str | None
    decided_at: str | None


class AudioResultResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    duration_seconds: str
    format: str
    sample_rate: int
    channels: int
    spoken_seconds: str | None
    speech_segments: list[dict]
    vad: str
    measurement_uncertain: bool
    measurement_note: str
    transcript: str
    timestamps: list[dict]
    provider: str
    speaker: dict
    demo_fixture: bool


class AnalysisResponse(ObjectResponse):
    asset_id: str
    result: AudioResultResponse


class ComplianceResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: Literal["COMPLIANT", "ADDITIONAL_ROYALTY_DUE", "NEEDS_REVIEW", "RESTRICTED_USAGE"]
    reasons: list[str]
    calculation: CalculationResponse | None
    findings: ContentFindings
    provider: str
    license_version: int
    source_pages: list[Evidence]
    metadata_note: str
    legal_note: str
    evaluated_on: str


class ReportResponse(ObjectResponse):
    asset_id: str
    status: str
    result: ComplianceResponse


class AssetResponse(ObjectResponse):
    license_id: str
    studio_id: str
    license_version: int
    campaign: Campaign
    original_name: str
    file_hash: str
    status: str
    error: str | None
    analysis: AnalysisResponse | None = None
    report: ReportResponse | None = None
    royalty: RoyaltyResponse | None = None


class InvoiceResponse(ObjectResponse):
    royalty_id: str
    provider_id: str
    provider: str
    simulated: bool
    artist_id: str
    studio_id: str
    recipient: str
    amount: str
    currency: str
    status: Literal["DRAFT", "SENT", "PAID_SIMULATED"]
    notice: str
    events: list[dict] | None = None


class ReferenceResponse(ObjectResponse):
    artist_id: str
    file_hash: str
    consent: bool
    metadata_json: dict


class AuditResponse(ObjectResponse):
    actor_id: str
    artist_id: str
    studio_id: str
    action: str
    entity_id: str
    detail: dict


class AnalyticsResponse(BaseModel):
    totals_by_currency: dict[str, dict[str, str]]
    license_count: int
    asset_count: int
    review_count: int
    pending_approvals: int
    rows: list[RoyaltyResponse]
    notice: str
