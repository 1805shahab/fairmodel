# FairModel — submission preparation

**Project:** AI Voice Licensing, Compliance & Royalty Payments

**Tagline:** Every voice deserves a fair share.

**Event:** Build What's Next with PayPal and AI

## Problem and product

Voice artists need clear permission boundaries and understandable compensation when studios use synthetic voices. Studios need a practical way to check campaigns against licensed rights. FairModel connects agreement review, actual media measurements, AI-assisted content assessment, deterministic usage pricing, artist approval and invoice history.

The product supports fictional Artist and Studio demo personas. Contracts stay human approved; AI output is evidence, not legal authority. Audio alone cannot establish geographic distribution, actual publication, unauthorized use or cloning.

## Implemented development scope

- Next.js/React/TypeScript/Tailwind responsive application: landing, two persona dashboards, license workflow, upload/review, media analysis, compliance report, royalties, invoices, AG Grid Community analytics, references, audit and integration status.
- FastAPI, validated schemas, SQLAlchemy/SQLite, versioned approvals, private local uploads, explicit ownership checks and consistent REST operations.
- Real text extraction from PDF pages; real Gemini SDK contract/content adapters; exact citation validation and unknown-term review.
- Real ffprobe/FFmpeg format validation, normalization and metadata; lightweight speech activity measurement; real Groq transcription adapter with segment timestamps.
- Decimal royalty engine, per-asset and cumulative semantics, safe restricted/review outcomes, artist decisions and duplicate protection.
- Persistent MockPaymentProvider invoices and deduplicated events. All payment views explicitly disclose simulation.
- Optional speaker CLI isolated from core dependencies. No model downloaded or inference verified; no invented scores.

## Critical outstanding requirement: PayPal

**This is not yet a completed PayPal hackathon submission.** The user's PayPal Developer account access issue is external and intentionally does not block application development. The current app makes **no PayPal API requests** and contains **no real PayPal integration success claim**.

Once the owner confirms account access and explicitly authorizes the phase, implement:

1. PayPal Sandbox OAuth with backend-only credentials and safe token handling.
2. Invoicing v2 draft creation from approved immutable royalty records, with durable idempotency keys.
3. Actual sandbox invoice sending and provider status retrieval.
4. Signature-verified payment notifications, unique event IDs and replay protection.
5. Invoice/amount/currency/recipient reconciliation and auditable provider state mappings.
6. A real sandbox end-to-end demonstration with clear distinction from simulated historical records.

The existing PaymentProvider interface isolates this future work. UI domain records remain provider-neutral, and every invoice stores provider/simulation provenance. The manual simulated completion action must remain mock-only.

## Verification honesty

Consult PLAN.md for exact verified check results. Automated provider tests mock external responses and exercise validation/failure paths. Real local PDF parsing, FFmpeg normalization, VAD and file playback are tested separately and in the fixture workflow. Fixture content is first-party, explicitly selected and hash matched; it is not a successful live API call.

Live Gemini contract extraction/content assessment and Groq transcription passed service smoke checks with owner-configured credentials on November 6, 2026, with fixture mode disabled. Gemini uses the verified `gemini-3.1-flash-lite` replacement after the original 2.5 model returned 404. The final manual browser judging run should also use real providers and explicit artist approvals. Actual SpeechBrain inference is not verified. No production authentication, cloud deployment or external payment has been performed. The owner has separately authorized publishing the project's source to GitHub.

## Suggested judging pitch

“FairModel makes AI voice licensing inspectable. Artists approve source-backed terms. Studios submit actual campaign audio. The platform measures speech, assesses possible content conflicts, and explains every cent with deterministic arithmetic. Artists review charges before settlement. Our current local build uses explicit simulated invoices; the final submission requires the real PayPal Sandbox adapter once account access is restored.”

Do not substitute the pitch for actual live provider evidence. Recording/script: [DEMO_GUIDE.md](DEMO_GUIDE.md). Setup: [API_SETUP.md](API_SETUP.md).
