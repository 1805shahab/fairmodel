# FairModel — submission preparation

Current routing update (November 10): FairModel is one application. `/` introduces the product and opens the same `/dashboard`; `/control-room` redirects there; the former fictional preview is retired. Artist/studio roles share the working UI. Standard backend startup selects actual PayPal Sandbox, with default-off draft/send writes; local simulation requires `-MockPayments`. Historical preview descriptions below document earlier milestones, not a second available app. See docs/APP_WORKFLOW.md.

**Project:** AI Voice Licensing, Compliance & Royalty Payments

**Tagline:** Every voice deserves a fair share.

**Event:** Build What's Next with PayPal and AI

**Owner-provided target deadline:** November 12, 2026, 12:00 PM PST (November 13, 1:00 AM Pakistan time). The real PayPal Sandbox requirement is still outstanding. See [PAYPAL_INTEGRATION_READINESS.md](PAYPAL_INTEGRATION_READINESS.md).

## Problem and product

Voice artists need clear permission boundaries and understandable compensation when studios use synthetic voices. Studios need a practical way to check campaigns against licensed rights. FairModel connects agreement review, actual media measurements, AI-assisted content assessment, deterministic usage pricing, artist approval and invoice history.

The product supports fictional Artist and Studio demo personas. Contracts stay human approved; AI output is evidence, not legal authority. Audio alone cannot establish geographic distribution, actual publication, unauthorized use or cloning.

## Implemented development scope

- Next.js/React/TypeScript/Tailwind responsive single application: role-specific artist/studio dashboards, license workflow, upload/review, media analysis, compliance report, royalties, invoices, AG Grid Community analytics, references, audit and integration status.
- FastAPI, validated schemas, SQLAlchemy/SQLite, versioned approvals, private local uploads, explicit ownership checks and consistent REST operations.
- Real text extraction from PDF pages; real Gemini SDK contract/content adapters; exact citation validation and unknown-term review.
- Real ffprobe/FFmpeg format validation, normalization and metadata; lightweight speech activity measurement; real Groq transcription adapter with segment timestamps.
- Decimal royalty engine, per-asset and cumulative semantics, safe restricted/review outcomes, artist decisions and duplicate protection.
- Independent live-by-default transcription/compliance controls, persisted provider provenance, safe provider errors without fixture fallback, and evidence-bound artist identity/usage attestation before any proposal. Speaker similarity remains optional and never proves authorization.
- Compliance policy v3 adds documented medium/category equivalences, source-backed rule outcomes, deterministic routing of administrative/metadata/content/human-review conditions, exact missing-clause citation recovery, successful-response receipts and conservative duplicate/excerpt review. No AI interpretation can expand approved distribution permissions. See [COMPLIANCE_RULES.md](COMPLIANCE_RULES.md).
- Policy v4 completes artist overlap resolution with paired playback/evidence, append-only same/separate/uncertain decisions, canonical usage, stale-input protection and reconciliation holds. Charge approvals are bound to reviewed inputs; processing/compliance/manual authorization/payment states are separate. Schema v3 is additive with a verified backup and preserved original records.
- Repeatable first-party A/B/C judging scenarios use actual local media/VAD, explicit offline AI and scripted fixture-only attestations. Current B measures 58.77s speech and USD 57.54, with a clearly simulated artist-approved invoice. Seed reruns preserve IDs/history. See [DEMO_GUIDE.md](DEMO_GUIDE.md), [DEMO_SCRIPT.md](DEMO_SCRIPT.md) and [TESTING.md](TESTING.md).
- Persistent MockPaymentProvider invoices and deduplicated events. Mock payment views explicitly disclose simulation; actual Sandbox invoices carry the distinct test-transaction notice.
- Optional speaker CLI isolated from core dependencies. No model downloaded or inference verified; no invented scores.

## PayPal: implemented, live financial verification outstanding

The owner authorized Sandbox integration. OAuth and read-only Invoicing access succeeded with actual backend credentials. Implemented code covers draft creation, separate artist send, authoritative status refresh, actual returned hosted links, partial/pending/refund handling, durable uncertain-operation reconciliation and signature-verified idempotent webhooks. Mock remains separate. No production APIs or real-money flow exist.

**This is not yet a completed Sandbox end-to-end submission.** Actual draft creation, sending and manual buyer payment have not been authorized/performed. Webhook delivery is not configured or live-tested. These remain critical before claiming PayPal completion. See [the readiness checklist](PAYPAL_INTEGRATION_READINESS.md) and [manual testing guide](PAYPAL_SANDBOX_TESTING.md).

APIMatic PayPal Context Plugin 0.4.1 was installed and its guidance read/used. Its SDK map does not cover Invoicing v2; the app uses official REST schemas through existing HTTPX. AG Grid Community provides actual-record ledger filtering/export. A placeholder Postman collection is prepared, not executed in Postman. [Sponsor evidence](SPONSOR_INTEGRATIONS.md) distinguishes these contributions.

## Verification honesty

Consult PLAN.md for exact verified check results. Automated provider tests mock external responses and exercise validation/failure paths. Real local PDF parsing, FFmpeg normalization, VAD and file playback are tested separately and in the fixture workflow. Fixture content is first-party, explicitly selected and hash matched; it is not a successful live API call.

Live Gemini contract extraction/content assessment and Groq transcription passed service smoke checks with owner-configured credentials on November 6, 2026, with fixture mode disabled. Gemini uses the verified `gemini-3.1-flash-lite` replacement after the original 2.5 model returned 404. The final manual browser judging run should also use real providers and explicit artist approvals. Actual SpeechBrain inference is not verified. No production authentication, cloud deployment or external payment has been performed. The owner has separately authorized publishing the project's source to GitHub.

Live adapters were reverified November 9, 2026. The sample Gemini content response included a finding and uncertainty; successful API execution does not mean compliant usage. A separate live Gemini request on a saved live-Groq asset used approved database version 4, persisted a restricted report and created no royalty. Updated automated browser checks cover offline media analysis, explicit artist review, simulated settlement and a failed live request displayed without substituting fixture success. See [the pipeline audit](AUDIO_COMPLIANCE_REVIEW.md).

## Suggested judging pitch

“FairModel makes AI voice licensing inspectable. Artists approve source-backed terms. Studios submit actual campaign audio. AI provides content evidence while deterministic rules explain every cent. Artist approval gates invoicing. The Sandbox adapter has passed OAuth and read-only API checks; draft, sending and buyer-payment verification are pending. Historical simulated payments stay clearly labeled.”

Only after an actual paid Sandbox case is verified should the video claim end-to-end PayPal settlement. Use the live variant in [DEMO_SCRIPT.md](DEMO_SCRIPT.md), without presenting an unfinished step as completed.

Do not substitute the pitch for actual live provider evidence. Recording/script: [DEMO_GUIDE.md](DEMO_GUIDE.md). Setup: [API_SETUP.md](API_SETUP.md).
