# Architecture

## Application boundary

The Next.js browser application calls same-origin `/api/backend/*` route handlers. These proxy to a fixed, server-configured FastAPI origin, forward the selected demo persona, preserve media range headers, and stream private audio/PDF responses. Browser requests cannot choose an arbitrary upstream host. No provider credentials enter frontend code.

FastAPI owns SQLite records, local private uploads, schema validation, provider calls, royalty allocation and invoice state transitions. `app/ai.py`, `app/audio.py`, `app/royalties.py`, and `app/payments.py` isolate the major services. `app/main.py` composes them into REST endpoints; route handlers enforce ownership and transactions.

## Data model

- Persona: fictional Artist or Studio profile. Profile and demo user are combined for this MVP.
- License: assigned artist/studio, source PDF/hash, page text, extracted/edited terms, processing state, extraction provenance and current version.
- LicenseVersion: immutable approved term snapshot and approver. Asset evaluation uses the approved version captured at upload.
- ReferenceVoice: private reference, consent, content hash, measured metadata, artist ownership.
- Asset → Analysis → Report: original file/hash, campaign declarations, audio metadata/VAD/transcript/provider, explainable compliance outcome.
- Asset → Royalty → Invoice → PaymentEvent: unique asset allocation, exact string-serialized Decimal amount and explanation, unique invoice per royalty, deduplicated event keys.
- Audit: actor, ownership scope, action, record, timestamp and concise context. No raw contract/transcript/audio is logged in audit entries.

Foreign keys and unique constraints enforce relationships and idempotency. Financial amounts/durations are persisted as decimal strings to avoid SQLite float conversion. Terms and provider evidence use validated JSON snapshots. All timestamps use UTC ISO strings; UI displays dates in Asia/Karachi.

## Contract workflow

Create draft → upload verified `%PDF-` text PDF → extract page text → select live Gemini or explicit matching fixture → validate Pydantic output and exact source citations → artist edits/reviews → optimistic version check → approve immutable snapshot. Invalid quotes and uncited rules produce review ambiguities. Unknown clauses remain null. Extraction never activates a license. Human edits are attributed by required audit notes; source quotes remain original extraction evidence and may need rechecking after edits.

The Gemini system instruction treats every contract, transcript and metadata field as untrusted data and forbids obeying embedded instructions. The model has no tools. Schema validation and evidence checking reduce risk; human approval and deterministic downstream rules provide the authority boundary. This is not a claim that prompt injection is solved.

## Audio and AI

Actual file content is decoded/probed locally, then normalized to 16kHz mono PCM16. Supported containers: WAV, MP3 and M4A; single audio stream, no video. WebRTC VAD mode 2 analyzes 30ms frames and records segments plus estimated spoken duration. No neural speaker model is downloaded by the core.

Groq Whisper Large V3 Turbo receives the normalized local audio, returns text and segment timestamps when available, and records provider/model provenance. Gemini assesses possible conflicts between that transcript and approved restrictions. Provider failures persist a safe error and produce explicit retry actions. Exception internals are not returned or logged. No network error triggers demo fallback.

Fixtures require an explicit checkbox/API parameter and exact SHA-256 matching. The fixture manifest is generated from our own sample document and stock-TTS script. Changed content restrictions invalidate the fixture's favorable content assessment. Reports record `demo_fixture (not Gemini)` / `demo_fixture (not Groq)` and never claim live success.

## Compliance and finance

Deterministic compliance combines approved scope, dates, metadata, VAD measurement, content findings and optional verification availability. Declared scope violations → RESTRICTED_USAGE; uncertain/missing clauses, measurements, possible AI conflicts or special conditions → NEEDS_REVIEW. These paths create no royalty allocation or invoice. Otherwise, positive additional charge → ADDITIONAL_ROYALTY_DUE, zero → COMPLIANT.

`royalties.calculate()` has no AI, database or payment dependency. Formula: `max(0, spoken_seconds - remaining_allowance) × rate`. Per-asset allowance resets. Cumulative remaining allowance subtracts prior permitted persisted allocations. The full calculation uses Decimal; only final money is rounded HALF_UP to cents. Persisted zero-charge entries reserve included cumulative usage. Rejecting a charge does not retroactively restore already-consumed duration.

SQLite transactions begin IMMEDIATE so parallel requests cannot simultaneously reserve allowance, allocate the same asset, or create duplicate invoices. Raw file hashes deduplicate within each license. Transcoded versions are not perceptually fingerprinted. Evaluation, analysis and royalty creation are idempotent by asset ID; invoices by royalty ID; payment events by global event key plus operation identity.

## Payment boundary

`PaymentProvider`: create/send/get/list invoice, get payment status and record payment event. `MockPaymentProvider` implements persistent DRAFT → SENT → PAID_SIMULATED with ownership, amount/approval checks and event history. Sending is only a local state transition; no email is sent. The studio deliberately simulates completion.

`PayPalSandboxProvider` is an isolated non-operational adapter. Configuration explicitly rejects `PAYMENT_PROVIDER=paypal`. No OAuth, PayPal endpoint, fabricated response or webhook handler exists. Future provider work must add durable PayPal request IDs, OAuth token handling, Invoicing v2 mapping, status reconciliation, signature verification, provider/currency/amount validation and unique webhook IDs. The simulation route remains mock-only. `PAID_SIMULATED` must never be treated as a real paid state.

## Development schema and operations

Schema version 1 is managed with SQLAlchemy `create_all` plus SQLite `user_version`. Unrecognized versions refuse startup. Future changes need explicit migrations and backups; `create_all` does not alter existing columns. Storage and DB files are private local ignored artifacts, never served by a static directory mount. Back up both together.

Synchronous provider calls run in FastAPI's thread pool. The local SQLite write lock intentionally favors correctness over throughput. Long jobs, durable processing queues, production session identity, multi-tenant deployment, object storage and retention jobs remain future work. Demo servers bind only to loopback.

The isolated `optional-speaker/verify.py` CLI uses CPU ECAPA-TDNN only when installed and invoked separately. Fetching is offline by default; network model download requires an explicit CLI flag. A real score is emitted only after inference; failures return unavailable with no score. The threshold is explicitly uncalibrated. This worker is not integrated into billing; enabling the core feature flag reports unavailable and requires review until independently validated.
