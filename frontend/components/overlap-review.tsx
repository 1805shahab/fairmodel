"use client";
import { useState } from "react";
import Link from "next/link";
import { BusyButton, ErrorPanel, Field, useAction, useData } from "./ui";
import { useWorkspace } from "./workspace";
import { date, endpoint, post } from "./api";
import type { ComparedAsset, OverlapDetail, OverlapPair } from "./types";

export default function OverlapReview({ assetId }: { assetId: string }) {
  const { data, error, loading, retry } = useData<OverlapDetail>(
    `/assets/${assetId}/overlap`,
  );
  if (error) return <ErrorPanel message={error} retry={retry} />;
  if (loading)
    return (
      <div className="alert info" role="status">
        Loading related usage evidence…
      </div>
    );
  if (!data?.pairs.length && !data?.incoming.length) return null;
  return (
    <section className="panel compact-panel" id="overlap-review">
      <h2>Related recordings & overlap review</h2>
      <p>
        Transcript similarity is evidence of possible reuse, not proof that
        recordings are identical. Exact decoded-sample hashing is identified
        only when it actually matched; no robust acoustic fingerprinting or
        speaker identification is claimed.
      </p>
      {data.usage?.reconciliation_required && (
        <div className="alert warning">
          Historical allocations conflict with this relationship, or the
          canonical recording does not cover a longer edit. Charges and invoices
          remain unchanged. Financial reconciliation is required before further
          approval.
        </div>
      )}
      {data.usage && (
        <p className="small">
          Canonical licensed usage:{" "}
          <Link
            className="text-link"
            href={`/dashboard/submissions/${data.usage.canonical_asset_id}`}
          >
            {data.usage.canonical_asset_id}
          </Link>
        </p>
      )}
      {data.pairs.map((pair) => (
        <PairReview
          key={`${pair.current.id}-${pair.related.id}-${pair.review?.id || "new"}-${pair.review?.state}`}
          pair={pair}
        />
      ))}
      {data.incoming.map((link) => (
        <p key={link.asset_id}>
          <Link
            className="text-link"
            href={`/dashboard/submissions/${link.asset_id}`}
          >
            Open related edited submission
          </Link>{" "}
          · {link.decision.replaceAll("_", " ").toLowerCase()} · {link.state}
        </p>
      ))}
    </section>
  );
}

function RecordingComparison({
  asset,
  excerpt,
}: {
  asset: ComparedAsset;
  excerpt?: string;
}) {
  return (
    <article className="panel compact-panel">
      <h3>{asset.name}</h3>
      <p className="small">Asset {asset.id}</p>
      <p>Campaign: {asset.campaign_name}</p>
      <p className="small">
        License{" "}
        <Link
          className="text-link"
          href={`/dashboard/licenses/${asset.license_id}`}
        >
          {asset.license_id}
        </Link>{" "}
        · version {asset.license_version}
      </p>
      <p>
        {asset.duration_seconds ?? "Unknown"}s recording ·{" "}
        {asset.spoken_seconds ?? "Unknown"}s estimated speech
      </p>
      <audio
        controls
        preload="none"
        src={endpoint(`/assets/${asset.id}/audio`)}
        aria-label={`Play ${asset.name}`}
      />
      {excerpt ? (
        <blockquote>{excerpt}</blockquote>
      ) : (
        <p className="small">
          No matched transcript passage available for this evidence type.
        </p>
      )}
      <Link className="text-link" href={`/dashboard/submissions/${asset.id}`}>
        Open recording & analysis
      </Link>
      {(asset.royalty_status || asset.invoice_status) && (
        <p className="small">
          Royalty: {asset.royalty_status || "not allocated"} · invoice:{" "}
          {asset.invoice_status || "not created"}
        </p>
      )}
    </article>
  );
}

function PairReview({ pair }: { pair: OverlapPair }) {
  const { role } = useWorkspace();
  const [decision, setDecision] = useState(
    pair.review?.state === "current" ? pair.review.decision : "",
  );
  const [note, setNote] = useState("");
  const { busy, error, run } = useAction();
  return (
    <div className="overlap-pair">
      <div className="alert info">
        Evidence: {pair.evidence.basis}
        {pair.evidence.matched_words
          ? ` · ${pair.evidence.matched_words} contiguous shared words`
          : ""}
        .
      </div>
      <div className="review-grid">
        <RecordingComparison
          asset={pair.current}
          excerpt={pair.evidence.current_excerpt}
        />
        <RecordingComparison
          asset={pair.related}
          excerpt={pair.evidence.related_excerpt}
        />
      </div>
      {pair.review && (
        <div
          className={`alert ${pair.review.state === "current" && pair.review.decision !== "UNCERTAIN" ? "info" : "warning"}`}
        >
          <strong>
            Recorded decision:{" "}
            {pair.review.decision.replaceAll("_", " ").toLowerCase()} ·{" "}
            {pair.review.state}
          </strong>
          <p>{pair.review.note}</p>
          <p className="small">
            Artist {pair.review.reviewer_id} · {date(pair.review.created_at)} ·
            license version {pair.review.license_version}
          </p>
        </div>
      )}
      <div className="overlap-implications">
        <h3>How this affects royalties</h3>
        <p>
          Same usage links this edit to one canonical allocation. Separate usage
          applies the approved billing rules independently. Uncertain keeps new
          approvals on hold. Existing charges and invoices are preserved;
          conflicts require reconciliation.
        </p>
      </div>
      {role === "artist" ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void run(async () => {
              await post(`/assets/${pair.current.id}/overlap`, {
                related_asset_id: pair.related.id,
                decision,
                note,
                expected_review_id: pair.review?.id || null,
              });
            }, "Overlap decision saved. Existing content evidence was reused for workflow checks when current; otherwise run compliance evaluation.");
          }}
        >
          <Field label="Overlap review decision">
            <select
              required
              value={decision}
              onChange={(event) => setDecision(event.target.value)}
              disabled={busy}
            >
              <option value="">Select a determination</option>
              <option value="SAME_USAGE">
                Same licensed usage / edited version
              </option>
              <option value="SEPARATE_USAGE">
                Separate independently licensed usage
              </option>
              <option value="UNCERTAIN">Uncertain / keep on hold</option>
            </select>
          </Field>
          <Field
            label="Overlap review note"
            hint="Explain the evidence and intended licensed usage. At least 10 characters."
          >
            <textarea
              required
              minLength={10}
              maxLength={2000}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              disabled={busy}
            />
          </Field>
          <p className="small">
            Same usage receives no separate allocation. Separate usage follows
            the approved per-asset/cumulative rules. Uncertain usage stays held.
            Conflicting historical charges require reconciliation; none are
            deleted.
          </p>
          {error && <ErrorPanel message={error} />}
          <BusyButton busy={busy} disabled={!decision}>
            Save overlap decision
          </BusyButton>
        </form>
      ) : (
        <p className="small">
          Only the artist may resolve or change the overlap decision. Studio
          users can inspect both recordings and the recorded decision.
        </p>
      )}
      {pair.history.length > 0 && (
        <details className="speech-details">
          <summary>Overlap decision history ({pair.history.length})</summary>
          {pair.history.map((review) => (
            <article className="finding" key={review.id}>
              <strong>{review.decision.replaceAll("_", " ")}</strong>
              <p>{review.note}</p>
              <p className="small">
                {date(review.created_at)} · reviewer {review.reviewer_id} ·
                version {review.license_version} · review {review.id}
              </p>
            </article>
          ))}
        </details>
      )}
    </div>
  );
}
