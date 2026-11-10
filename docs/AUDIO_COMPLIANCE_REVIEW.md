# Audio analysis and compliance review — November 9, 2026

Follow-up: the version-4 string mismatch, administrative-condition reasoning, missing citations and excerpt overlap were corrected in compliance policy v3. The supplied asset was rechecked with live Gemini and now correctly returns NEEDS_REVIEW / USD 0.00 with no substantiated violation. See [COMPLIANCE_RULES.md](COMPLIANCE_RULES.md) for current behavior and the actual result. The earlier restricted outcome below records the historical pre-fix audit.

## Why the page said fixture mode

The old audio page displayed “Explicit local fixture mode — not a live AI result” as a checkbox label even when unchecked. It was not evidence that Gemini had run or that the saved transcript was a fixture. One checkbox also controlled both services and inherited the saved transcript's fixture setting. Backend analysis/report caches could return an existing fixture without checking a newly requested live provider.

Live Gemini was already implemented with `google-genai` and enabled by a nonempty server-side key. `DEMO_MODE=true` enables local personas and simulated payments; it does not force AI fixtures. Both keys are configured in this workspace; no credential values were inspected or printed during this review.

The page now has independent transcription/compliance selectors that start on live services. Offline mode requires an explicit selection. Saved transcript and assessment provenance are displayed separately. Provider failures return safe actual upstream status/category, not invented success. A failed refresh retains labeled previous evidence and holds charge eligibility until a successful retry.

## Trace from browser to persistent records

| Step | Implementation and evidence |
| --- | --- |
| Upload | `frontend/app/dashboard/submissions/new/page.tsx` submits a private multipart upload through `frontend/app/api/backend/[...path]/route.ts` to `POST /api/assets`. Ownership, active license, campaign schema, actual audio format, size/duration and duplicate hash are checked. |
| Process | `frontend/components/asset-detail.tsx` calls `POST /api/assets/{id}/analyze`. `backend/app/audio.py` runs ffprobe, normalizes with FFmpeg, and estimates speech with WebRTC VAD. Total duration and speech duration are separate. |
| Transcribe | `backend/app/ai.py::transcribe` uses the actual Groq SDK for normalized audio, requesting segment timestamps. Live provenance is `groq:<model>`; fixtures have `demo_fixture (not Groq)` and an explicit boolean. Only a matching bundled file may use the fixture. |
| Review identity/use | The assigned artist explicitly records identity and usage authorization at `POST /api/assets/{id}/authorization`. `UsageAuthorization` binds that decision to the exact file, campaign, analysis and approved contract version. Metadata/transcription changes invalidate it. This is manual attestation, not biometric proof. |
| Retrieve approved terms | `backend/app/eligibility.py::approved_version` reads `LicenseVersion` from SQLite using the asset's license ID/version. Active artist approval and assigned studio are required. Evaluation does not accept replacement terms from the frontend; the report persists a hash of the actual approved snapshot. |
| Assess content | `POST /api/assets/{id}/evaluate` passes that snapshot, declared campaign metadata and the persisted transcript to `ai.content_findings`. Gemini returns Pydantic-validated findings/uncertainty; supporting transcript quotes are checked. Documents/transcripts are treated as untrusted data. |
| Determine eligibility | `backend/app/royalties.py::evaluate` independently checks medium, territory, language, dates, campaign, declared restricted category, unknown terms, special conditions, measurement uncertainty, AI findings and manual authorization. AI-only possible prohibited content requires review; explicit declared out-of-scope use is restricted. |
| Calculate | `royalties.calculate` uses measured spoken seconds, approved allowance/rate/billing basis, Decimal arithmetic and HALF_UP cent rounding. Estimates may be shown during review, but no royalty allocation is created while identity, authorization or eligibility is unresolved. |
| Approve | Eligible positive proposals remain pending artist charge approval. Approval and invoice creation recheck the current evidence-bound eligibility, including legacy records. Exact file hashes, unique asset allocations and transactions prevent duplicate charges. |
| Payments | Existing `MockPaymentProvider` only. All invoices/payments remain explicitly simulated. No PayPal API or integration changes. |

`ANALYZED` means local audio processing/transcription completed. The page separately shows compliance outcome and “Identity not automatically verified.” Core processing runs no speaker model and produces no invented similarity score. Optional experimental inference remains isolated and unverified.

## What was actually verified

- Database provenance: a saved transcript with 28 timestamp segments is live `groq:whisper-large-v3-turbo`, with `demo_fixture=false`, and originally had no compliance report. Earlier browser-test records are explicitly offline fixtures and remain labeled that way.
- The newest successfully analyzed record has nine segments from live Groq. A new actual Gemini request assessed it against approved database version 4 and saved `gemini:gemini-3.1-flash-lite`, `assessment_fixture=false`, and `RESTRICTED_USAGE`. Its term hash was recorded, charge eligibility was false, and total royalty count did not change. No artist attestation was invented.
- Separate first-party sample smoke checks actually called Groq and Gemini with fixture mode off: 70.052s total / 58.77s estimated speech, 990 transcript characters, 12 timestamp segments; Gemini extraction produced 14 verified citations. Gemini content assessment returned one finding and one uncertainty. Successful requests are not assertions of compliant content.
- Automated tests use mock provider responses or explicit matching fixtures, separately from those live calls. Tests cover provider failure/redaction, cache/provider switching, approved snapshot retrieval, identity/authorization gating, scope/uncertainty, deterministic amounts, duplicates, schema upgrade and revoked/legacy charge safety.
- Final checks: 81 backend tests, Ruff, frontend TypeScript/ESLint/production Webpack build, and two Edge browser tests pass. Browser tests used a separate ignored QA database and tested mobile audio layout. The original financial records were preserved. Verification servers were stopped.

## Test in the browser with real Gemini and Groq

1. Keep keys only in the existing `backend/.env`. The working model is `GEMINI_MODEL=gemini-3.1-flash-lite`. Keep `PAYMENT_PROVIDER=mock`, `DEMO_MODE=true`, and speaker verification disabled. No `.env` values belong in frontend variables or screenshots. Restart both servers with the commands below and open `http://127.0.0.1:3000`.
2. As Artist, create a new agreement, upload an authorized text PDF, leave fixture extraction unchecked, and extract. Verify `gemini:<model>` on the license. Review every term/citation, correct discrepancies with a review note, and approve. Unknown/ambiguous clauses must not be invented to force a passing demo.
3. As Studio, submit consented single-speaker audio under that agreement. Supply medium, region, language, campaign/category and an intended-use date inside the actual approved scope. Choose **Live Groq Whisper**, then **Analyze audio**. Check `groq:<model>`, timestamp segments, real playback and distinct VAD speech/total durations.
4. Keep **Compliance provider → Live Gemini** and click **Evaluate compliance**. Check the prominent live assessment label and both saved sources. Initial unresolved identity/authorization must hold charges even when content is otherwise allowed. Restricted declarations or uncertain Gemini findings also hold charges.
5. As Artist, listen and review the contract, transcript, campaign and authorization evidence. Record identity/usage confirmations only if supportable, with a substantive note. Do not claim identity from synthetic fixture audio. Save, then reevaluate using **Live Gemini**. Manual authorization does not override out-of-scope clauses or uncertainty. Resolve actual metadata/contract problems and repeat review; genuinely unresolved content remains held for human/legal review. There is no “ignore uncertainty and bill anyway” action.
6. For eligible permitted usage, inspect the deterministic formula and any pending royalty. Example: 45 measured spoken seconds, 30 included, USD 2/s → USD 30. Separately approve the charge, then create a simulated invoice. Every payment screen must show `DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED`.
7. Reopen an older fixture asset: the saved result must still say offline, while the new compliance selector defaults to live. A failed real request displays an error, retains historical provenance, and never becomes fixture success. Retranscription is locked once financial evidence has been allocated; use a new agreement/asset for an independent live run.

Run from the repository root in separate PowerShell terminals:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend.ps1
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend.ps1
```

Optional direct live service smoke check (real quota usage, safe aggregate output, no royalties/payments):

```powershell
Set-Location backend
.\.venv\Scripts\python.exe ..\scripts\verify_live_ai.py
```

For offline development choose the matching bundled fixtures deliberately for each stage. The fixture-only artist review is a simulated exercise; it is not consent for real use. See `DEMO_GUIDE.md`. Neither live nor offline mode implements production authentication or actual PayPal settlement.
