# Sponsor integrations: verified scope

**Latest evidence — November 12, 2026:** the owner-deployed Render preview is separate from durable local payment evidence. Recording used live Gemini/Groq, actual AG Grid filtering/detail/CSV, the sponsor guidance page and guarded Postman download. A saved Fish success was shown without a new generation request. A real status refresh verified the earlier owner-paid USD 17.46 Sandbox invoice as PAID/zero outstanding; no new invoice/send/payment was performed during filming. The new filmed royalty is USD 56.76 and has no invoice. APIMatic remains used developer guidance, not an Invoicing runtime SDK; Postman execution, AG Studio and live webhook delivery are not claimed. Earlier dated verification paragraphs below describe the original milestone. See [current submission evidence](HACKATHON_SUBMISSION.md).

## APIMatic PayPal Context Plugin

Installed with the exact requested command, from FairModel: `npx context-plugins install paypal`. System tools were detected without reinstallation: Node v26.13.0, npm/npx 11.20.0. Registry metadata identified the official `apimatic/context-plugins-installer` source. The installer reported successful Codex marketplace/plugin installation. The installed `plugin.json` independently identifies **paypal 0.4.1**, author APIMatic, MIT license.

Verified installed instructions at `C:/Users/shaha/.codex/plugins/cache/context-plugins/paypal/0.4.1/`. This session directly read the Python getting-started, authentication, integration, resilience, error-handling and testing guidance. It also retrieved the public SDK map from `context-plugins/paypal-python-sdk`, spec version 2.29. This is actual use of installed guidance, not a claim that a new tool automatically appeared in the current chat. In the current November 10 session, PayPal skills are listed in the Codex skill catalog and the installed manifest/Python guidance are directly accessible. A new installation can require a session reload, but this verified installation does not need reinstalling. No credentials are exposed to the plugin documentation.

### Verified coverage and implementation choices

The SDK map lists 40 operations across Orders, Payments, Subscriptions, Transaction Search and Vault. **It has no Invoicing v2 or webhook-verification controller.** We did not invent those endpoints, install an unnecessary SDK, or claim APIMatic executes invoice requests. FairModel retains its existing maintained HTTPX dependency for those official REST endpoints.

Guidance used meaningfully:

- Explicit Sandbox host/auth configuration and pooled synchronous client, matching FastAPI's existing synchronous service pattern.
- Backend OAuth token cache/expiry, bounded timeouts, safe credential/token error boundaries and no header/body logging.
- Resilience policy: bounded read retries and token refresh; no blind retry of financial POSTs.
- Durable local duplicate claims before remote writes, not a provider idempotency header alone. `payment_operations` records create/send intents and uncertain outcomes before a network request. Unique constraints and serialized SQLite transactions protect concurrent requests.
- Transport-level tests through HTTPX MockTransport, asserting actual paths, methods, payload aliases, money and error handling. Fixtures do not prove live API access.

Components informed: `app/paypal_client.py`, `paypal_provider.py`, `paypal_models.py`, `paypal_webhooks.py`, additive database tables and `tests/test_paypal.py`. Installing this development plugin is distinct from integrating the payment API.

Sources: [APIMatic marketplace](https://context.apimatic.io/plugins/paypal/), [plugin source](https://github.com/context-plugins/plugin-marketplace/tree/main/plugins/paypal), [SDK map](https://github.com/context-plugins/paypal-python-sdk/blob/main/sdk-map.md). Invoicing models/endpoints and signature verification instead use [official PayPal Invoicing v2](https://developer.paypal.com/api/invoicing/v2), [OAuth](https://developer.paypal.com/api/rest/authentication/) and [webhook verification](https://developer.paypal.com/api/webhooks/v1/verify-webhook-signature-post).

## AG Grid Community

The existing application already used AG Grid Community; it remains in use. The ledger now includes actual artist/studio/campaign/license filters, stored compliance assessment, invoice status/provider, received test funds and outstanding approved amounts. Numeric columns sort/filter; CSV export includes provider labels. Aggregated money is computed with Python Decimal and kept separate by currency and provider. A historical compliance column is not an invoice authorization; backend eligibility is revalidated at the action.

**AG Studio and Enterprise features are not installed or claimed.** No trial, license account or additional external resource was created.

## Postman

Prepared `postman/FairModel.postman_collection.json` with 19 local API requests: health, integration diagnostic, licenses, media/report, authorizations, royalties, invoice preview/create/get/send/refresh and analytics. It contains placeholders, no client credentials/tokens. Mutations have a pre-request skip guard (`allow_explicit_writes=false`); Sandbox financial confirmations also default false. Import and manually inspect before enabling a particular action. The collection was structurally validated locally; **it was not run in the Postman app**, and exporting it is not proof of live payment success. See [Postman's skip-request behavior](https://learning.postman.com/docs/tests-and-scripts/write-scripts/postman-sandbox-reference/pm-execution).

## Earlier installation milestone: evidence and limits

Live Sandbox OAuth and read-only invoice-list access succeeded. No Sandbox invoice creation, sending, payment or cancellation has been performed without the owner's separate approval. Webhook code is mock-tested; no public endpoint or live delivery is claimed. Exact final test counts are in PLAN.md and the development report. The previous cinematic preview is retired from application routing. One Settings & integrations page links to the actual Community ledger and the guarded Postman collection at `/api/tools/postman`. APIMatic PayPal 0.4.1 manifest/Python guidance and the cached SDK map were rechecked on November 10; actual OAuth and read-only Invoicing succeeded again. No live financial write was performed.
