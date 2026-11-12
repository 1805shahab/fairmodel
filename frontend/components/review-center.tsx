"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Badge,
  BusyButton,
  ErrorPanel,
  Field,
  Loading,
  PageHeading,
  useData,
} from "./ui";
import { api, post } from "./api";
import { useWorkspace } from "./workspace";
import type { Asset } from "./types";
import type { Passport, ReviewCase } from "./passport-types";

export default function ReviewCenter({
  initialAssetId = "",
}: {
  initialAssetId?: string;
}) {
  const { role, refresh, notify } = useWorkspace();
  const assets = useData<Asset[]>("/assets"),
    cases = useData<ReviewCase[]>("/review-cases");
  const [assetId, setAssetId] = useState(initialAssetId),
    [filter, setFilter] = useState("OPEN");
  const [decision, setDecision] = useState("REQUEST_CHANGES"),
    [category, setCategory] = useState("metadata");
  const [note, setNote] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const request = useRef({ signature: "", key: "" });
  const [referenceData, setReferenceData] = useState<{
    asset: string;
    items: { id: string; label: string }[];
  }>({ asset: "", items: [] });
  const references = referenceData.asset === assetId ? referenceData.items : [];
  const [evidenceRef, setEvidenceRef] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    if (assetId)
      void api<Passport>(`/assets/${assetId}/passport`, {
        signal: controller.signal,
      })
        .then((p) => {
          if (!controller.signal.aborted)
            setReferenceData({
              asset: assetId,
              items: [
                ...[
                  "analysis",
                  "report",
                  "authorization",
                  "royalty",
                  "invoice",
                ].flatMap((key) => {
                  const record =
                    p.asset[
                      key as
                        | "analysis"
                        | "report"
                        | "authorization"
                        | "royalty"
                        | "invoice"
                    ];
                  return record && "id" in record
                    ? [
                        {
                          id: String(record.id),
                          label: `Current ${key} record`,
                        },
                      ]
                    : [];
                }),
                ...Array.from(
                  new Set(
                    p.license.source_review.citations.map((c) => c.field),
                  ),
                ).map((field) => ({
                  id: `contract:${field}`,
                  label: `Approved clause: ${field.replaceAll("_", " ")}`,
                })),
              ],
            });
        })
        .catch(() => {
          /* The main request displays errors; no evidence is invented. */
        });
    return () => controller.abort();
  }, [assetId, role]);
  const selected = assets.data?.find((asset) => asset.id === assetId);
  const visible =
    cases.data?.filter(
      (row) =>
        (filter === "ALL" ||
          (filter === "OPEN"
            ? row.status !== "RESOLVED"
            : row.status === "RESOLVED")) &&
        (!assetId || row.asset_id === assetId),
    ) || [];
  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!selected || busy) return;
    const signature = JSON.stringify([
      assetId,
      decision,
      category,
      note,
      evidenceRef,
    ]);
    if (request.current.signature !== signature)
      request.current = { signature, key: crypto.randomUUID() };
    setBusy(true);
    setError("");
    try {
      await post(`/assets/${assetId}/review-cases`, {
        request_key: request.current.key,
        decision,
        category,
        note,
        evidence_refs: references.some((ref) => ref.id === evidenceRef)
          ? [evidenceRef]
          : [],
      });
      setNote("");
      refresh();
      notify("Artist decision recorded. No invoice was sent or changed.");
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Decision could not be saved. Retry.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="HUMAN REVIEW • NO AUTOMATIC FINANCIAL ACTIONS"
        title={
          role === "artist" ? "Artist Review Center" : "Studio Review Center"
        }
        description="Inspect usage, request corrections and resolve concerns with a recorded decision."
      />
      {(assets.loading || cases.loading) && <Loading />}
      {(assets.error || cases.error || error) && (
        <ErrorPanel
          message={assets.error || cases.error || error}
          retry={() => {
            assets.retry();
            cases.retry();
          }}
        />
      )}
      <div className="review-center-grid">
        <section className="panel">
          <h2>Usage review desk</h2>
          <Field label="Select a recording">
            <select
              value={assetId}
              onChange={(e) => setAssetId(e.target.value)}
            >
              <option value="">All recordings</option>
              {assets.data?.map((asset) => (
                <option value={asset.id} key={asset.id}>
                  {asset.campaign.name} — {asset.original_name}
                </option>
              ))}
            </select>
          </Field>
          {!assetId && (
            <div className="pending-reviews">
              <h3>Pending usage reviews</h3>
              {assets.data
                ?.filter(
                  (asset) =>
                    asset.compliance_state === "NEEDS_REVIEW" ||
                    asset.authorization_state !== "artist_confirmed",
                )
                .map((asset) => (
                  <button
                    type="button"
                    key={asset.id}
                    onClick={() => setAssetId(asset.id)}
                  >
                    <strong>{asset.campaign.name}</strong>
                    <span>{asset.original_name}</span>
                    <Badge status={asset.compliance_state || "PENDING"} />
                  </button>
                ))}
              {assets.data?.length === 0 && <p>No submitted recordings yet.</p>}
            </div>
          )}
          {selected && (
            <>
              <div className="review-selected">
                <Badge status={selected.compliance_state || "PENDING"} />
                <h3>{selected.campaign.name}</h3>
                <p>
                  {selected.original_name} · license version{" "}
                  {selected.license_version}
                </p>
                <p>{selected.next_action}</p>
                <div className="passport-actions">
                  <Link
                    className="button secondary"
                    href={`/dashboard/submissions/${assetId}/passport`}
                  >
                    Inspect usage passport
                  </Link>
                  <Link
                    className="text-link"
                    href={`/dashboard/submissions/${assetId}`}
                  >
                    Listen, review identity & correct metadata →
                  </Link>
                </div>
              </div>
              {role === "artist" ? (
                <form onSubmit={save}>
                  <Field label="Artist decision">
                    <select
                      value={decision}
                      onChange={(e) => setDecision(e.target.value)}
                    >
                      <option value="APPROVE_USAGE">
                        Approve usage review
                      </option>
                      <option value="REQUEST_CHANGES">Request changes</option>
                      <option value="REJECT_USAGE">
                        Reject proposed usage
                      </option>
                      <option value="INVESTIGATE">
                        Flag concern for investigation
                      </option>
                    </select>
                  </Field>
                  <Field label="Reason category">
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                    >
                      {[
                        ["campaign", "Unauthorized campaign"],
                        ["medium", "Usage medium"],
                        ["voice_identity", "Suspected voice mismatch"],
                        ["metadata", "Campaign metadata"],
                        ["royalty", "Royalty calculation"],
                        ["duplicate", "Potential duplicate charge"],
                        ["other", "Other concern"],
                      ].map(([value, label]) => (
                        <option value={value} key={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Supporting evidence reference (optional)">
                    <select
                      value={evidenceRef}
                      onChange={(e) => setEvidenceRef(e.target.value)}
                    >
                      <option value="">No specific reference selected</option>
                      {references.map((ref) => (
                        <option value={ref.id} key={ref.id}>
                          {ref.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Required review note">
                    <textarea
                      minLength={10}
                      maxLength={2000}
                      required
                      rows={4}
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                    />
                  </Field>
                  <p className="small muted">
                    Approval here is a usage-review decision. Identity
                    attestation and charge approval remain separate. A concern
                    is not a legal finding of infringement.
                  </p>
                  <BusyButton busy={busy}>Record artist decision</BusyButton>
                </form>
              ) : (
                <p className="alert info">
                  Artist decisions are read-only for the studio. Reply to an
                  open concern below, or correct supported campaign metadata on
                  the recording page.
                </p>
              )}
            </>
          )}
        </section>
        <section className="panel">
          <div className="section-heading">
            <h2>Review history</h2>
            <Field label="Case status">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              >
                <option value="OPEN">Open / stale</option>
                <option value="RESOLVED">Resolved</option>
                <option value="ALL">All decisions</option>
              </select>
            </Field>
          </div>
          {!visible.length && (
            <p className="muted">
              No cases match this view. Select a recording to record an artist
              decision.
            </p>
          )}
          {visible.map((row) => (
            <CaseThread key={row.id} row={row} />
          ))}
        </section>
      </div>
    </>
  );
}

function CaseThread({ row }: { row: ReviewCase }) {
  const { role, refresh, notify } = useWorkspace();
  const [note, setNote] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const request = useRef({ signature: "", key: "" });
  async function send(kind: string) {
    if (busy || note.trim().length < 10) return;
    const signature = JSON.stringify([kind, note]);
    if (request.current.signature !== signature)
      request.current = { signature, key: crypto.randomUUID() };
    setBusy(true);
    setError("");
    try {
      await post(`/review-cases/${row.id}/events`, {
        request_key: request.current.key,
        kind,
        note,
      });
      setNote("");
      refresh();
      notify(
        kind === "RESOLVE"
          ? "Concern resolved. Reevaluate compliance and renew charge approval before invoicing."
          : "Response recorded for artist review.",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save response.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="case-thread">
      <div className="section-heading">
        <strong>{row.decision.replaceAll("_", " ")}</strong>
        <Badge status={row.status} />
      </div>
      <Link
        className="text-link"
        href={`/dashboard/submissions/${row.asset_id}/passport`}
      >
        {row.campaign_name || "Open linked passport"} →
      </Link>
      <p>{row.note}</p>
      <p className="small muted">
        {row.category.replaceAll("_", " ")} · license v{row.license_version} ·{" "}
        {new Date(row.created_at).toLocaleString()}
      </p>
      {row.requires_reconciliation && (
        <p className="alert warning">
          New financial approvals are held. Existing charges and invoices remain
          unchanged and may require reconciliation.
        </p>
      )}
      <ol className="review-thread-events">
        {row.events.map((event) => (
          <li key={event.id}>
            <strong>
              {event.actor_name} · {event.kind.replaceAll("_", " ")}
            </strong>
            <p>{event.note}</p>
            <time dateTime={event.created_at}>
              {new Date(event.created_at).toLocaleString()}
            </time>
          </li>
        ))}
      </ol>
      {row.status !== "RESOLVED" && (
        <div>
          <Field label={`Response note for ${row.id.slice(0, 8)}`}>
            <textarea
              minLength={10}
              maxLength={2000}
              rows={3}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </Field>
          {error && <ErrorPanel message={error} />}
          <div className="passport-actions">
            <button
              type="button"
              className="button secondary"
              disabled={busy || note.trim().length < 10}
              onClick={() => send("RESPONSE")}
            >
              Record response
            </button>
            {role === "artist" && (
              <button
                type="button"
                className="button"
                disabled={busy || note.trim().length < 10}
                onClick={() => send("RESOLVE")}
              >
                Resolve concern
              </button>
            )}
          </div>
        </div>
      )}
    </article>
  );
}
