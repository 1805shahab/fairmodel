# PayPal Sandbox readiness

The owner's Sandbox implementation authorization supersedes the earlier account-blocked plan. Production APIs remain forbidden. Historical mock records remain simulated. **Actual Sandbox invoice/payment end-to-end verification is outstanding.**

## Implemented and mock-tested

- [x] OAuth client credentials, secret-safe errors, expiry cache, credential rotation and unauthorized-token refresh.
- [x] Fixed Sandbox host; production environment rejected; credentials not required for mock startup.
- [x] Positive approved royalty → typed Invoicing v2 draft. Current compliance, identity/use, overlap and evidence-bound artist charge approval are required.
- [x] Additive schema 4: consistent backup, unique durable create/send intents, actual provider ID mapping, authoritative snapshots and webhook receipts.
- [x] Separate artist send; no draft/send at startup, migration, analysis or automated test.
- [x] Read/refresh, actual returned trusted payment URL, distinct pending/partial/paid/cancelled/refund/manual-external states.
- [x] Unknown write outcomes held for reconciliation without blind POST replay; concurrent confirmed creates allocate once.
- [x] Signature verification, unique event IDs, replay/out-of-order reconciliation against authoritative GET.
- [x] Artist/studio ownership, stored-provider routing, mock-only simulation, provider-specific labels and UI confirmations.
- [x] AG Grid Community filters/export, guarded placeholder Postman collection and manual testing scripts.

## Verified live

- [x] Owner-configured credentials loaded through runtime settings without displaying them.
- [x] Sandbox OAuth succeeded.
- [x] Invoicing v2 read-only list succeeded (`VERIFIED_READ_ONLY`). This does not prove create/send permission or payload acceptance.
- [x] New first-party stock-TTS recording measured locally; actual Groq and Gemini smoke calls succeeded. No agreement activation, artist attestation, royalty or invoice was created by preparation.

## Owner actions and remaining verification

- [ ] Configure distinct Sandbox business merchant and personal buyer emails. No passwords or tokens in chat/app.
- [ ] Review actual demo agreement/audio and attest truthfully to identity/use; resolve overlap and approve the actual eligible charge.
- [ ] Review concrete amount/recipient/payload and authorize one actual draft; enable draft writes for that process and inspect returned ID/details.
- [ ] Separately authorize sending that invoice; enable sending, confirm and inspect actual status/payment URL.
- [ ] Manually complete buyer test payment on the actual PayPal-hosted Sandbox page.
- [ ] Refresh and verify actual payment totals/PayPal evidence; check persistence after restart for this actual case.
- [ ] Optional: authorize/configure reachable webhook listener and `PAYPAL_WEBHOOK_ID`; verify real signature/delivery. No tunnel or public endpoint is configured.
- [ ] Record actual successful sequence and update submission claims. Do not claim completion until it happens.

Commands: [PAYPAL_SANDBOX_TESTING.md](PAYPAL_SANDBOX_TESTING.md). Sponsor evidence: [SPONSOR_INTEGRATIONS.md](SPONSOR_INTEGRATIONS.md). Owner-provided deadline: November 12, 2026, 12:00 PM PST (November 13, 1:00 AM Pakistan time); confirm the portal's final cutoff directly.
