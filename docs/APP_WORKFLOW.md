# FairModel: one application

Open **http://127.0.0.1:3000**, then **Open workspace** (or go directly to `/dashboard`). The public introduction describes the supported workflow and leads into the same application. Old `/control-room` bookmarks redirect to `/dashboard`. There is one database and one licensing-to-invoice workflow; the fictional preview is no longer routed. Artist and studio are roles within that application, not different apps.

## Start with actual PayPal Sandbox

Stop your current backend terminal with Ctrl+C, then start from the project root in two separate PowerShell terminals:

```powershell
Set-Location 'C:\Users\shaha\OneDrive\Desktop\Work\fairmodel'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1
```

```powershell
Set-Location 'C:\Users\shaha\OneDrive\Desktop\Work\fairmodel'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1
```

The backend launcher selects `paypal_sandbox` for its process and loads the existing backend credentials normally. It does not overwrite `.env`. The old `-PayPalSandbox` switch still works. `-MockPayments` deliberately selects offline simulation for development; it is not another UI. Direct Uvicorn launch continues to use your environment configuration.

Open **Settings & integrations** and inspect the selected provider. Use **Test Sandbox connection (read-only)** to obtain actual OAuth/Invoicing capability status. The November 10 diagnostic succeeded with network access. Configured credentials alone are not proof of a successful request.

## Working workflow

1. Artist uploads a contract PDF, chooses live Gemini extraction, reviews exact terms/source clauses and approves the agreement.
2. Studio submits authorized audio and campaign metadata under that approved agreement. Live Groq transcription and real local speech measurement remain the default processing path.
3. Evaluate using live Gemini. Deterministic contract rules determine eligibility and royalties. Failed live services return errors; no fixture fallback is used.
4. Artist reviews the actual file/transcript/campaign, records identity/use attestation with a note and resolves overlap when applicable. Update workflow checks, then approve an eligible positive royalty separately.
5. Artist creates a genuine Sandbox draft, sends it in a separate explicit action; studio opens the API-returned PayPal-hosted invoice, pays manually with the Sandbox buyer and refreshes status.

The final step is implemented but has **not** been live-verified end to end. Live OAuth/read access is verified; automated draft/send/partial/paid/webhook tests use mocked HTTP responses. Do not call those mock tests evidence of an actual paid invoice.

## Financial authorization still applies

Normal startup leaves Sandbox draft/send writes off. Startup, migrations, redirects and tests never create or send an invoice. Review the exact eligible royalty, amount, currency, merchant and buyer before authorizing a test. After that specific approval, `-EnableSandboxDrafts` enables the existing confirmed draft action; a separately approved send uses `-EnableSandboxSending`. Neither flag performs an action at startup. Keep using the exact-case confirmations in the application. Details: [PAYPAL_SANDBOX_TESTING.md](PAYPAL_SANDBOX_TESTING.md).

Zero royalties, restricted usage, stale evidence, unresolved overlap or missing artist approval cannot be invoiced. Historical simulated invoices remain simulated; they are not converted into PayPal invoices.

## Sponsor tools in the same app

- **APIMatic PayPal Context Plugin 0.4.1:** installed developer instructions used in the integration. It assists development; it is not an end-user payment service. The checked SDK map lacks Invoicing v2/webhook verification, so those operations use official REST through HTTPX.
- **AG Grid Community:** actual royalty ledger at Analytics, with filtering, sorting and CSV export. No AG Studio/Enterprise claim.
- **Postman:** download the actual guarded collection in Settings or at `/api/tools/postman`, then import it into Postman. Placeholders contain no secrets. Write requests are skipped by default. It has been structurally checked and downloaded through the app, not executed in Postman.

Local role selection remains demonstration access, not production sign-in. Offline fixtures are explicitly selected development tools under Settings. Speaker-model verification remains optional; manual artist review is not biometric proof. These limitations are kept visible without presenting separate applications.

## Verification for this consolidation

173 backend tests/Ruff, TypeScript, ESLint, production build and nine Playwright checks pass. Both entry points, no automatic payment writes, guarded Postman downloads and the full local workflow were tested. Desktop/mobile screenshots at 1440/390px show no page overflow or browser errors. OAuth and authenticated invoice-list access were live-verified; financial write/settlement tests remain mocked. All 32 backend application/test source files match the pre-change hashes. No database migration, private record modification, credential edit or new dependency was required. Source was preserved under `.tmp/unify-before-20261110T213952`; QA screenshots are under `.tmp/unified-ui/`. The isolated QA servers were stopped; user servers were not stopped.
