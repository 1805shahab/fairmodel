# Compliance rule semantics and provenance

The deterministic engine owns scope, dates, eligibility and money. Gemini assesses only transcript content and genuine purpose uncertainty. It cannot broaden approved rights or calculate a charge. Current policy version 4 retains version-3 semantic/source fixes and adds persistent overlap decisions and canonical billing; reevaluate historical reports before relying on eligibility.

## Medium and category vocabulary

`backend/app/canonical.py` is the audited equivalence registry. Matching ignores case, surrounding/repeated whitespace and underscore separators. It does not use fuzzy similarity or an LLM.

| Canonical distribution medium | Documented equivalents |
| --- | --- |
| `online_advertising` | online advertising; online advertisement(s); online commercial advertising; online commercial advertisement(s); internet advertising |
| `television` | television; television advertising; TV; TV advertising; broadcast television |
| `podcast` | podcast(s); podcast advertising; podcast advertisements |
| `radio` | radio; radio advertising; broadcast radio |
| `audiobook` | audiobook(s) |
| `film` | film; cinema; motion picture |

These categories describe distribution medium; they do not grant campaign, content, date, language or territory permission. Online advertising does not authorize TV, radio, podcast or film use. Identical unknown labels can match their explicitly approved label; non-identical unknown/restricted variants require semantic review. For example, “online advertising on approved news sites only” is not silently expanded to all online advertising. Generic “digital advertising” is intentionally unmapped because it may include offline displays.

The registry also maps US/USA/U.S./United States to the same territory label, and the explicit political-advertising/endorsement, gambling-promotion and adult-content-advertising variants used by the test contracts. An unusual creative narrative is not itself one of these prohibited categories.

## Condition routing

`backend/app/contract_rules.py` recognizes a small set of documented condition forms. Exact normalized administrative obligations are supported; ambiguous or mixed clauses default to human review.

| Kind | Check |
| --- | --- |
| Content | Supported “content/advertisement/transcript must not contain …” conditions go to Gemini together with restricted content categories. Possible conflict or uncertainty requires review, never an automatic penalty. |
| Campaign metadata | “Campaign category must be …” compares declared metadata deterministically. Unknown interpretations require review. |
| Administrative: submit for review before publication | Verify the studio's persisted upload and compliance-request audit receipts and analyzed asset. Never require the narrator to say that review occurred. Local receipts do not independently prove external publication timing. |
| Administrative: artist approves royalties before invoicing | Enforced at the later invoice stage by the separate artist decision and existing provider/route approval guards. It is not a transcript condition and does not create a circular requirement to approve a nonexistent royalty first. |
| Human interpretation | Unsupported wording, custom obligations and ambiguous conditions hold eligibility for review. No guessed administrative rule is treated as satisfied. |

Gemini receives only content rule IDs/text, the actual transcript and the declared category. Administrative clauses, financial allowances, geographic scope and medium labels are excluded from its decision task. Benign confirmations are not converted to conflicts just because they lack transcript quotations. Genuine findings require their supplied rule ID and exact supporting transcript passage. Purpose uncertainty remains advisory `NEEDS_REVIEW`.

## Source evidence and classification

Approved `LicenseVersion` snapshots stay immutable. Quotations are checked against actual extracted PDF page text. A missing special-condition citation can be repaired only by locating the entire already-approved clause verbatim on an actual source page, allowing PDF whitespace differences. The report records the literal matched text, real page, `verified=true` and `origin=source_text_match`. Recovery never changes the approved clause, invents a quote or clears genuine ambiguity. Only a stale machine-generated missing-citation warning is replaced after evidence is actually found.

Extraction and artist review revalidate evidence before persistence/activation. The report and license-detail API expose verified source evidence separately from immutable historical terms. Empty/invalid/unverified source blocks are omitted by the shared frontend renderer. Missing provenance remains a review reason; a claimed scope violation with missing rule provenance is `NEEDS_REVIEW`, not a substantiated restriction.

Reports include `rule_checks`, `substantiated_violations`, provider receipts, source-review diagnostics, overlap signals and administrative receipts. `RESTRICTED_USAGE` requires a supported deterministic violation of approved scope/dates/declared category or explicitly denied additional use. AI findings, missing facts, unknown medium equivalences, absent identity authorization and uncertain purpose produce `NEEDS_REVIEW`. Reasons and rule outcomes identify the actual cause.

## Usage, identity and overlapping recordings

The allowance uses measured **spoken** duration, not container length. Decimal arithmetic determines money. For 23.52 spoken seconds with a 30-second per-asset allowance and USD 2/s additional use: additional duration = 0 and estimated additional royalty = USD 0.00. Total duration of 38.477 seconds does not change that result.

Speaker verification remains optional and disabled. A score is never fabricated. Human artist identity/use attestation is distinct from independent identity verification and is required before an allocation. Artist charge approval remains separate. Unknown eligibility cannot create a proposal or invoice.

Raw file hashes deduplicate exact uploads within a license. New analyses additionally fingerprint normalized PCM samples, ignoring container metadata, to identify exact decoded duplicates. A conservative transcript-sequence screen flags a shared contiguous passage of at least 12 words covering at least 70% of the shorter transcript against earlier analyzed assets in that license. It catches the supplied excerpt case without downloading a model. Both signals hold new allocations; they never subtract arbitrary seconds, combine independent per-asset allowances or alter earlier financial history. Earlier-analysis evidence is included in report cache/charge eligibility checks.

An artist can resolve a pair as **SAME_USAGE**, **SEPARATE_USAGE** or **UNCERTAIN**, with a required note. Decisions are append-only, idempotent and bound to both assets' actual semantic evidence and the approved terms. Same usage links to the earliest canonical record without another allocation. Separate usage follows approved billing rules even when scripts resemble each other. Uncertain/stale decisions remain held. Valid unchanged decisions survive re-evaluation; changed transcript, measurements, metadata or contract version require fresh review. Circular and contradictory relationships are rejected.

Conflicting historical allocations/invoices are retained for reconciliation, as are edited versions with more speech than their canonical evidence covers. A valid original charge is not revoked just because an independent newer excerpt is uncertain. New invoice creation/sending requires current charge approval proof. No $0 usage is turned into a payable invoice. Workflow-only refresh can reuse a validated content assessment, explicitly retaining its original receipt and indicating that no fresh AI call was made; provider failures never cause fixture fallback.

Limitations: decoded hashes are not robust perceptual fingerprints; re-encoding may change samples. Transcript overlap is a review signal, not proof of audio identity, speaker identity or unauthorized use. Common scripts may produce false positives; changed recognition, other languages, edits or non-speech content may evade it. Unsupported contractual purpose disputes and conflicting historical finances require manual reconciliation; those cannot be bypassed just to make a charge pass.

## Verified supplied version-4 result

On November 9, 2026 the actual approved snapshot permitted online commercial advertisements for the declared campaign, United States/English, November 1–December 31, 2026, with 30 spoken seconds per asset and USD 2/additional second. The supplied recording measured 38.477 seconds total and 23.52 seconds VAD speech. Its saved successful Groq analysis was live, with nine timestamp segments; the older related recording had 28 live segments.

After the fixes, a new successful live Gemini request recorded the provider's actual returned model (`gemini-3.1-flash-lite`), response identifier and completion time. It returned no content conflict/uncertainty. The report now records **NEEDS_REVIEW**, **USD 0.00 estimated additional royalty**, **zero substantiated violations**, both administrative checks resolved at their proper workflow stages, and two exactly recovered special-condition citations. Identity/use authorization is still unresolved and a 59-word shared transcript passage with the earlier recording triggers overlap review. The total royalty count did not change.

Historical provider records are not retroactively assigned invented response IDs. Their saved successful-response provenance and completion audit are distinguished from merely configured models. New receipts are recorded only after a valid SDK response. Failed requests return a safe upstream status/category with no fixture fallback. PayPal integration is unchanged and remains deferred.
