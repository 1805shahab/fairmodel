## Inspiration

**Every voice deserves a fair share.**

AI makes generating speech easier, but permission and fair compensation remain complicated. A voice license may restrict campaigns, distribution channels, territories, dates, content and duration. Artists and studios need a way to connect those rules to actual recordings and payments.

FairModel began with a question: _What if every synthetic voice campaign had an inspectable path from permission to payment?_

We wanted artists to retain control while giving studios a practical way to understand their obligations.

## What it does

FairModel connects **artist-authorized voice generation, licensing, audio compliance, royalties and PayPal Sandbox invoicing** in one workspace.

1. **Approve the agreement.** An artist uploads a licensing PDF. Gemini extracts structured terms with supporting quotations and page references. The artist reviews and edits the terms before activating a version.
2. **Authorize generation.** The artist uploads an authorized reference recording and grants the assigned studio separate, provider-specific voice replication and processing permission. Storage consent alone never authorizes cloning.
3. **Create the advertisement.** The studio enters an original script and permitted campaign metadata. Fish Audio generates reference-conditioned speech using the consented sample. Studios can also upload authorized audio produced elsewhere.
4. **Analyze actual usage.** FFprobe measures total duration, WebRTC VAD estimates speech activity, and Groq Whisper transcribes the recording.
5. **Evaluate and review.** Gemini provides advisory content findings. Deterministic rules check approved scope and workflow requirements. Artists review identity and campaign authorization and resolve potential overlapping usage.
6. **Calculate and invoice.** Python Decimal calculates eligible additional royalties. Separate artist charge approval gates genuine PayPal Sandbox invoicing. Payment status comes from authoritative provider information.

We successfully tested and saved a Fish Audio reference-conditioned generation; the owner reported that it reproduced the reference voice. **Generation does not independently verify identity or establish authorization, compliance or payment eligibility.**

## How we built it

The frontend uses **Next.js, React, TypeScript and Tailwind CSS**, with a recording-studio ledger design. Contract evidence, audio playback, review actions and financial explanations connect to actual records.

**AG Grid Community** powers ledger filtering, sorting, calculation details and CSV export. Three.js provides original decorative artwork, explicitly labelled as non-verification evidence.

The backend uses **Python, FastAPI, Pydantic, SQLAlchemy and SQLite**. It persists approved contract versions, provider provenance, evidence revisions, artist decisions and payment events.

Gemini handles contract extraction and advisory compliance. Groq handles transcription. Fish generation uses inline references, an artist-reviewed reference transcript and the exact requested `s2.1-pro-free` model. It creates no reusable provider voice profile and never silently switches providers or paid models. FFmpeg validates and normalizes generated output before asset creation.

Financial calculations remain independent of AI:

$$
\text{Additional royalty} = \max(0,\text{spoken seconds}-\text{remaining allowance}) \times \text{approved rate}
$$

This applies only when additional use is permitted and required eligibility reviews are satisfied. Decimal arithmetic and explicit final rounding keep the calculation explainable.

The **APIMatic PayPal Context Plugin** informed authentication, resilience, errors and testing. Its inspected SDK coverage did not include Invoicing v2; those endpoints use official PayPal REST schemas through HTTPX. A guarded **Postman collection** is included, without claiming execution in Postman.

The **Render preview** offers shared demo access and temporary storage. PayPal draft/send is disabled there; durable financial demonstrations run locally.

## Challenges we ran into

**Separating evidence from authority.** A transcript cannot establish consent or prove an administrative review occurred. We separated AI content observations, campaign declarations, contractual rules, stored workflow events and human decisions.

**Handling generated audio safely.** WAV responses exposed inconsistent declared container lengths. The Fish adapter now requests completed MP3, validates it, normalizes it with FFmpeg and validates the final WAV before creating an asset. Failures never become fabricated success.

**Managing uncertain payments.** A timeout does not prove an invoice was never created. Durable operation records, duplicate constraints and reconciliation help prevent blind retries and repeated financial writes.

**Building an honest short demo.** The main video walkthrough uses fictional Windows stock-voice material. It separately shows the saved successful Fish generation, avoiding another transfer of the private reference recording. It does not show a fresh cloning request during filming. This filming choice did not remove the application feature.

## Accomplishments that we're proud of

- Connected consented generation, source-backed licensing, measured usage, artist decisions and payment evidence.
- Tested and saved successful Fish reference-conditioned speech generation.
- Verified live Gemini extraction/compliance and live Groq transcription.
- Implemented deterministic royalties, overlap review, stale-approval checks and financial safeguards.
- Built genuine PayPal Sandbox invoicing and authoritative payment-status synchronization.
- Added automated coverage for permissions, citations, provider failures, calculations and duplicate prevention.

In the recorded walkthrough, Gemini extracted **19 supporting citations**. The stock-voice ad measured **58.38 spoken seconds**. With 30 included seconds and USD 2 per additional permitted second, the backend calculated **USD 56.76** after review. No invoice was created for this new example.

The ending separately refreshes an earlier **USD 17.46 PayPal Sandbox invoice**, confirming paid status and zero outstanding. It is not payment for the new calculation. **No real money is transferred.**

## What we learned

**Processing, compliance, identity, authorization and payment are different states.**

A generated voice is not identity proof. Manual confirmation is an attestation, not biometrics. AI findings are not legal judgments. Sending an invoice does not prove payment.

Trust comes from preserving evidence, showing uncertainty and keeping the right decisions with the artist. Reliable integrations need validation, provenance, safe failures and reconciliation—not just successful API calls.

## What's next for FairModel

Our next priorities are production authentication, tenant-aware permissions, durable hosted storage, tested recovery and background audio processing.

We also plan live webhook delivery verification, broader Sandbox payment scenarios, scanned-contract OCR, improved ambiguous-clause review and evaluated acoustic overlap detection. Retention/deletion/export controls and provider agreements are important before handling sensitive production voice data. Merchant onboarding and additional currencies require further integration and review.

FairModel's goal remains simple: **make the journey from voice permission to compensation understandable, reviewable and fair.**

[Try the hosted preview](https://fairmodel.onrender.com) · [Source code and setup](https://github.com/1805shahab/fairmodel) · [Shared demo login](https://github.com/1805shahab/fairmodel#hosted-demo-login)
