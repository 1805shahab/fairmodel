"use client";
import { useState } from "react";
import { Check, Download, Save, Sparkles } from "lucide-react";
import {
  Badge,
  BusyButton,
  ErrorPanel,
  Field,
  Loading,
  PageHeading,
  useAction,
  useData,
} from "./ui";
import { endpoint, api, post } from "./api";
import { useWorkspace } from "./workspace";
import type { License, Terms } from "./types";

const lists: [keyof Terms, string][] = [
  ["permitted_media", "Permitted media"],
  ["territories", "Territories"],
  ["languages", "Languages"],
  ["campaigns", "Allowed campaigns"],
  ["restricted_categories", "Restricted content categories"],
  ["special_conditions", "Special conditions"],
  ["ambiguities", "Ambiguous or missing clauses"],
];
export default function LicenseDetail({ id }: { id: string }) {
  const { data, error, loading, retry } = useData<License>(`/licenses/${id}`);
  return loading ? (
    <Loading />
  ) : error ? (
    <ErrorPanel message={error} retry={retry} />
  ) : data ? (
    <Review key={`${data.id}-${data.version}`} license={data} />
  ) : null;
}
function Review({ license }: { license: License }) {
  const { role } = useWorkspace();
  const [terms, setTerms] = useState<Terms>(license.terms),
    [demo, setDemo] = useState(false),
    [note, setNote] = useState(""),
    [ack, setAck] = useState(false);
  const { busy, error, run } = useAction();
  const active = license.status === "ACTIVE",
    editable = role === "artist" && !active;
  const update = <K extends keyof Terms>(key: K, value: Terms[K]) =>
    setTerms((t) => ({ ...t, [key]: value }));
  async function save(approve: boolean) {
    await api(`/licenses/${license.id}/${approve ? "approve" : "terms"}`, {
      method: approve ? "POST" : "PUT",
      body: JSON.stringify({
        terms,
        note,
        expected_version: license.version,
        acknowledge_unknowns: ack,
      }),
    });
  }
  return (
    <>
      <PageHeading
        eyebrow={`VOICE LICENSE · VERSION ${license.version}`}
        title={license.title}
        description="Every extracted term stays connected to its source. Review the rules before approval."
        action={<Badge status={license.status} />}
      />
      <div className="detail-toolbar">
        <a
          className="button secondary"
          href={endpoint(`/licenses/${license.id}/contract`)}
          target="_blank"
          rel="noreferrer"
        >
          <Download size={15} />
          Source PDF
        </a>
        <span className="small">
          Extraction: <strong>{license.extraction_provider}</strong>
        </span>
      </div>
      {license.error && <ErrorPanel message={license.error} />}{" "}
      {editable && (
        <section className="panel extraction-bar">
          <div>
            <h2>Contract intelligence</h2>
            <p>
              Run Gemini on your PDF or explicitly select the bundled demo
              fixture.
            </p>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={demo}
                onChange={(e) => setDemo(e.target.checked)}
              />
              Use local demo fixture — not a Gemini result
            </label>
          </div>
          <BusyButton
            busy={busy}
            onClick={() =>
              void run(async () => {
                await post(`/licenses/${license.id}/extract`, {
                  use_demo_fixture: demo,
                });
              }, "Extraction ready for your review.")
            }
          >
            <Sparkles size={16} />
            Extract terms
          </BusyButton>
        </section>
      )}
      {demo && (
        <div className="alert warning">
          Local fixture mode. This does not call Gemini and only accepts the
          bundled sample PDF.
        </div>
      )}
      {active && (
        <div className="alert success">
          <Check size={17} />
          Artist-approved agreement. This version is immutable and ready for
          assigned studio submissions.
        </div>
      )}
      <div className="review-grid">
        <section className="panel form-panel">
          <div className="panel-heading inline">
            <div>
              <h2>{active ? "Approved terms" : "Review licensing terms"}</h2>
              <p>
                Empty means unknown. Use * only for an explicitly unrestricted
                scope.
              </p>
            </div>
            <Badge status={license.status} />
          </div>
          <fieldset disabled={!editable || busy}>
            <div className="form-grid">
              <Field label="Voice artist">
                <input
                  value={terms.artist || ""}
                  onChange={(e) => update("artist", e.target.value || null)}
                />
              </Field>
              <Field label="Production studio">
                <input
                  value={terms.studio || ""}
                  onChange={(e) => update("studio", e.target.value || null)}
                />
              </Field>
              <Field label="License starts">
                <input
                  type="date"
                  value={terms.start_date || ""}
                  onChange={(e) => update("start_date", e.target.value || null)}
                />
              </Field>
              <Field label="License ends">
                <input
                  type="date"
                  value={terms.end_date || ""}
                  onChange={(e) => update("end_date", e.target.value || null)}
                />
              </Field>
            </div>
            {lists.slice(0, 5).map(([key, label]) => (
              <Field
                key={key}
                label={label}
                hint="Separate values with commas. An empty field remains unknown."
              >
                <RuleInput
                  initial={terms[key] as string[] | null}
                  onChange={(values) =>
                    update(key, values.length ? values : null)
                  }
                />
              </Field>
            ))}
            <div className="form-grid">
              <Field label="Included voiced seconds">
                <input
                  type="number"
                  min="0"
                  step="0.001"
                  value={terms.included_seconds ?? ""}
                  onChange={(e) =>
                    update("included_seconds", e.target.value || null)
                  }
                />
              </Field>
              <Field label="Additional rate per second">
                <input
                  type="number"
                  min="0"
                  step="0.0001"
                  value={terms.additional_rate ?? ""}
                  onChange={(e) =>
                    update("additional_rate", e.target.value || null)
                  }
                />
              </Field>
              <Field label="Billing basis">
                <select
                  value={terms.billing_basis || ""}
                  onChange={(e) =>
                    update(
                      "billing_basis",
                      (e.target.value || null) as Terms["billing_basis"],
                    )
                  }
                >
                  <option value="">Unknown</option>
                  <option value="per_asset">Per asset</option>
                  <option value="cumulative">Cumulative per license</option>
                </select>
              </Field>
              <Field label="Currency">
                <select
                  value={terms.currency || ""}
                  onChange={(e) =>
                    update(
                      "currency",
                      (e.target.value || null) as Terms["currency"],
                    )
                  }
                >
                  <option value="">Unknown</option>
                  <option>USD</option>
                  <option>EUR</option>
                  <option>GBP</option>
                </select>
              </Field>
            </div>
            <Field label="Is additional usage explicitly permitted?">
              <select
                value={
                  terms.additional_usage_permitted === null
                    ? "unknown"
                    : String(terms.additional_usage_permitted)
                }
                onChange={(e) =>
                  update(
                    "additional_usage_permitted",
                    e.target.value === "unknown"
                      ? null
                      : e.target.value === "true",
                  )
                }
              >
                <option value="unknown">Unknown</option>
                <option value="true">
                  Yes — at the approved additional rate
                </option>
                <option value="false">
                  No — additional usage is restricted
                </option>
              </select>
            </Field>
            {lists.slice(5).map(([key, label]) => (
              <Field
                key={key}
                label={label}
                hint="One clause per line. Resolve ambiguities by reviewing the source."
              >
                <RuleInput
                  multiline
                  initial={terms[key] as string[]}
                  onChange={(values) => update(key, values)}
                />
              </Field>
            ))}
          </fieldset>
          {editable && (
            <>
              <Field
                label="Review note"
                hint="Required for edits and approval. Explain any manual corrections."
              >
                <textarea
                  minLength={5}
                  maxLength={2000}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="I reviewed the source agreement and confirmed these terms."
                />
              </Field>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={ack}
                  onChange={(e) => setAck(e.target.checked)}
                />
                I acknowledge unresolved unknowns require human review and
                cannot produce automatic invoices.
              </label>
              {error && <ErrorPanel message={error} />}
              <div className="form-footer">
                <BusyButton
                  className="button secondary"
                  busy={busy}
                  disabled={note.trim().length < 5}
                  onClick={() =>
                    void run(() => save(false), "Review changes saved.")
                  }
                >
                  <Save size={15} />
                  Save edits
                </BusyButton>
                <BusyButton
                  busy={busy}
                  disabled={note.trim().length < 5}
                  onClick={() =>
                    void run(
                      () => save(true),
                      "License approved and activated.",
                    )
                  }
                >
                  <Check size={16} />
                  Approve & activate
                </BusyButton>
              </div>
            </>
          )}
        </section>
        <aside className="evidence-column">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Source evidence</h2>
                <p>Verified quotes from the uploaded PDF.</p>
              </div>
            </div>
            <div className="evidence-list">
              {terms.evidence.length ? (
                terms.evidence.map((x, i) => (
                  <article key={i}>
                    <span className="eyebrow">
                      {x.field.replaceAll("_", " ")} · PAGE {x.page}
                    </span>
                    <blockquote>“{x.quote}”</blockquote>
                    <a
                      className="text-link"
                      href={`${endpoint(`/licenses/${license.id}/contract`)}#page=${x.page}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open source page {x.page} ↗
                    </a>
                  </article>
                ))
              ) : (
                <p className="muted">
                  Run extraction to see supporting text. Manually entered terms
                  should be checked against the source document.
                </p>
              )}
            </div>
          </section>
          <details className="panel source-pages">
            <summary>Extracted PDF text · {license.pages.length} pages</summary>
            {license.pages.map((p) => (
              <article key={p.page}>
                <strong>Page {p.page}</strong>
                <pre>{p.text}</pre>
              </article>
            ))}
          </details>
          <div className="alert info">
            Contract text is treated as untrusted data. AI extraction never
            activates terms or authorizes payments.
          </div>
        </aside>
      </div>
    </>
  );
}

function RuleInput({
  initial,
  onChange,
  multiline = false,
}: {
  initial: string[] | null;
  onChange: (value: string[]) => void;
  multiline?: boolean;
}) {
  const [raw, setRaw] = useState((initial || []).join(multiline ? "\n" : ", "));
  function change(value: string) {
    setRaw(value);
    onChange(
      value
        .split(multiline ? "\n" : ",")
        .map((x) => x.trim())
        .filter(Boolean),
    );
  }
  return multiline ? (
    <textarea rows={3} value={raw} onChange={(e) => change(e.target.value)} />
  ) : (
    <input value={raw} onChange={(e) => change(e.target.value)} />
  );
}
