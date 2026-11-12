# Voice Usage Passport and review tools

These tools extend the existing workspace without new dependencies or a second preview application. They are workflow evidence, not legal certificates or biometric verification.

## Passport

Choose **Voice usage passport** on a recording or **Passport** in Audio submissions. `/dashboard/submissions/{asset_id}/passport` calls private `GET /api/assets/{asset_id}/passport`. The stable identifier is `VP-` plus the immutable asset ID; it is not a signature or public identity credential.

The projection joins the saved asset, exact approved `LicenseVersion`, analysis, current compliance, manual attestation, royalties, append-only charge approvals, provider-specific invoice/payment events, related usage and audit. It exposes no filesystem paths or credentials. Reading it creates no record and makes no provider call. Audio, compliance, attestation, charge, invoice and payment stages are independent. Partial/pending payments do not complete payment; simulated completion stays explicitly simulated.

Print / save PDF uses the browser, includes a snapshot timestamp and all current compliance conditions, and removes navigation/interactive controls. Private exports remain the user's responsibility to store/share safely. There is no public share endpoint or token.

## Schema 5 and history

The additive migration creates only `evidence_revisions`, `usage_cases` and `usage_case_events`, after a consistent SQLite backup. Original backup: `backend/backups/fairmodel-pre-v5-20261110T204021406377Z.db`. All 17 original tables compared unchanged after migration; integrity/foreign keys pass. All 18 original contract/audio/reference files remain present and match saved hashes.

Hash-deduplicated, append-only revisions preserve analysis, compliance and authorization before future replacement/removal, including failed reassessments and metadata correction. Migration captures then-current records as `migration_current_only`. Earlier overwritten decisions cannot be reconstructed and are not invented. Existing financial/overlap approval history remains intact. Back up the database and uploads together. `.env` is never exported or committed.

## Interactive evidence

The explorer appears in passports and the existing Compliance tab. Named buttons support keyboard Tab/Enter/Space. Select a condition to inspect its outcome, deterministic/manual/advisory source, actual PDF quotation/page, declared campaign metadata and next action. Missing/invalid citations are omitted and explained.

A seek button appears only if exactly one supplied timestamp segment contains the passage and falls inside the recording. It seeks the containing segment's start, never an invented word timestamp. Offline fixtures have no timestamps. The browser regression injects explicitly synthetic timestamps only into an intercepted response; persisted records are unchanged.

## Artist/studio Review Center

`/dashboard/reviews?asset={asset_id}` lets artists record approve-usage review, request-changes, reject-usage or investigate decisions. A category and explanatory note are mandatory; optional references must belong to the actual asset/approved contract. Usage review does not replace identity attestation or charge approval. Studios may respond and correct supported metadata on the existing recording page; they cannot grant artist approvals or resolve cases.

Non-approval cases remain OPEN until artist resolution. Concerns are not findings of infringement. Responses/resolutions are append-only; request keys make retries idempotent and reject conflicting reuse. Resolution binds current file/transcript/metadata/license evidence. Changed evidence makes a resolved review stale; replaying an old request does not renew it.

Open/stale cases block financial approval/create/send, including linked canonical usage. Resolution changes the compliance input hash and requires reevaluation/current charge approval. Existing charges/invoices remain unchanged and may require reconciliation. No case action sends/cancels/refunds a PayPal invoice. Other compliance/overlap holds remain. Controls are inert while changing demo roles, preventing input during the transition.

## Studio simulator

`/dashboard/simulator` uses an assigned active approved agreement, actual scope choices (wildcards permit intended declarations), date/category and 0–600 estimated speech seconds. The slider and numeric field call `POST /api/licenses/{id}/estimate`, using the existing pure Decimal engine and deterministic scope projection. No AI/PayPal call, asset, allocation, approval, audit event or invoice is created.

Output is `SCOPE_APPEARS_PERMITTED`, `NEEDS_REVIEW` or `RESTRICTED_USAGE`, never actual approval. Missing rates/financial provenance or ambiguous billing require review; prohibited scope has no payable estimate. It invents no transcript, administrative receipt or artist attestation. Cumulative previews use persisted prior allocations and may change before submission.

At 30 included seconds and USD 2/second: 20s/30s → USD 0.00; 45s → USD 30.00; 58.77s → USD 57.54. Only final money is rounded HALF_UP to cents. The visible notice states that actual charges depend on submitted usage, approved terms, compliance and artist approval.

## Provenance, audit and limits

Audio submissions filter all records, successful live transcription+compliance receipts, records containing fixtures, or pending/unverified receipts. Configured model names alone are not labeled live. No fixture is deleted/relabelled. Existing ledger filters and separate currency/provider totals remain unchanged.

Passports show chronological license/submission/analysis/compliance/authorization/overlap/financial events, new review threads, royalty-calculation and direct Sandbox-status synchronization events with actor/time. No audit history is erased.

Fresh live Sandbox OAuth and authenticated read-only Invoicing diagnostics succeeded. Original records contained zero Sandbox invoices/operations. Actual draft/send/buyer payment and live webhook delivery remain unverified and need separate case-specific approval; webhooks are unconfigured. Automated PayPal checks mock HTTP. QA uses an isolated database, actual local PDF/media/VAD, explicitly selected AI fixtures and blank credentials. No financial write, production endpoint, tunnel, deployment or push was performed. Existing Gemini/Groq adapters were preserved; no fresh live AI request was needed for these record projections.

Demo identities remain selectable local roles, not production authentication. Keep servers loopback-only. No speaker model, acoustic fingerprinting, OCR, production login, durable job queue or automatic financial reconciliation is added. The Taste checker previously returned ERROR and was not rerun or claimed as passing; screenshots and browser regressions are separate evidence. See PLAN.md for final test counts.

## Final reliability and verification

All **190 backend tests**, Ruff and **23 final Edge checks (3.1m)** pass, along with TypeScript/ESLint/production Webpack build. The original full real-media/local-fixture/artist-review/simulated-settlement/overlap workflows still pass. The one pre-existing Starlette TestClient deprecation warning remains. Early failures included a duplicate type/effect-state lint issue, role-transition draft loss, unscoped duplicate report text and an analytics assertion before asynchronous data arrived; all were corrected before the final run.

Concurrent browser reads exposed an existing lock/session-lifetime issue. Ordinary GET/HEAD and estimate previews now use read transactions. Financial writes, including invoice-status synchronization, retain serialized `BEGIN IMMEDIATE`. Database dependencies close before sending/streaming responses, using [FastAPI's documented function scope](https://fastapi.tiangolo.com/advanced/advanced-dependencies/#dependencies-with-yield-and-scope); FastAPI's minimum is now 0.121, already supported by the installed environment. Real-runtime regressions verify two concurrent reads and a writer committing while a response streams. No DB reset or timeout increase was used. Final browser validation used a fresh QA frontend process, avoiding old cached server modules.

Final responsive inspection covers passports, reviews, submissions and the simulator at 1440/1024/768/390px: 16 checks, zero document overflow or browser errors. Local screenshots and the report are retained under ignored `.tmp/passport-ui/`. Temporary QA servers on ports 3001/8002 were stopped and the owner's normal servers retained. `git diff --check` passes. Changes remain local and uncommitted; nothing was pushed or deployed.

Implementation entry points: `backend/app/passports.py`, existing database/migration/API/eligibility modules, `frontend/components/usage-passport.tsx`, `evidence-explorer.tsx`, `review-center.tsx` and `royalty-estimator.tsx`. Schema 5 adds only `evidence_revisions`, `usage_cases` and `usage_case_events`. New backend passport/concurrency regressions and `frontend/tests/passport.spec.ts` cover these workflows; existing regression suites remain passing.

To run, open two PowerShell terminals at the repository root and start `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1` and `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1`, respectively. Stop any existing instance in its terminal before restarting. Open `http://127.0.0.1:3000/dashboard`; use a recording's Passport action, Review Center, or the Studio simulator. The backend's `-MockPayments` switch selects explicitly simulated offline payments. Default Sandbox startup performs no financial write. Full test commands are in [TESTING.md](TESTING.md).
