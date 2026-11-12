# FairModel — submission description and readiness

This is the current submission guide, updated November 12, 2026. Earlier checkpoint notes in other reports are historical; use the current README and PLAN for verified status. This document prepares submission content; it does not submit, publish the repository or upload a video.

**November 13 story update:** [PROJECT_STORY.md](PROJECT_STORY.md) is the latest copy-ready narrative using the requested seven Devpost headings. It explicitly describes the saved successful Fish reference-conditioned generation, the owner's reported voice match and the stock-voice filming choice. The main video is not represented as a fresh cloning request or payment for the newly calculated royalty.

## Project name and tagline

**FairModel — Every voice deserves a fair share.**

## Short description

FairModel connects synthetic voice licensing to explainable usage review and artist-approved royalties. Gemini extracts source-backed contract terms; Groq transcribes real audio; local speech measurements and deterministic rules calculate permitted additional usage. Artists resolve authorization and overlap before genuine PayPal Sandbox invoicing. Every decision keeps its supporting evidence.

## Project description — ready to adapt for the form

### The problem and audience

For a voice artist and a production studio, permission is more specific than “we licensed a voice.” It can depend on campaign, medium, country, dates, content and billable duration. A new edit can resemble an earlier submission. A transcript does not prove consent, and a generated invoice does not prove payment. Keeping those facts in separate files makes review and royalty reconciliation difficult.

FairModel gives artists, studios and rights reviewers one connected workspace to inspect an approved agreement, the actual submitted audio, the reasoning behind a royalty and its payment history.

### What we built

An artist uploads a reference and licensing PDF. Gemini proposes structured terms with genuine page/quotation evidence. The artist reviews, edits and activates a version; AI extraction never activates terms automatically.

A studio supplies campaign metadata and uploads an authorized advertisement, or generates one using a separate provider-specific artist grant. Optional Fish Audio generation uses the exact requested `s2.1-pro-free` model with inline reference audio and a reviewed transcript; it creates no reusable provider voice profile. Reference storage consent never implies cloning consent or consent to another provider.

FFprobe measures the recording, FFmpeg preprocesses it, WebRTC VAD estimates actual speech intervals and Groq Whisper transcribes it. Gemini assesses spoken content against approved restrictions. Deterministic checks handle medium, territory, dates, campaigns, financial clauses and application workflow. Administrative events are checked in the database, not inferred from dialogue. Uncertainty stays visible.

The artist reviews speaker identity and campaign authorization manually, resolves possible overlap and separately approves eligible charges. Shared transcript passages are possible-reuse evidence, not proof of acoustic identity. Same-usage decisions prevent duplicate allocation; conflicting historical records are held for reconciliation rather than erased.

The royalty engine uses Python Decimal and approved contract rules, independently of AI. With 30 included spoken seconds and USD 2 per additional permitted second, 45 accepted spoken seconds produce USD 30.00. Real recordings use their actual measurements; the system does not force a demo amount. Zero additional usage has no payable invoice. Unresolved or restricted usage cannot be automatically invoiced.

The PayPal Sandbox adapter authenticates backend-only and uses Invoicing v2 to create a genuine draft. Sending is a separate confirmed artist action. The studio follows the actual PayPal-hosted link, uses a sandbox buyer and returns to refresh status. Paid status requires authoritative PayPal evidence, not a send button or webhook name. Durable intents, approval revalidation and reconciliation guard against duplicate or uncertain writes.

### Why this is different

FairModel does not stop at generating speech or displaying an AI compliance score. It connects versioned rights, source citations, real speech measurements, reviewable uncertainty, artist control, exact financial calculation and payment reconciliation. Its private Voice Usage Passport and Review Center make the path from permission to payment inspectable.

The app preserves the distinction between audio processing, compliance, identity attestation, financial approval and payment. It does not claim biometric proof, automatic legal judgment or autonomous commerce.

### Tools and how they are used

- **PayPal Developer Platform:** genuine Sandbox OAuth and Invoicing v2, separate draft/send actions, real hosted links and authoritative status synchronization. One configured sandbox merchant issues invoices; arbitrary merchant onboarding/production payments are outside the MVP.
- **Google Gemini / google-genai:** structured contract extraction and advisory transcript content findings, with validation, citations and provider provenance. Optional Gemini replication/TTS is a separate adapter; successful live replication remains unverified after model-access rejection.
- **Groq Whisper Large V3 Turbo:** live speech transcription and available segment timestamps.
- **Fish Audio:** optional consented reference-conditioned ad generation. A saved successful generation is demonstrated; requested-model metadata is not independent served-model or speaker attestation. Free-tier consent/retention limitations remain explicit.
- **FFmpeg, FFprobe and WebRTC VAD:** local validation, normalization, duration and speech intervals. Silero is not the current VAD; optional SpeechBrain is isolated and not required.
- **AG Grid Community:** real royalty ledger filtering, sorting, detail inspection and CSV export. No AG Studio/Enterprise claim.
- **APIMatic PayPal Context Plugin 0.4.1:** installed development guidance actually used for client/authentication, resilience, errors and testing decisions. Its inspected SDK map does not cover Invoicing v2/webhook verification; the runtime uses official REST schemas through HTTPX for those operations.
- **Postman:** guarded, credential-free API collection supplied and structurally validated; execution in the Postman application is not claimed.
- **Render:** owner-deployed password-protected free Docker preview. Temporary storage limits apply; PayPal create/send is blocked on that host. Local operation is the durable payment-demo path.
- **Next.js, React, TypeScript, Tailwind, Radix and Three.js:** the responsive shared artist/studio interface, source review and artwork. The sculpture is explicitly not verification evidence.
- **FastAPI, Pydantic, SQLAlchemy and SQLite:** validated API workflows, versioned evidence, append-only reviews, deterministic finance and operation history.

### Current verified demonstration

The November 12 recording used live Gemini and Groq with original fictional stock-voice materials, real PDF/media processing and manual fictional-demo reviews. Gemini extracted 19 supporting citations. The ad measured 69.613 total seconds and 58.38 VAD speech seconds; the backend calculated USD 56.76 after eligibility review. No invoice was created for this new case. An initial Gemini HTTP 503 remained visible; a deliberate retry succeeded without fixture fallback.

The ending separately refreshes an earlier owner-completed USD 17.46 PayPal Sandbox invoice and displays authoritative `PAID`, USD 17.46 paid and zero outstanding. It does not present the new USD 56.76 example as paid, show a new checkout or initiate another payment. The Fish section shows an earlier saved successful generation, not a new private voice transfer.

The latest recorded code baseline is 384 Python tests, Ruff, frontend TypeScript/ESLint/build and 38 Edge browser checks. Normal tests use mocks/explicit fixtures and isolated storage; they do not establish live API availability. Public webhook delivery and successful live Gemini replication remain unverified.

### Future work

Replace demo personas with real tenant-aware authentication. Add durable storage, tested restore and background processing before accepting sensitive production workloads. Verify public webhooks and more real Sandbox edge cases. Improve ambiguous-clause review, OCR and evaluated acoustic reuse triage. Add retention/export controls and provider agreements. Merchant onboarding and currencies beyond the single-merchant USD Sandbox MVP require deliberate integration and legal/provider review.

## Functional build and submission links

| Requirement | Current deliverable | Owner action before submitting |
| --- | --- | --- |
| Working project | Complete local source and detailed fresh-checkout instructions in [README](../README.md). | Rehearse on a fresh environment and provide any required provider accounts privately. |
| Functional demo | Owner-deployed https://fairmodel.onrender.com, owner-authorized [shared judging login](../README.md#hosted-demo-login), plus reproducible local setup. | Check current reachability/login and disclose shared access, temporary storage and payment-write limits. |
| Public code repository | https://github.com/1805shahab/fairmodel | Public visibility has not been established by this documentation task. Verify logged out; make public only after owner review/authorization. |
| Open-source license | Root [MIT LICENSE](../LICENSE), linked in README; [third-party notices](../THIRD_PARTY_NOTICES.md). | Push the reviewed files when authorized, verify GitHub detects MIT in About, and review rights of all contributors/assets. |
| Tools explained | README integration table and [sponsor evidence](SPONSOR_INTEGRATIONS.md). | Match form selections to actual usage; do not select unused sponsors/features. |
| Under-three-minute video | Local narrated 2:59 1080p MP4 (`FairModel-hackathon-demo-NARRATED-1080p.mp4`) in ignored `output/video/`; the complete owner voiceover is included with pitch-preserving time fit. | Review the final, upload **publicly to YouTube**, and paste the URL here and on the submission form. No public URL has been supplied yet. |
| Media permissions | Original fictional material/stock TTS, original artwork, no added music; provider UI/marks visible. | Confirm rights/permissions for stock voices, marks, visible media and participants. No legal clearance is asserted. |

Local recordings and private proof are deliberately not committed. All first-party source, application assets, locks, environment examples and fixture-generation scripts needed to run the supported workflow should be present; private voice data and API secrets must not be published to satisfy “all source.”

## Three-minute presentation structure

Use the narrated 2:59 edit, not the 5:38 supplemental walkthrough. The owner's entire 3:11.12 voiceover is included at 1.073727× speed with pitch preserved; picture chapters follow the actual recording. Original silent/extended edits are retained. This is the updated pitch structure:

| Time | What judges see | Point to communicate |
| --- | --- | --- |
| 00:00–00:20 | Product and reference upload | Artist control; storage consent is separate from cloning permission. |
| 00:20–00:57 | Live extraction, PDF evidence and activation | Source-backed terms and a human approval boundary. |
| 00:57–01:24 | Campaign/audio form, live Groq and VAD | Real audio; total versus billable speech duration. |
| 01:24–02:00 | Visible provider recovery, compliance and artist review | Honest uncertainty and distinct deterministic/AI/manual evidence. |
| 02:00–02:24 | Royalty approval and saved Fish result | Backend Decimal calculation; explicit generation provenance. |
| 02:24–02:41 | Separate paid Sandbox case refreshed live | Actual PayPal payment evidence, no new payment claimed. |
| 02:41–02:59 | AG Grid, sponsor tooling and closing | One inspectable permission-to-payment workflow. |

Avoid narrating the new case as a paid invoice. Keep test-funds, fictional-demo and provider labels visible. The final passed full decoding, browser seeking/playback and loudness/peak checks. Review narration and private-data exposure yourself, then verify public YouTube access in a logged-out browser after uploading.

## Judging criteria: evidence to emphasize

| Criterion | Specific project evidence |
| --- | --- |
| Technological implementation | Real AI adapters, structured validation, local speech measurements, deterministic finance, evidence-bound approvals and genuine Sandbox API reconciliation. |
| Design | One connected artist/studio workspace, source review, accessible status/action patterns, transcript playback, ledger and clear financial confirmation. |
| Potential impact | A concrete review/reconciliation workflow for artists, studios and rights operations. No invented user adoption, revenue or measured time-savings claims. |
| Innovation | Evidence continuity across contract versions, measured usage, overlap review, human authorization and payment state. |
| Presentation | Actual browser workflow, honest provider errors, concrete monetary explanation and verified separate Sandbox settlement in under three minutes. |

AG Grid and APIMatic contributions have specific evidence. Postman and Render usage are described within their actual limits. Bryntum, Channel3, AG Studio and autonomous/agentic payment operation are not implemented or claimed. Prize eligibility and sponsor judging remain the organizers' determination.

## Final owner checklist

- [ ] Review and authorize publication; confirm repository is public and cloneable while logged out.
- [ ] Confirm root MIT license is detected and application/font/dependency notices are retained.
- [ ] Recheck source/history for secrets and private data before changing visibility; a current `.gitignore` does not remove historical leaks.
- [ ] Verify fresh-checkout setup, locked installs, offline fixtures and actual frontend/API operation.
- [ ] For live judging, supply account setup guidance without sharing API keys in public text; leave financial writes deliberate.
- [ ] Test hosted URL with the published shared demo login; disclose shared access and free storage/cold-start/payment limitations. Never publish provider keys or PayPal account passwords.
- [ ] Review the completed narrated 2:59 cut and media permissions, then upload to public YouTube.
- [ ] Add the actual YouTube URL to README and submission form; verify playback logged out.
- [ ] Paste the final feature/tool description and accurate verification limits into the submission.
- [ ] Submit through the organizer's form and verify the confirmation. No submission is performed by these files.
