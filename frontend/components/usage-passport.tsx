"use client";
import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Printer, ShieldCheck } from "lucide-react";
import { useData, Badge, ErrorPanel, Loading, PageHeading } from "./ui";
import { date, money } from "./api";
import type { Passport } from "./passport-types";
import RecordingPlayer from "./recording-player";
import EvidenceExplorer from "./evidence-explorer";
import SourceCitations from "./source-citations";

export default function UsagePassport({ id }: { id: string }) {
  const {
    data: p,
    error,
    loading,
    retry,
  } = useData<Passport>(`/assets/${id}/passport`);
  const player = useRef<HTMLAudioElement | null>(null);
  const connect = useCallback((node: HTMLAudioElement | null) => {
    player.current = node;
  }, []);
  const [active, setActive] = useState(-1);
  if (loading) return <Loading />;
  if (error) return <ErrorPanel message={error} retry={retry} />;
  if (!p) return null;
  const asset = p.asset,
    audio = asset.analysis?.result,
    report = asset.report?.result;
  const calc = asset.royalty?.calculation || report?.calculation,
    invoice = asset.invoice;
  function seek(seconds: number) {
    if (
      player.current &&
      audio &&
      seconds >= 0 &&
      seconds < Number(audio.duration_seconds)
    ) {
      player.current.currentTime = seconds;
      player.current.focus();
    }
  }
  return (
    <div className="passport-page">
      <PageHeading
        eyebrow="PRIVATE • VOICE USAGE PASSPORT"
        title={asset.campaign.name}
        description="One recording. Its permissions, evidence, decisions and financial history."
        action={
          <div className="passport-actions">
            <Link
              className="button secondary"
              href={`/dashboard/submissions/${id}`}
            >
              Open recording <ArrowUpRight size={15} />
            </Link>
            <button
              type="button"
              className="button secondary"
              onClick={() => window.print()}
            >
              <Printer size={15} />
              Print / save PDF
            </button>
          </div>
        }
      />
      <section className="passport-cover panel">
        <div>
          <ShieldCheck size={27} />
          <span className="eyebrow">WORKFLOW RECORD</span>
          <h2>Voice Usage Passport</h2>
          <code>{p.id}</code>
          <p>{p.disclaimer}</p>
        </div>
        <div>
          <Badge status={asset.compliance_state || "PENDING"} />
          <p className="small">
            Snapshot:{" "}
            <time dateTime={p.snapshot_at}>
              {new Date(p.snapshot_at).toLocaleString()}
            </time>
          </p>
          <p className="small muted">
            Private under the local demo-persona access model. Not a public
            verification link.
          </p>
        </div>
      </section>
      <ol
        className="passport-lifecycle"
        aria-label="Independent lifecycle evidence"
      >
        {p.stages.map((stage, i) => (
          <li key={stage.label} data-state={stage.state}>
            <span>{String(i + 1).padStart(2, "0")}</span>
            <strong>{stage.label}</strong>
            <small>
              {stage.state === "simulated"
                ? "Completed in simulation"
                : stage.state}
            </small>
            <p>{stage.detail}</p>
          </li>
        ))}
      </ol>
      <section className="panel">
        <div className="section-heading">
          <h2>Recording & ownership</h2>
          <span className="eyebrow">LICENSE VERSION {p.license.version}</span>
        </div>
        <dl className="passport-facts">
          {[
            ["Artist", p.artist.name],
            ["Studio", p.studio.name],
            ["Filename", asset.original_name],
            ["Asset ID", id],
            ["Submitted", date(asset.created_at)],
            ["Approved agreement", p.license.title],
            [
              "Recording duration",
              audio ? `${audio.duration_seconds}s` : "Not analyzed",
            ],
            [
              "Measured speech",
              audio?.spoken_seconds
                ? `${audio.spoken_seconds}s · ${audio.vad}`
                : "Unavailable",
            ],
            [
              "Transcription",
              `${p.provenance.transcription} · ${audio?.provider || "not run"}`,
            ],
            [
              "Content assessment",
              `${p.provenance.compliance} · ${report?.provider || "not run"}`,
            ],
          ].map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        <details>
          <summary>Integrity and analysis revision</summary>
          <p className="small">{p.audio_evidence.hash_note}</p>
          <dl className="passport-facts">
            <div>
              <dt>File SHA-256</dt>
              <dd>
                <code>{p.audio_evidence.sha256}</code>
              </dd>
            </div>
            <div>
              <dt>Analysis revision hash</dt>
              <dd>
                <code>
                  {p.audio_evidence.analysis_revision || "No analysis"}
                </code>
              </dd>
            </div>
            <div>
              <dt>Analysis ID</dt>
              <dd>{p.audio_evidence.analysis_id || "Not run"}</dd>
            </div>
            <div>
              <dt>Audio processing</dt>
              <dd>{p.audio_evidence.processing}</dd>
            </div>
          </dl>
        </details>
        <div className="no-print">
          <RecordingPlayer
            id={id}
            result={audio}
            onPlayer={connect}
            onSegment={setActive}
          />
        </div>
        {audio && (
          <details>
            <summary>Transcript and provider timestamps</summary>
            <p>{audio.transcript}</p>
            <div className="passport-segments">
              {audio.timestamps
                .filter(
                  (s) =>
                    Number.isFinite(s.start) &&
                    Number.isFinite(s.end) &&
                    s.start >= 0 &&
                    s.end > s.start &&
                    s.end <= Number(audio.duration_seconds) &&
                    s.start < Number(audio.duration_seconds),
                )
                .map((s, i) => (
                  <button
                    type="button"
                    aria-pressed={i === active}
                    key={i}
                    onClick={() => seek(s.start)}
                  >
                    <time>{s.start.toFixed(2)}s</time>
                    {s.text}
                  </button>
                ))}
            </div>
          </details>
        )}
      </section>
      {asset.next_action && (
        <div className="alert warning">
          <strong>Current next action</strong>
          <p>{asset.next_action}</p>
          <Link className="text-link" href={`/dashboard/reviews?asset=${id}`}>
            Open Review Center →
          </Link>
        </div>
      )}
      {report ? (
        <EvidenceExplorer
          report={report}
          audio={audio}
          campaign={asset.campaign}
          licenseId={p.license.id}
          onSeek={seek}
        />
      ) : (
        <section className="panel">
          <h2>Compliance pending</h2>
          <p>
            No compliance result has been recorded. Audio processing alone does
            not establish permission.
          </p>
        </section>
      )}
      {report && (
        <section className="panel passport-print-evidence">
          <h2>Complete compliance evidence snapshot</h2>
          <p>{report.primary_reason}</p>
          <p>
            Provider: {report.provider} · current status:{" "}
            {asset.compliance_state}
          </p>
          {report.rule_checks?.map((rule, i) => (
            <article key={i}>
              <h3>
                {rule.rule.replaceAll("_", " ")} · {rule.outcome}
              </h3>
              <p>{rule.explanation}</p>
              <SourceCitations
                items={rule.citations || []}
                licenseId={p.license.id}
              />
            </article>
          ))}
          {report.findings.findings.map((finding, i) => (
            <article key={i}>
              <h3>Advisory observation: {finding.category}</h3>
              {finding.passage && <blockquote>{finding.passage}</blockquote>}
              <p>{finding.explanation}</p>
            </article>
          ))}
          <h3>Unresolved requirements</h3>
          {(report.unresolved_conditions || report.reasons).map((reason, i) => (
            <p key={i}>{reason}</p>
          ))}
        </section>
      )}
      <section className="panel">
        <h2>Artist authorization</h2>
        <p>
          Manual attestation is separate from automatic speaker verification.
        </p>
        <Badge status={asset.authorization?.status || "unresolved"} />
        {asset.authorization ? (
          <dl className="passport-facts">
            <div>
              <dt>Identity attested</dt>
              <dd>{asset.authorization.identity_confirmed ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Campaign authorized</dt>
              <dd>{asset.authorization.use_authorized ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Reviewer</dt>
              <dd>
                {p.artist.name} · {asset.authorization.artist_id}
              </dd>
            </div>
            <div>
              <dt>Reviewed</dt>
              <dd>
                {new Date(asset.authorization.updated_at).toLocaleString()}
              </dd>
            </div>
            <div>
              <dt>Note</dt>
              <dd>{asset.authorization.note}</dd>
            </div>
          </dl>
        ) : (
          <p className="muted">No artist attestation is recorded.</p>
        )}
        <Link className="text-link" href={`/dashboard/submissions/${id}`}>
          Inspect or update the existing authorization workflow →
        </Link>
      </section>
      <section className="panel passport-finance">
        <span className="eyebrow">DETERMINISTIC FINANCIAL RULES</span>
        <h2>Royalty breakdown</h2>
        {calc ? (
          <>
            <dl className="passport-facts">
              {[
                ["Billable speech", `${calc.spoken_seconds}s`],
                [
                  "Included allowance",
                  `${calc.included_seconds}s · ${calc.billing_basis.replaceAll("_", " ")}`,
                ],
                ["Previously allocated", `${calc.prior_seconds}s`],
                ["Allowance remaining", `${calc.allowance_remaining}s`],
                ["Additional speech", `${calc.additional_seconds}s`],
                [
                  "Approved rate",
                  `${money(calc.rate, calc.currency)} / second`,
                ],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
            {!report?.eligible_for_charge && (
              <p className="alert warning">
                Historical or conditional calculation — not authorization to
                invoice.
              </p>
            )}
            <p className="passport-amount">
              {money(calc.amount, calc.currency)}
            </p>
            <p>{calc.explanation}</p>
            <p className="small">
              {calc.rounding}.{" "}
              {report?.eligible_for_charge
                ? "Eligibility is still revalidated before approval/invoicing."
                : "Calculation is historical or conditional; it does not authorize a payable charge."}
            </p>
            {asset.royalty && (
              <>
                <Badge status={asset.royalty.status} />
                <p>
                  Charge approval current:{" "}
                  {asset.royalty.approval_current ? "Yes" : "No"}. Allocation:{" "}
                  <code>{asset.royalty.id}</code>
                </p>
              </>
            )}
          </>
        ) : (
          <p>
            No eligible financial calculation is recorded. Rates and
            measurements are not invented.
          </p>
        )}
        <details>
          <summary>Financial source clauses</summary>
          <SourceCitations
            licenseId={p.license.id}
            items={p.license.source_review.citations.filter((c) =>
              [
                "included_seconds",
                "additional_rate",
                "billing_basis",
                "currency",
                "additional_usage_permitted",
              ].includes(c.field),
            )}
          />
        </details>
        {p.charge_approvals?.length > 0 && (
          <details>
            <summary>Recorded artist charge approvals</summary>
            {p.charge_approvals.map((approval) => (
              <article key={approval.id}>
                <strong>
                  {new Date(approval.created_at).toLocaleString()} ·{" "}
                  {approval.artist_id}
                </strong>
                <blockquote>{approval.note}</blockquote>
                <p className="small">
                  Bound assessment: <code>{approval.evidence_hash}</code>.
                  Current eligibility and approval status appear above.
                </p>
              </article>
            ))}
          </details>
        )}
      </section>
      <section className="panel">
        <h2>Invoice & payment</h2>
        {invoice ? (
          <>
            <div className="alert info">{invoice.notice}</div>
            <dl className="passport-facts">
              <div>
                <dt>Provider</dt>
                <dd>{invoice.provider}</dd>
              </div>
              <div>
                <dt>
                  {invoice.provider === "paypal_sandbox" && !invoice.simulated
                    ? "PayPal Sandbox invoice ID"
                    : "Simulated invoice ID"}
                </dt>
                <dd>{invoice.provider_id}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <Badge status={invoice.status} />
                </dd>
              </div>
              <div>
                <dt>Amount</dt>
                <dd>{money(invoice.amount, invoice.currency)}</dd>
              </div>
              {invoice.sandbox && (
                <>
                  <div>
                    <dt>Provider-reported received</dt>
                    <dd>
                      {money(invoice.sandbox.paid_amount, invoice.currency)}
                    </dd>
                  </div>
                  <div>
                    <dt>Last successful synchronization</dt>
                    <dd>
                      {invoice.sandbox.last_synced_at || "Not synchronized"}
                    </dd>
                  </div>
                </>
              )}
            </dl>
            <details>
              <summary>Recorded payment events</summary>
              <ol className="review-thread-events">
                {invoice.events?.map((event) => (
                  <li key={event.id}>
                    <strong>{event.kind.replaceAll("_", " ")}</strong>
                    <p>
                      {new Date(event.created_at).toLocaleString()} ·{" "}
                      {event.simulated ? "Simulated event" : "Sandbox event"}
                    </p>
                  </li>
                ))}
              </ol>
              {invoice.sandbox && (
                <>
                  <p className="small">
                    Persisted provider-reported transaction details; not a
                    production settlement record.
                  </p>
                  <pre>
                    {JSON.stringify(invoice.sandbox.transactions, null, 2)}
                  </pre>
                </>
              )}
            </details>
            <Link className="text-link" href="/dashboard/invoices">
              Inspect invoice and payment events →
            </Link>
            <p className="small muted">
              Sending an invoice is not evidence of payment. This passport
              displays persisted status; opening it never contacts PayPal.
            </p>
          </>
        ) : (
          <p>No invoice exists. Included usage requires no payable invoice.</p>
        )}
      </section>
      <section className="panel">
        <h2>Approved licensing scope</h2>
        {p.license.terms ? (
          <dl className="passport-facts">
            {Object.entries(p.license.terms)
              .filter(([key]) => !["evidence", "ambiguities"].includes(key))
              .map(([key, value]) => (
                <div key={key}>
                  <dt>{key.replaceAll("_", " ")}</dt>
                  <dd>
                    {value == null
                      ? "Unknown — review required"
                      : Array.isArray(value)
                        ? value.join(" · ") || "None recorded"
                        : String(value)}
                  </dd>
                </div>
              ))}
          </dl>
        ) : (
          <p>Approved snapshot unavailable.</p>
        )}
        <details>
          <summary>Supporting approved PDF clauses</summary>
          <SourceCitations
            licenseId={p.license.id}
            items={p.license.source_review.citations}
          />
          {p.license.source_review.review_reasons.map((reason, i) => (
            <p key={i} className="alert warning">
              {reason}
            </p>
          ))}
        </details>
        {report?.billing_usage?.member_asset_ids && (
          <div>
            <h3>Related licensed usage</h3>
            {report.billing_usage.member_asset_ids
              .filter((member) => member !== id)
              .map((member) => (
                <p key={member}>
                  <Link
                    className="text-link"
                    href={`/dashboard/submissions/${member}/passport`}
                  >
                    {member} →
                  </Link>
                </p>
              ))}
            <p>
              {report.billing_usage.disposition}. Transcript similarity
              indicates possible reuse, not proof of identical recordings.
            </p>
          </div>
        )}
        {!!report?.overlap?.length && (
          <details>
            <summary>Potentially overlapping submissions</summary>
            {report.overlap.map((related, index) => (
              <p key={`${related.asset_id}-${index}`}>
                <Link
                  className="text-link"
                  href={`/dashboard/submissions/${related.asset_id}/passport`}
                >
                  {related.asset_id} →
                </Link>
                <br />
                {related.basis} · {related.kind.replaceAll("_", " ")}
              </p>
            ))}
            <p className="small muted">
              Transcript overlap indicates possible reuse. No acoustic
              fingerprint match or identity proof is claimed.
            </p>
          </details>
        )}
      </section>
      <section className="panel">
        <h2>Assessment & approval history</h2>
        <p className="small muted">{p.history_note}</p>
        {p.history.map((revision) => (
          <details key={revision.id}>
            <summary>
              {revision.kind} ·{" "}
              {new Date(revision.snapshot.updated_at).toLocaleString()} ·{" "}
              {revision.snapshot.status ||
                revision.snapshot.result?.status ||
                "Recorded"}
            </summary>
            <p>
              Provider:{" "}
              {revision.snapshot.result?.provider ||
                "Manual artist / local processing record"}
            </p>
            {revision.snapshot.note && (
              <blockquote>{revision.snapshot.note}</blockquote>
            )}
            <p>
              Evidence revision: <code>{revision.revision_hash}</code>
            </p>
            <p className="small">
              Capture origin: {revision.origin}. Retained history; current
              eligibility appears above.
            </p>
            {revision.snapshot.result && (
              <details>
                <summary>Recorded structured evidence</summary>
                <pre>{JSON.stringify(revision.snapshot.result, null, 2)}</pre>
              </details>
            )}
          </details>
        ))}
      </section>
      <section className="panel">
        <h2>Audit timeline</h2>
        <ol className="passport-audit">
          {p.audit.map((event) => (
            <li key={event.id}>
              <time dateTime={event.created_at}>
                {new Date(event.created_at).toLocaleString()}
              </time>
              <div>
                <strong>
                  {event.action.replaceAll(".", " · ").replaceAll("_", " ")}
                </strong>
                <p>
                  {event.actor_name} · <code>{event.entity_id}</code>
                </p>
                <details>
                  <summary>Recorded event details</summary>
                  <pre>{JSON.stringify(event.detail, null, 2)}</pre>
                </details>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
