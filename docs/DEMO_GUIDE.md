# Three-minute FairModel demonstration

## Preparation

Start both servers using README's PowerShell commands. Generate local fixtures with `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/create-demo.ps1` if missing. Use localhost:3000 and the **Demo & integrations** screen to download the sample PDF/audio. Use this exact generated pair; arbitrary files cannot use fixture results. The sample PDF names fictional parties; audio is Windows stock synthetic narration, not an artist voice clone.

For a live AI judging run, configure Gemini and Groq on the backend before starting. Leave all fixture checkboxes unchecked. A live demo is not verified until both providers actually complete requests. Keep a separate clearly disclosed fixture run available for quota/network problems. Never claim a fixture result is Gemini/Groq.

## Interactive control room preview

Open `/control-room` for a separate, client-only cinematic product preview. Its fictional sample artist, contract clauses, generated events, voice-match display, earnings, invoices, and payouts are local mock data; they are not derived from uploads, backend records, or a real voice analysis. Navigate among Identity overview, Contract ingestion, Live control room, Generation audit, and Royalty ledger. Use **Use sample contract**, **Simulate breach**, or **Demo mode** to demonstrate the interactions. The demo story lasts 60 seconds; `Ctrl+K` opens the command palette.

The breach panel illustrates a simulated Brazil / gambling scope violation and requires artist review before approving its proposed demo amount. Ledger approvals and payouts are also simulated. Every payment view must state **DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED**. There is no PayPal connection, invoice creation, payout, or transfer in this preview. On narrow/coarse-pointer screens, reduced-motion settings, or low-power devices, the orb uses a 2D fallback; the screens remain usable.

## 0:00–0:20 — Why FairModel

Show the landing page: “Every voice deserves a fair share. FairModel translates voice licensing into evidence-backed usage rules and transparent royalties. The artist stays in control.” Open the workspace. Explain that the role selector is **demo identity**, not production login.

## 0:20–1:00 — Set the terms

Artist view → **New voice license** → name the agreement → select sample PDF → Upload & continue. In this credential-free demo, explicitly check **Use local demo fixture — not a Gemini result** and extract. Show page-linked exact source quotes and editable structured terms. For live AI, use the real provider instead and explain its persisted model identifier.

Point to 30 included voiced seconds per asset, USD 2 per extra second, US / online advertising / English, and prohibited political advertising. Add a review note and **Approve & activate**. Explain that AI cannot activate contracts or invent unknown terms; unknowns and unresolved clauses require review.

## 1:00–1:45 — Measure and explain the usage

Switch to Studio → Audio submissions → Submit audio. Select the newly approved license. Campaign: Northstar launch; region **US**; medium **online advertising**; language **English**; category **consumer products**; intended date within January 1, 2026–December 31, 2027. Select the sample narration.

Upload, explicitly enable local fixture mode, **Analyze audio**, then **Evaluate compliance** with fixture mode still selected. Play the recording. Show actual FFmpeg/ffprobe metadata, distinct total/speech duration, WebRTC VAD segments, and transcript provenance. The bundled transcript has no timestamps; the live Groq adapter requests segment timestamps. No artificial word timings or speaker confidence scores are generated.

Show the exact formula: `max(0, measured speech − 30 seconds) × USD 2`. The payable amount depends on locally generated narration and actual VAD measurement, so do not promise an invented fixed demo amount. For the deterministic 45-second unit-test scenario, the verified result is **USD 30**.

## 1:45–2:25 — Approve and simulate settlement

Switch to Artist → Royalties. Open the evidence if needed, enter a review note, and approve the positive charge. Create a **simulated invoice**. Open Invoices & payments and use the on-screen three-step guide to explain the Artist → Studio handoff. Point to:

**DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED**

Simulate sending. Switch to Studio and deliberately simulate payment completion. Show the obviously simulated ID and CREATED → SENT → PAID_SIMULATED event history. Use **See PayPal Sandbox status** to confirm the adapter is not connected. Explain: “No PayPal request, email, or funds transfer occurred. A provider interface isolates the future PayPal adapter.”

## 2:25–3:00 — Accountability and honest status

Show Analytics: real persisted royalty entries in Community AG Grid with sorting/filtering/CSV export and separate currency totals. Show Audit trail. Explain that possible prohibited content or missing restricted-region metadata is held for human review and produces no automatic invoice. Exact duplicate uploads reuse the asset/charge.

Close with: “Real PayPal Sandbox OAuth, Invoicing v2, and verified webhooks remain required for the final hackathon submission. Account access currently blocks that phase. This development build demonstrates the licensing, media, compliance, royalty, and explicitly simulated invoice workflow.”

## Recovery and additional scenarios

- Missing region: leave region empty with sample contract → NEEDS_REVIEW → no royalty. In asset detail, correct metadata → reevaluate. Metadata is immutable after a royalty allocation exists.
- Declared political advertising: category `political advertising` → RESTRICTED_USAGE → no royalty or invoice. AI-only possible category conflicts yield NEEDS_REVIEW rather than a definitive legal conclusion.
- Duplicate file: upload identical file under the same license → existing asset ID, unchanged metadata and no new charge.
- Missing AI key: uncheck demo → useful 503, preserved input, no fabricated result. Check integration status, configure the backend, and retry, or explicitly choose the sample fixture.
- Invalid media: renaming a non-audio file to `.wav` does not pass ffprobe validation.
- Speaker experiment: disabled by default. Do not claim voice identity or a running ECAPA model. The optional worker has not been validated with model inference.
- If using a generated sample after December 31, 2027, create/update the sample source and manifest together rather than falsifying dates or source evidence.
