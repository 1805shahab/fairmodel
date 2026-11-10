# PayPal Sandbox testing

Only `https://api-m.sandbox.paypal.com` is used. Production is rejected. Mock and Sandbox remain separate, with no failure fallback. **PAYPAL SANDBOX — TEST TRANSACTION — NO REAL MONEY** labels every Sandbox invoice. Mock records retain **DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED**. Demo personas are selectable local identities, not production authentication or arbitrary-artist merchant onboarding.

## Verified versus pending

- **Live verified:** backend OAuth client credentials; authenticated read-only Invoicing v2 invoice-list capability. No credential/token output.
- **Implemented and mock-tested:** draft payload/create, durable duplicate claims, uncertain-create search reconciliation, separate send, actual-ID retrieval, refresh, partial/pending/full/refunded states, merchant/recipient/amount checks and verified/idempotent webhooks.
- **Live not yet performed:** draft creation, sending, buyer payment, full settlement or webhook delivery. Each needs the owner's relevant explicit authorization; account emails and supported artist review are still required. Read access does not prove write permission.

## Configure test accounts without exposing secrets

Keep existing Client ID/Secret in `backend/.env`. The agent never overwrites this file. Use a PayPal **Sandbox business** merchant and a different **Sandbox personal** buyer from the developer dashboard. The app issues invoices as the single configured merchant; it does not onboard artists. Choose existing test accounts, or create accounts yourself after reviewing that external action. Do not put buyer passwords in FairModel.

Add these non-secret settings yourself, substituting the actual test-account emails:

```dotenv
PAYPAL_ENVIRONMENT=sandbox
PAYPAL_SANDBOX_MERCHANT_EMAIL=YOUR_SANDBOX_BUSINESS_EMAIL
PAYPAL_SANDBOX_BUYER_EMAIL=YOUR_SANDBOX_PERSONAL_EMAIL
PAYPAL_WEBHOOK_ID=
```

Keep default `PAYMENT_PROVIDER=mock` if using offline fixtures. When deliberately testing Sandbox, the launch flags below override settings only in that PowerShell child process. They do not edit `.env`. `PAYPAL_ALLOW_DRAFTS`/`PAYPAL_ALLOW_SENDING` default false; merely adding credentials creates nothing.

## Start and diagnose, no invoice writes

From this workspace, terminal 1:

```powershell
Set-Location 'C:\Users\shaha\OneDrive\Desktop\Work\fairmodel'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1 -PayPalSandbox
```

Terminal 2:

```powershell
Set-Location 'C:\Users\shaha\OneDrive\Desktop\Work\fairmodel'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1
```

Stop an old server with Ctrl+C before reusing its port. Open http://127.0.0.1:3000/dashboard/settings. Artist view → **Test Sandbox connection (read-only)**. The result separately reports configured credentials, actual OAuth success/failure, read-only invoicing capability and webhook configuration. Alternatively:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe ..\scripts\paypal_diagnostic.py
.\.venv\Scripts\python.exe ..\scripts\paypal_diagnostic.py --capability
Set-Location ..
```

The first command is OAuth-only; the second additionally reads invoice listing. Neither writes invoices or transfers money. There is no automatic diagnostic/account API call on application startup.

## Prepare a distinct case and human review

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\prepare-sandbox-demo.ps1
Set-Location backend
.\.venv\Scripts\python.exe ..\scripts\measure_sandbox_demo.py --live-ai
Set-Location ..
```

This creates an original, fictional Harbor Lantern advertisement using an installed Windows stock computer voice. It does not imitate a real artist. Files stay ignored under `backend/fixtures/paypal-sandbox-demo/`. Actual measurement here: **81.710s recording / 70.23s VAD speech**. Live Groq returned 14 segments; live Gemini sample-contract extraction returned 15 verified citations and content assessment had no findings/uncertainties. The sample's 30s allowance and USD 2/extra second conditionally calculate **USD 80.46**. These are measured values, not an attempt to force USD 30. No contract, identity attestation, allocation or invoice was created by this preparation script. Stock-voice measurements can differ on another machine.

Use `/dashboard`, not the fictional `/control-room`. Artist creates/reviews the first-party sample agreement and approves its actual terms/citations. Studio uploads the new recording with the assigned campaign, authorized date, US, English, online advertising and consumer-products metadata; choose **Live Groq** and **Live Gemini**. Inspect actual measurements/provenance. Artist manually reviews the synthetic demonstration's identity and campaign authorization with a truthful note; manual attestation is not biometric proof. Resolve any detected overlap based on evidence. Reevaluate workflow checks, then approve the positive royalty separately. Unresolved identity, restricted scope, missing evidence, stale approval or unresolved overlap must remain held.

Never reuse an already mock-invoiced royalty for a Sandbox invoice. Its existing record is preserved; use a new eligible case. The adapter initially supports **USD** financial charges only.

## Explicitly authorized draft creation

First review the exact case, amount, currency, merchant and buyer using **Create / open PayPal Sandbox draft**'s preview or `GET /api/royalties/{id}/invoice-preview`. Obtain owner authorization for that case. Only then restart the backend:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1 -PayPalSandbox -EnableSandboxDrafts
```

Artist → Royalties → **Create / open PayPal Sandbox draft** → read the concrete confirmation → accept only if correct. A real `INV2-...` must come from a successful API response. Creation does **not** send the invoice. Merchant data is populated from PayPal's authenticated merchant, then verified against configuration. Stored amounts remain unchanged. Repeated clicks reuse one local/remote invoice.

A manually invoked equivalent test exists; no write occurs without explicit case arguments:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\live_paypal_test.py --draft REVIEWED_ROYALTY_ID --approve-amount REVIEWED_AMOUNT --approve-recipient REVIEWED_SANDBOX_BUYER_EMAIL --i-authorize-this-sandbox-action
```

## Separate explicit send authorization

Review the actual draft ID, amount and recipient. Obtain authorization to notify that specific Sandbox buyer, then enable sending:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1 -PayPalSandbox -EnableSandboxDrafts -EnableSandboxSending
```

Artist → Invoices → **Send Sandbox invoice** → confirm. The app requests the official send operation, then fetches actual invoice state. A send acceptance is not payment. No tests, migrations or startup tasks send invoices. The manual CLI equivalent requires `--send LOCAL_INVOICE_ID` and the same reviewed amount/recipient/authorization arguments.

## Buyer payment: manual, Sandbox only

1. Switch to Studio, find the actual Sandbox invoice and inspect issuer, amount, status and history.
2. Click **Open PayPal Sandbox invoice** only when its real returned link is displayed. The app never synthesizes checkout URLs. If no link is supplied, refresh; otherwise inspect that actual invoice in the merchant's Sandbox account.
3. In the PayPal-hosted Sandbox page, sign in manually using the separate Sandbox personal buyer. Do not use production credentials or paste its password into FairModel/chat. Review the invoice and explicitly complete the test payment yourself.
4. Return to FairModel → **Refresh PayPal status**. Pending and partial payments stay distinct. Fully paid requires the latest API's `PAID`, matching total/paid/due amounts and actual PayPal payment rows. External/manual marks and an event named `INVOICING.INVOICE.PAID` alone do not prove PayPal settlement.
5. Restart the backend and verify the same invoice, amounts, provider status, last synchronization and event history remain. Refund/cancel history is preserved; the app does not initiate those operations.

## Webhooks: optional for local demonstration

Direct status refresh works without a webhook/public URL. No tunnel, deployment or public endpoint was created. If you later authorize a reachable test listener, register that endpoint in the Sandbox app yourself and set `PAYPAL_WEBHOOK_ID`. The backend handler is `POST /api/paypal/webhook`. It sends the official signature-verification request to PayPal Sandbox, rejects failures/missing headers, preserves event IDs, deduplicates replays and fetches authoritative invoice state. Out-of-order event labels cannot override a newer successful snapshot. A failed reconciliation is retained for retry, not marked paid.

## Errors and uncertain writes

Missing credentials, OAuth 401, permission 403, validation 422, rate limits and network failures produce safe categories without provider bodies/secrets. Status-refresh failures preserve last successful evidence and show the error separately. Financial amounts are never rewritten. Draft/send operations have durable unique local claims saved before HTTP. The current official create/send definitions do not advertise `PayPal-Request-Id`; the implementation does not rely on that header. A timed-out create searches by the frozen invoice number/reference or fetches the stored real ID; an unresolved outcome stays held instead of creating another invoice. A timed-out send refreshes state before any further action and does not blindly resend. A simultaneous request can observe a write still in flight and return a safe 409; wait for the first request, then retry to retrieve/reconcile the same invoice. Persistent reconciliation holds may require owner/provider investigation; no automatic cancellation or replacement is performed.

## Tests and sponsor artifacts

Normal Pytest tests blank payment credentials and mock the HTTP transport. Browser Sandbox UI tests mock backend responses; they do not create actual PayPal invoices. `scripts/qa_backend.py` also blanks all PayPal credentials/write flags. `scripts/seed_demo.py` refuses to run against a Sandbox-selected server. See TESTING.md for isolated runs.

APIMatic usage/coverage: [SPONSOR_INTEGRATIONS.md](SPONSOR_INTEGRATIONS.md). AG Grid Community adds practical record filters and provider-separated received/outstanding amounts; AG Studio is not used. Import `postman/FairModel.postman_collection.json`, keep `allow_explicit_writes=false`, populate local record IDs and inspect requests individually. Mutating examples require intentional opt-in; Sandbox confirmations still default false. No secrets/tokens belong in the collection. Actual Postman execution and live webhook delivery remain unverified.
