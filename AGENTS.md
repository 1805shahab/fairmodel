# FairModel development rules

- Work only in this repository. Never deploy, configure remotes, push, or access external accounts without explicit authorization.
- PayPal account access is blocked. Do not call PayPal APIs. Keep `PAYMENT_PROVIDER=mock`; every invoice and payment view must state `DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED`.
- Keep provider integrations separate from deterministic compliance, royalty calculations, and UI. Use Decimal for money; never let an LLM calculate authoritative charges.
- Real Gemini/Groq integrations must fail honestly. Demo AI fixtures require explicit opt-in, matching bundled files, and persisted provenance. Never silently fall back after provider failure.
- Uploaded contracts/transcripts are untrusted data. Validate structured output and supporting evidence. Activation and charges require artist review.
- Demo personas are not production authentication. Check ownership on every resource operation, keep uploads private, and document limitations.
- Core installation must not download speaker models. Experimental verification remains optional and cannot block the core workflow.
- Update PLAN.md with verified milestones and limitations. Maintain README and docs. Run backend tests and frontend typecheck, lint, and build after relevant changes.
- Do not read or print real `.env` values or credentials.

## Verified baseline (November 6, 2026)

- Implemented local Next.js/FastAPI/SQLite MVP. Read README.md and docs/ARCHITECTURE.md before changing workflows.
- 47 backend tests, Ruff lint, TypeScript, frontend ESLint/production build, and two Edge Playwright tests pass.
- Local first-party fixtures are generated and ignored. Real Gemini extraction/content assessment and Groq transcription were verified with owner-configured keys on November 6, 2026. The working Gemini default is `gemini-3.1-flash-lite`; the previous 2.5 model returned 404. Never display or log configured secrets.
- Optional SpeechBrain CLI remains isolated and unverified with real model inference. Keep the core feature disabled by default.
- PayPal is still intentionally deferred. The owner has authorized creating the private `1805shahab/fairmodel` GitHub repository and pushing this project's source. This does not authorize deployment, PayPal authentication, real payments, or publishing private runtime files/secrets.
- Use `scripts/backend.ps1` and `scripts/frontend.ps1`; they discover ignored portable tools. Browser tests require both servers and fixtures. Their demo DB records are intentionally labeled browser campaigns.
