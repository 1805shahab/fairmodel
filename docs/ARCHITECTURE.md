# Architecture

## Optional Render Free demonstration

The root Dockerfile builds Next.js standalone only for the hosted image, then
packages Node, Python 3.12 and FFmpeg together. A small supervisor runs FastAPI
on loopback and Next.js on Render's public port, stops both on termination, and
fails if either process fails. Existing domain/provider services are unchanged.
A shared HTTP password gate protects pages and API handlers; it is a restricted
demo entrance, not production identity. The public health endpoint exposes only
readiness and checks no external providers. Temporary cloud storage is isolated;
no local records or media enter the image. Because Render Free erases local
files on idle/restart/redeploy, PayPal draft/send are blocked here. Original local
financial history remains local. See [deployment limits and steps](RENDER_DEPLOYMENT.md).

Fish addition (schema 7): grants/jobs are provider-bound. Legacy records remain Gemini; Fish requires separate transfer/retention consent and an artist-reviewed reference transcript. Its free-only adapter uses inline MessagePack references, creates no profiles, never retries/switches providers, and hands validated audio to the existing review/financial pipeline. Backed-up transactional migration expands grant uniqueness by provider without changing IDs/history. See [Fish details](FISH_AUDIO.md).

November 11 voice-generation addition: schema 6 adds `VoiceGrant` and `SpeechGeneration` without modifying existing tables. Artist grants bind an owned reference plus separate adult-speaker consent clip to one exact approved license version and assigned studio. `voice_routes.py` enforces ownership, deterministic scope, durable idempotent intents and pre/post-provider grant validation; `voice_generation.py` uses maintained Google GenAI Voices/Interactions with stateless replication and discards the ephemeral voice key. A validated WAV becomes an ordinary UPLOADED asset for existing Groq/VAD/Gemini/artist authorization and Decimal royalty services. Generation never approves identity, compliance, financial charges or invoices. No comparison-only consent is upgraded. See [GEMINI_VOICE_WORKFLOW.md](GEMINI_VOICE_WORKFLOW.md) for retention, failure and verification limits.

## Product presentation - November 10, 2026

The working workspace uses a responsive sidebar and semantic tokens in `frontend/app/workspace-theme.css`. Controlled recording tabs separate processing, compliance, authorization and finance. Hidden panels stay mounted during tab changes; data refreshes retain the selected tab. Timestamp buttons seek the native audio element. Invoice filtering uses returned records only; provider confirmation payloads, writes and evidence checks remain unchanged. Both `/` and the retired `/control-room` route redirect to the single working `/dashboard`. This redesign requires no schema or provider changes; see DESIGN.md.

## Application boundary

The Next.js browser application calls same-origin `/api/backend/*` route handlers. These proxy to a fixed, server-configured FastAPI origin, forward the selected demo persona, preserve media range headers, and stream private audio/PDF responses. Browser requests cannot choose an arbitrary upstream host. No provider credentials enter frontend code.

FastAPI owns SQLite records, local private uploads, schema validation, provider calls, royalty allocation and invoice state transitions. `app/ai.py`, `app/audio.py`, `app/royalties.py`, and `app/payments.py` isolate the major services. `app/main.py` composes them into REST endpoints; route handlers enforce ownership and transactions.

The former cinematic preview route no longer imports its experience component, sample store or visual scenes. It redirects to `/dashboard`. Legacy preview source remains in the repository as reference, without a user-facing route or navigation entry. No sample events, rates or simulated decisions are merged into application records. The same workspace serves both roles and all configured real providers; test data and the mock payment adapter remain explicit development tools.

## Data model

The working workspace uses neutral/teal product tokens in `app/workspace-theme.css`, with a navy sidebar and responsive role selector. API-backed forms, versioned approvals, audio reports, overlap decisions and invoice actions use the existing backend. AG Grid Community renders actual ledger rows. The Postman download route serves a fixed credential-free source collection, never an arbitrary file path. The standard backend launcher selects Sandbox with process-scoped variables; explicit `-MockPayments` selects simulation, with no failure fallback and no automatic financial operation.

- Persona: fictional Artist or Studio profile. Profile and demo user are combined for this MVP.
- License: assigned artist/studio, source PDF/hash, page text, extracted/edited terms, processing state, extraction provenance and current version.
- LicenseVersion: immutable approved term snapshot and approver. Asset evaluation uses the approved version captured at upload.
- ReferenceVoice: private reference, consent, content hash, measured metadata, artist ownership.
- Asset → Analysis → Report: original file/hash, campaign declarations, audio metadata/VAD/transcript/provider, explainable compliance outcome.
- UsageAuthorization: explicit artist identity/usage attestation bound by a SHA-256 digest to asset ID/file hash, campaign metadata, analysis evidence and approved contract version. It is manual review, not speaker-model inference.
- OverlapReview: append-only artist pair decision, evidence hash of both analyses/campaigns/approved version, reviewer/note/timestamp, canonical snapshot and prior-decision link. Same-usage edges only point toward earlier assets; union groups reject contradictory separate relationships.
- RoyaltyApproval: append-only charge approval proof bound to the current report input hash. Reaffirming a changed charge adds proof; it does not rewrite invoice history.
- Asset → Royalty → Invoice → PaymentEvent: unique asset allocation, exact string-serialized Decimal amount and explanation, unique invoice per royalty, deduplicated event keys.
- Audit: actor, ownership scope, action, record, timestamp and concise context. No raw contract/transcript/audio is logged in audit entries.

Foreign keys and unique constraints enforce relationships and idempotency. Financial amounts/durations are persisted as decimal strings to avoid SQLite float conversion. Terms and provider evidence use validated JSON snapshots. All timestamps use UTC ISO strings; UI displays dates in Asia/Karachi.

## Contract workflow

Create draft → upload verified `%PDF-` text PDF → extract page text → select live Gemini or explicit matching fixture → validate Pydantic output and exact source citations → artist edits/reviews → optimistic version check → approve immutable snapshot. Invalid quotes and uncited rules produce review ambiguities. Unknown clauses remain null. Extraction never activates a license. Human edits are attributed by required audit notes; source quotes remain original extraction evidence and may need rechecking after edits.

The Gemini system instruction treats every contract, transcript and metadata field as untrusted data and forbids obeying embedded instructions. The model has no tools. Schema validation and evidence checking reduce risk; human approval and deterministic downstream rules provide the authority boundary. This is not a claim that prompt injection is solved.

## Audio and AI

Actual file content is decoded/probed locally, then normalized to 16kHz mono PCM16. Supported containers: WAV, MP3 and M4A; single audio stream, no video. WebRTC VAD mode 2 analyzes 30ms frames and records segments plus estimated spoken duration. No neural speaker model is downloaded by the core.

Groq Whisper Large V3 Turbo receives the normalized local audio, returns text and segment timestamps when available, and records provider/model provenance. Gemini assesses possible conflicts between that transcript and approved restrictions. Provider failures persist a safe error and produce explicit retry actions. Exception internals are not returned or logged. No network error triggers demo fallback.

Fixtures require an explicit development/testing selection/API parameter and exact SHA-256 matching. The fixture manifest is generated from our own sample document and stock-TTS script. Changed content restrictions invalidate the fixture's favorable content assessment. Reports record `demo_fixture (not Gemini)` / `demo_fixture (not Groq)` and never claim live success. Audio transcription and compliance provider choices are independent and default to live. Cached fixture evidence cannot satisfy a live-provider request. A failed replacement keeps old evidence visibly labeled, records a safe upstream HTTP status/category and holds charge eligibility; it never returns fixture success.

## Compliance and finance

Evaluation reads the immutable `LicenseVersion` matching both the asset's license ID and captured version, validates artist approval/active assignment, and persists a digest of those terms. Frontend-supplied terms cannot replace that snapshot. Deterministic compliance combines approved medium, territory, dates, language, campaign/category, VAD measurement, transcript findings and explicit artist identity/usage review. Supported scope violations → RESTRICTED_USAGE; unresolved identity/authorization, unknown clauses, uncertain measurements, possible AI conflicts or unsupported special conditions → NEEDS_REVIEW. Recognized administrative conditions use workflow receipts and stage-specific approval guards. These paths can show an estimate but create no new royalty allocation. Otherwise, positive additional charge → ADDITIONAL_ROYALTY_DUE, zero → COMPLIANT. Artist charge approval is a separate step.

Policy version 4 binds eligibility to stable business evidence, approved terms, source/workflow/overlap decisions and manual review. Provider response IDs/timestamps and display notes do not change the reviewed usage. Metadata/transcript/measurement changes invalidate dependent decisions; identical saves are idempotent and unchanged reanalysis preserves valid review. Legacy full-evidence hashes are accepted while their original evidence remains unchanged. Approval/invoice/send operations recheck current evidence-bound eligibility and explicit charge-approval proof. Optional speaker scores cannot substitute for authorization. `ANALYZED`, compliance, attestation, royalty and invoice states are independent API fields, with a derived workflow stage/next action.

Same-usage groups use the earliest canonical asset and allocate once. Separate decisions retain independent per-asset/cumulative semantics; uncertain/stale decisions hold new allocations. Multiple historical allocations in one group, noncanonical historical charges or longer edited speech require reconciliation; no charges/invoices are deleted. Uncertain/separate incoming excerpts do not revoke the original's independently valid approval. Cumulative reconciliation holds dependent new allocations. A current saved content assessment can be reused for changed workflow checks with its original provider receipt; explicit reprocessing requests real AI, and failed requests never trigger cached-fixture fallback. Normalization/citation/content routing is documented in [COMPLIANCE_RULES.md](COMPLIANCE_RULES.md).

`royalties.calculate()` has no AI, database or payment dependency. Formula: `max(0, spoken_seconds - remaining_allowance) × rate`. Per-asset allowance resets. Cumulative remaining allowance subtracts prior permitted persisted allocations. The full calculation uses Decimal; only final money is rounded HALF_UP to cents. Persisted zero-charge entries reserve included cumulative usage. Rejecting a charge does not retroactively restore already-consumed duration.

SQLite transactions begin IMMEDIATE so parallel requests cannot simultaneously reserve allowance, allocate the same asset, or create duplicate invoices. Raw file hashes deduplicate within each license. Transcoded versions are not perceptually fingerprinted. Evaluation, analysis and royalty creation are idempotent by asset ID; invoices by royalty ID; payment events by global event key plus operation identity.

## Payment boundary

`PaymentProvider`: create/send/get/list invoice, get payment status and record payment event. `MockPaymentProvider` implements persistent DRAFT → SENT → PAID_SIMULATED with ownership, amount/approval checks and event history. Sending is only a local state transition; no email is sent. The studio deliberately simulates completion.

`PayPalSandboxProvider` implements real Invoicing v2 through pooled HTTPX pinned to `api-m.sandbox.paypal.com`. Backend OAuth tokens are cached and refreshed near expiry. Bounded GET retries and one unauthorized-token refresh are separate from financial POST handling; failures never switch providers. Creation/sending are separately disabled by default and require per-case confirmation. All invoices use the configured merchant and Sandbox buyer; arbitrary artist onboarding is outside this MVP. Initial support is USD only.

Schema-4 `PaymentOperation` uniquely claims each royalty/provider/create-or-send intent. Frozen payload and INFLIGHT state commit before a remote write. Ambiguous outcomes become UNKNOWN. Retrying reconciles by saved provider ID or exact invoice number/reference search; no match does not authorize another create. The official Invoicing create/send definitions do not advertise PayPal-Request-Id, so correctness does not depend on an invented idempotency guarantee. Current artist approval/eligibility is rechecked after journal checkpoints. Historical invoices and approved amounts remain unchanged.

`SandboxInvoiceDetail` stores provider status, sanitized payment rows, paid/due/refunded totals, sync timestamps, actual trusted Sandbox link and safe errors. Currency, amount, issuer, recipient and reference must match the frozen intent. PAID requires authoritative GET status, matching paid total, zero due/refund and PayPal transaction evidence. Pending/partial/manual-external/refund states remain distinct; stale snapshots cannot roll back established settlement/refund evidence. Failed refresh preserves last good state and displays its error.

Signature verification uses PayPal's official verification endpoint and configured webhook ID. Unique `WebhookReceipt` IDs prevent replay; events trigger current GET reconciliation, never event-named settlement. A hidden service actor distinguishes webhook processing from artist decisions. No public endpoint/tunnel is configured; direct status refresh works independently. Each invoice routes by stored provider; simulation remains mock-only. Live verification currently covers OAuth/read-only listing, not create/send/settlement.

## Development schema and operations

Current schema 5 adds only `EvidenceRevision`, `UsageCase` and `CaseEvent`, after backup, and captures then-current evidence; earlier overwritten revisions are unavailable. Passports are private joined projections with no provider calls/writes. Case state enters compliance/approval hashes only when cases exist, preserving untouched assets' existing hashes. Open/stale cases (including canonical usage) hold financial actions; resolution requires reevaluation/current approval without changing invoices. The Studio estimator reuses deterministic scope and Decimal rules without usage/financial writes. See [PRODUCT_UPGRADE.md](PRODUCT_UPGRADE.md). The schema-4 payment migration description below is historical.

Schema version 4 is managed by `app/migrations.py` and SQLite `user_version`. Existing databases receive a consistent SQLite backup (including committed WAL data) in ignored `backups/` before upgrade. Version 1 → 2 added `usage_authorizations`; version 2 → 3 only adds `overlap_reviews` and `royalty_approvals`. Version 3 → 4 adds `sandbox_invoice_details`, `payment_operations` and `paypal_webhook_receipts`. No existing columns or financial records are changed. Backup handles close explicitly for Windows. Tests inspect the backup, retained rows and repeat migration behavior. Unrecognized versions refuse startup. Future column changes need explicit migrations; `create_all` does not alter existing columns. Storage and DB files remain private local ignored artifacts. Back up DB/uploads together.

Synchronous provider calls run in FastAPI's thread pool. The local SQLite write lock intentionally favors correctness over throughput. Long jobs, durable processing queues, production session identity, multi-tenant deployment, object storage and retention jobs remain future work. Demo servers bind only to loopback.

The isolated `optional-speaker/verify.py` CLI uses CPU ECAPA-TDNN only when installed and invoked separately. Fetching is offline by default; network model download requires an explicit CLI flag. A real score is emitted only after inference; failures return unavailable with no score. The threshold is explicitly uncalibrated. This worker is not integrated into billing; enabling the core feature flag reports unavailable and requires review until independently validated.
