# PayPal Sandbox readiness — November 12, 2026

Actual Sandbox integration supersedes the historical account-access deferral. Production endpoints remain unsupported. Historical mock records are simulations. One genuine owner-completed Sandbox payment has been refreshed and verified paid; that is not a claim of production readiness or permission for another financial operation.

## Implemented and automated with mocked provider HTTP

- [x] Backend OAuth client credentials, expiry cache and safe token/credential failures.
- [x] Fixed Sandbox host; production environment rejected; no credentials needed for mock startup.
- [x] Eligible positive royalty → typed Invoicing v2 draft with current contract/compliance/identity/use/overlap/artist charge approval checks.
- [x] Durable unique create/send operation intents committed before remote writes; actual returned IDs and uncertain-outcome reconciliation without blind POST replay.
- [x] Separate confirmed artist sending; no startup, migration, analysis or normal test sends invoices.
- [x] Authoritative refresh and separate pending/partial/paid/cancelled/refund/manual-external states, with matching amounts and actual payment evidence.
- [x] Signature verification, unique webhook receipts, replay/out-of-order protection and authoritative GET reconciliation.
- [x] Role/ownership checks, stored-provider routing, simulation only for mock records, distinct Sandbox/mock notices.
- [x] Actual-record AG Grid, guarded Postman collection and separate manual test tools.

## Actual live evidence

- [x] Owner-configured Sandbox OAuth and authenticated invoice reads succeeded without printing credentials/tokens.
- [x] Genuine USD 17.46 draft returned a real remote ID. Owner-corrected issuer binding was reconciled through GET-only repair with backup, matching evidence and original-intent audit preservation; no duplicate draft was created.
- [x] Owner completed sending/buyer payment outside the filming task. On November 12, the authorized captured refresh queried PayPal and verified the existing case as PAID, USD 17.46 paid and zero outstanding.
- [x] The film clearly separates that earlier payment from the new USD 56.76 calculation, for which no invoice was created. No new draft/send/payment/cancellation occurred during filming.
- [x] The filming preservation check confirmed 316 pre-existing rows across 22 tables and 52 pre-existing media files unchanged against the pre-filming backup; database integrity/foreign keys passed.

## Before each new local Sandbox test

- [ ] Use distinct real Sandbox business issuer and personal buyer matching the configured merchant app; no passwords/tokens in FairModel or public docs.
- [ ] Review the actual agreement, audio, campaign, speech measurement and artist attestation; resolve overlap/open cases and approve the specific eligible positive charge.
- [ ] Explicitly authorize its amount/currency/recipient before enabling draft writes and confirming creation.
- [ ] Separately authorize/confirm sending; inspect actual provider ID, status and returned payment link.
- [ ] Buyer completes test checkout on the PayPal-hosted Sandbox page, then refresh status and inspect totals/events.
- [ ] Confirm the particular case's persistence after a controlled restart before making restart guarantees. Do not reset records or retry unknown writes to make a demo pass.

## Remaining limitations and submission work

- [ ] Configure an approved reachable webhook endpoint and verify actual signature/delivery. No automatic tunnel/public receiver setup is authorized; the free hosted shared gate is unsuitable as-is.
- [ ] Verify more actual partial/pending/refund and out-of-order scenarios under separate explicit authorization; current coverage is mocked.
- [ ] Verify the final buyer journey on any new account/case instead of inferring it from old paid evidence.
- [ ] Keep Render Free draft/send disabled because operation history is ephemeral. Durable storage, production authentication, merchant onboarding and production payments require separate work.
- [ ] Publish the reviewed source/license and publicly upload/link the narrated under-three-minute demo; see [submission guide](HACKATHON_SUBMISSION.md).

Commands and safe error recovery: [Sandbox testing](PAYPAL_SANDBOX_TESTING.md). Detailed sponsor contribution: [sponsor integrations](SPONSOR_INTEGRATIONS.md). Fresh setup: [README](../README.md). Exact historical results and backups: [PLAN](../PLAN.md).
