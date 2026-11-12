# Three-minute FairModel demonstration

**Current recorded demo — November 12:** use the 2:59 edit and timed voiceover in ignored `output/video/`. Live Gemini extracted 19 citations; live Groq plus local audio tools measured 69.613 total / 58.38 speech seconds. Fictional-demo manual review and deterministic rules produced USD 56.76; no invoice exists for that new case. The ending refreshes a separate earlier owner-paid USD 17.46 Sandbox invoice as PAID/zero outstanding. Fish footage is a saved success, not a new request. No new send/payment or private voice transfer occurred in filming. Add narration, review permissions and upload publicly to YouTube; no public video URL has been supplied. See [submission checklist](HACKATHON_SUBMISSION.md). Older preparation examples below remain reproducible but are not the latest video script.

Current routing update (November 10): FairModel is one application. `/` introduces the product and opens the same `/dashboard`; `/control-room` redirects there; the former fictional preview is retired. Artist/studio roles share the working UI. Standard backend startup selects actual PayPal Sandbox, with default-off draft/send writes; local simulation requires `-MockPayments`. Historical preview descriptions below document earlier milestones, not a second available app. See docs/APP_WORKFLOW.md.

## Actual Sandbox variant

The repeatable offline scenarios below remain mock-only; `seed_demo.py` refuses Sandbox selection in its runtime. To demonstrate a new PayPal case, follow [PAYPAL_SANDBOX_TESTING.md](PAYPAL_SANDBOX_TESTING.md) with case-specific review/authorization. The existing owner's paid case can be shown as historical settlement evidence, separately from a new calculation. Do not describe offline cases as PayPal transactions.

For the new original recording, `prepare-sandbox-demo.ps1` and `measure_sandbox_demo.py --live-ai` passed real local processing, Groq transcription and Gemini extraction/content smoke checks. Actual speech is 70.23s here; the sample rule conditionally estimates USD 80.46. Owner-reviewed database agreement/authorization/approval are still required. No invoice was created.

## Preparation

### Repeatable judging scenarios

From the repository root, with existing base fixtures:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-scenarios.ps1
$env:PAYMENT_PROVIDER = 'mock'
Set-Location backend
.\.venv\Scripts\python.exe ..\scripts\seed_demo.py
Set-Location ..
```

If base fixtures are missing, first run `scripts/create-demo.ps1`. The scenario helper preserves existing recordings and validates their hashes. The seed uses only a dedicated fictional fixture agreement, real PDF/audio processing, explicit offline AI flags and scripted fixture-only artist attestations. It never claims actual identity confirmation. It is repeatable without duplicating the license, assets, allocations, invoice or payment events and never resets the database. Modified seed records are held for manual review instead of overwritten.

| Scenario | Expected result | Current verified local result |
| --- | --- | --- |
| A: included usage | COMPLIANT; no payable invoice | 14.88s speech; USD 0.00 |
| B: additional usage | ADDITIONAL_ROYALTY_DUE; artist-approved simulated draft | 58.77s speech; USD 57.54 |
| C: declared fictional political advertising | RESTRICTED_USAGE; no invoice | 12.57s speech; no charge/invoice |

The command prints persistent asset/license/invoice IDs. Find the `Judging scenario A/B/C — explicit offline fixture` campaigns in Audio submissions. Open B's simulated draft under Invoices & payments; deliberately simulate send/payment when narrating those steps. Rerunning the seed preserves a previously sent/paid simulated invoice. Stock-voice durations may differ on another machine; use actual VAD values and the displayed deterministic formula.

### Resolve an overlapping recording

Open the shortened submission, including the supplied version-4 excerpt. In **Related recordings & overlap review**, listen to both files, compare their campaigns/versions/durations and inspect the actual shared passages. Switch to Artist, confirm identity/use only when justified, select **Same licensed usage**, **Separate independently licensed usage**, or **Uncertain**, and write a meaningful note. Saving a decision updates workflow checks automatically when a current content assessment is available; its original provider provenance is preserved. Otherwise explicitly evaluate compliance first. Stale/failed assessments are never replaced with a fake success.

Same usage points to its canonical recording and never allocates another royalty for the edit. Separate usage respects per-asset/cumulative rules. Uncertain usage stays held. Existing conflicting charges/invoices remain visible for reconciliation. Decision history, reviewer, timestamp, version and evidence binding survive reloads. The original recording's unrelated valid charge is not revoked merely because a new excerpt is uncertain. An older recording links to incoming edited submissions for review.

Complete recording script: [DEMO_SCRIPT.md](DEMO_SCRIPT.md). Safe isolated browser tests and optional real AI checks: [TESTING.md](TESTING.md).

For the offline fixture exercise, start the backend with `scripts/backend.ps1 -MockPayments` and the frontend with README's normal command. Generate local fixtures with `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/create-demo.ps1` if missing. Use localhost:3000 and the **Settings & integrations > Offline testing tools** screen to download the sample PDF/audio. Use this exact generated pair; arbitrary files cannot use fixture results. The sample PDF names fictional parties; audio is Windows stock synthetic narration, not an artist voice clone.

For a live AI judging run, configure Gemini and Groq on the backend before starting. Leave contract fixture extraction unchecked and keep the audio page's **Live Groq Whisper** / **Live Gemini** selections. A live demo is not verified until both providers actually complete requests. Keep a separate clearly disclosed fixture run available for quota/network problems. Never claim a fixture result is Gemini/Groq. See [the detailed live workflow and pipeline audit](AUDIO_COMPLIANCE_REVIEW.md).

## One working workspace

Open `/` and choose Open workspace, or use `/dashboard` directly. Old `/control-room` bookmarks redirect to `/dashboard`. Use Workspace role for artist/studio actions. There is no fictional control-room branch. Settings & integrations contains PayPal readiness, AG Grid analytics access and the guarded Postman download. For the actual Sandbox invoice journey, follow APP_WORKFLOW.md and PAYPAL_SANDBOX_TESTING.md; for the offline fixture exercise below, explicitly use `scripts/backend.ps1 -MockPayments`.

## 0:00–0:20 — Why FairModel

Show the artist overview: explain how licensed voice usage becomes source-backed compliance evidence and artist-approved royalties. Artist and studio roles share the same app and records. Explain that local role selection is demonstration identity, not production login.

## 0:20–1:00 — Set the terms

Artist view → **New voice license** → name the agreement → select sample PDF → Upload & continue. In this credential-free demo, explicitly check **Use local demo fixture — not a Gemini result** and extract. Show page-linked exact source quotes and editable structured terms. For live AI, use the real provider instead and explain its persisted model identifier.

Point to 30 included voiced seconds per asset, USD 2 per extra second, US / online advertising / English, and prohibited political advertising. Add a review note and **Approve & activate**. Explain that AI cannot activate contracts or invent unknown terms; unknowns and unresolved clauses require review.

## 1:00–1:45 — Measure and explain the usage

Switch to Studio → Audio submissions → Submit audio. Select the newly approved license. Campaign: Northstar launch; region **US**; medium **online advertising**; language **English**; category **consumer products**; intended date within January 1, 2026–December 31, 2027. Select the sample narration.

Upload, explicitly choose **Offline development fixture** for **Transcription provider**, then **Analyze audio**. Separately choose **Offline development fixture** for **Compliance provider**, then **Evaluate compliance**. Provider selectors default back to live whenever the page reloads. Play the recording. Show actual FFmpeg/ffprobe metadata, distinct total/speech duration, WebRTC VAD segments, and transcript provenance. The bundled transcript has no timestamps; the live Groq adapter requests segment timestamps. No artificial word timings or speaker confidence scores are generated. The initial compliance report requires artist identity/usage review and proposes no charge.

Show the exact formula: `max(0, measured speech − 30 seconds) × USD 2`. The payable amount depends on locally generated narration and actual VAD measurement, so do not promise an invented fixed demo amount. For the deterministic 45-second unit-test scenario, the verified result is **USD 30**.

## 1:45–2:25 — Approve and simulate settlement

Switch to Artist on the audio page. Under **Artist identity & usage review**, record both confirmations with a note explicitly identifying this as a simulated review of synthetic fixture audio. It does not prove the fictional artist's identity. Save, explicitly select offline compliance again, and reevaluate. If all other rules pass, open Royalties, enter a separate charge review note, and approve the positive charge. Create a **simulated invoice**. Open Invoices & payments and use the on-screen three-step guide to explain the Artist → Studio handoff. Point to:

**DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED**

Simulate sending. Switch to Studio and deliberately simulate payment completion. Show the obviously simulated ID and CREATED → SENT → PAID_SIMULATED event history. Use **See PayPal Sandbox status** to distinguish this mock case from the actual Sandbox adapter. Explain: “This fixture case sent no PayPal invoice, email or funds. OAuth/read-only capability has been verified separately; actual Sandbox draft/send/payment still requires owner authorization.”

## 2:25–3:00 — Accountability and honest status

Show Analytics: real persisted royalty entries in Community AG Grid with sorting/filtering/CSV export and separate currency totals. Show Audit trail. Explain that possible prohibited content or missing restricted-region metadata is held for human review and produces no automatic invoice. Exact duplicate uploads reuse the asset/charge.

Close with: “Real PayPal Sandbox OAuth, Invoicing v2, and verified webhooks remain required for the final hackathon submission. Actual draft/send/buyer-payment verification still requires the owner's configured test emails, reviewed case and separate authorizations. This development build demonstrates the licensing, media, compliance, royalty, and explicitly simulated invoice workflow.”

## Recovery and additional scenarios

- Missing region: leave region empty with sample contract → NEEDS_REVIEW → no royalty. In asset detail, correct metadata → fresh artist identity/usage review → reevaluate. Metadata is immutable after a royalty allocation exists.
- Declared political advertising: category `political advertising` → RESTRICTED_USAGE → no royalty or invoice. AI-only possible category conflicts yield NEEDS_REVIEW rather than a definitive legal conclusion.
- Duplicate file: upload identical file under the same license → existing asset ID, unchanged metadata and no new charge.
- Missing AI key: choose live → useful 503, preserved input, no fabricated result. Provider 404/429 errors display safe status/category. Check integration status, configure the backend, and retry, or explicitly choose the sample fixture. A previously saved fixture remains labeled offline; it is not returned as the failed live request's result.
- Invalid media: renaming a non-audio file to `.wav` does not pass ffprobe validation.
- Speaker experiment: disabled by default. Do not claim voice identity or a running ECAPA model. The optional worker has not been validated with model inference.
- Administrative contract conditions use upload/review receipts and the later artist decision, never spoken declarations. Supporting clauses are verified against PDF text; empty/unverified quotations are omitted. See [COMPLIANCE_RULES.md](COMPLIANCE_RULES.md) for canonical medium mappings and the supplied version-4 result.
- Overlapping excerpts: substantial shared transcript passages or identical decoded PCM require an artist determination before new allocation. This is not an infringement finding or a way to combine per-asset allowances. Only conflicting historical allocations or edits longer than canonical evidence require manual financial reconciliation.
- If using a generated sample after December 31, 2027, create/update the sample source and manifest together rather than falsifying dates or source evidence.
