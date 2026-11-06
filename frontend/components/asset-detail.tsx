"use client";
import { useState } from "react";
import Link from "next/link";
import {
  AudioLines,
  Check,
  ClipboardCheck,
  Clock3,
  FileText,
  Sparkles,
} from "lucide-react";
import {
  Badge,
  BusyButton,
  ErrorPanel,
  Loading,
  PageHeading,
  useAction,
  useData,
} from "./ui";
import { useWorkspace } from "./workspace";
import { api, endpoint, money, post } from "./api";
import CampaignForm from "./campaign-form";
import type { Asset, Campaign } from "./types";

export default function AssetDetail({ id }: { id: string }) {
  const { data, error, loading, retry } = useData<Asset>(`/assets/${id}`);
  return loading ? (
    <Loading />
  ) : error ? (
    <ErrorPanel message={error} retry={retry} />
  ) : data ? (
    <Analysis asset={data} />
  ) : null;
}
function Analysis({ asset }: { asset: Asset }) {
  const { role } = useWorkspace();
  const [demo, setDemo] = useState(
    Boolean(asset.analysis?.result.demo_fixture),
  );
  const { busy, error, run } = useAction();
  const result = asset.analysis?.result,
    report = asset.report?.result;
  return (
    <>
      <PageHeading
        eyebrow={`AUDIO ASSET · LICENSE VERSION ${asset.license_version}`}
        title={asset.campaign.name}
        description={asset.original_name}
        action={<Badge status={asset.status} />}
      />
      <div className="detail-toolbar">
        <Link
          className="text-link"
          href={`/dashboard/licenses/${asset.license_id}`}
        >
          <FileText size={15} />
          View associated license
        </Link>
        <span className="small">Single licensed speaker per asset</span>
      </div>
      {asset.error && <ErrorPanel message={asset.error} />}
      <section className="panel audio-panel">
        <div className="audio-header">
          <span className="file-icon">
            <AudioLines size={26} />
          </span>
          <div>
            <h2>Listen to the submitted asset</h2>
            <p>{asset.original_name}</p>
          </div>
          {result && (
            <span className="pill blue">
              {result.format.split(",")[0].toUpperCase()} ·{" "}
              {result.sample_rate.toLocaleString()} Hz
            </span>
          )}
        </div>
        <audio
          controls
          preload="metadata"
          src={endpoint(`/assets/${asset.id}/audio`)}
        >
          Your browser does not support audio playback.
        </audio>
      </section>
      {!report && (
        <section className="panel extraction-bar">
          <div>
            <h2>
              {!result
                ? "Process the recording"
                : "Evaluate licensing compliance"}
            </h2>
            <p>
              {!result
                ? "Decode audio, measure speech activity, and transcribe with Groq."
                : "Review content against approved terms using Gemini and deterministic rules."}
            </p>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={demo}
                onChange={(e) => setDemo(e.target.checked)}
              />
              Explicit local fixture mode — not a live AI result
            </label>
          </div>
          {!result ? (
            role === "studio" ? (
              <BusyButton
                busy={busy}
                onClick={() =>
                  void run(async () => {
                    await post(`/assets/${asset.id}/analyze`, {
                      use_demo_fixture: demo,
                    });
                  }, "Audio analysis completed.")
                }
              >
                <Sparkles size={16} />
                Analyze audio
              </BusyButton>
            ) : (
              <span className="small">The studio runs audio analysis.</span>
            )
          ) : (
            <BusyButton
              busy={busy}
              onClick={() =>
                void run(async () => {
                  await post(`/assets/${asset.id}/evaluate`, {
                    use_demo_fixture: demo,
                  });
                }, "Compliance report is ready.")
              }
            >
              <ClipboardCheck size={16} />
              Evaluate compliance
            </BusyButton>
          )}
        </section>
      )}
      {error && <ErrorPanel message={error} />}
      {busy && (
        <div className="alert info" role="status">
          Processing may take up to 90 seconds. The result will appear here when
          the request finishes.
        </div>
      )}
      {result && (
        <>
          <div className="measurement-grid">
            <article className="stat-card">
              <div className="stat-top">
                Total recording <Clock3 size={17} />
              </div>
              <strong>
                {Number(result.duration_seconds).toFixed(2)}
                <small> sec</small>
              </strong>
              <span className="stat-note">Measured by ffprobe</span>
            </article>
            <article className="stat-card">
              <div className="stat-top">
                Estimated speech <AudioLines size={17} />
              </div>
              <strong>
                {result.spoken_seconds === null
                  ? "Unknown"
                  : Number(result.spoken_seconds).toFixed(2)}
                <small> sec</small>
              </strong>
              <span className="stat-note">{result.vad}</span>
            </article>
            <article className="stat-card">
              <div className="stat-top">
                Transcription source <Sparkles size={17} />
              </div>
              <strong className="provider-value">
                {result.provider.startsWith("demo")
                  ? "Demo fixture"
                  : "Groq Whisper"}
              </strong>
              <span className="stat-note">{result.provider}</span>
            </article>
          </div>
          <div className="alert info">{result.measurement_note}</div>
          <div className="review-grid">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Transcript & timestamps</h2>
                  <p>
                    {result.demo_fixture
                      ? "Explicit local fixture transcript. Groq has not run."
                      : "Provider transcript. Review for recognition errors."}
                  </p>
                </div>
              </div>
              <div className="transcript">
                {result.timestamps.length ? (
                  result.timestamps.map((x, i) => (
                    <p key={i}>
                      <span className="timestamp">
                        {x.start.toFixed(1)}s — {x.end.toFixed(1)}s
                      </span>
                      {x.text}
                    </p>
                  ))
                ) : (
                  <p>{result.transcript || "No transcript returned."}</p>
                )}
              </div>
              <details className="speech-details">
                <summary>
                  Speech activity segments ({result.speech_segments.length})
                </summary>
                <div className="segment-list">
                  {result.speech_segments.map((x, i) => (
                    <span key={i}>
                      {x.start.toFixed(2)}–{x.end.toFixed(2)}s
                    </span>
                  ))}
                </div>
              </details>
            </section>
            <aside className="panel compact-panel">
              <h2>Voice verification</h2>
              <Badge status={result.speaker.status.toUpperCase()} />
              <p>{result.speaker.note}</p>
              <p className="small">
                Similarity is not proof of cloning, authorization, or legal
                infringement. No score is displayed unless the model actually
                runs.
              </p>
            </aside>
          </div>
        </>
      )}
      {report && (
        <section className="panel report-panel">
          <div className="panel-heading">
            <div>
              <h2>Compliance report</h2>
              <p>
                Contract rules + measured speech + transcript findings +
                declared metadata
              </p>
            </div>
            <Badge status={report.status} />
          </div>
          <div className="report-body">
            {report.reasons.length ? (
              <ul className="findings-list">
                {report.reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            ) : (
              <div className="alert success">
                <Check size={17} />
                No conflicts found in the evaluated evidence.
              </div>
            )}
            {report.findings.findings.map((finding, i) => (
              <article className="finding" key={i}>
                <strong>{finding.category}</strong>
                <blockquote>“{finding.passage}”</blockquote>
                <p>{finding.explanation}</p>
              </article>
            ))}
            {report.calculation && (
              <div className="calculation">
                <div>
                  <span className="eyebrow">
                    DETERMINISTIC ROYALTY CALCULATION
                  </span>
                  <h3>
                    {money(
                      report.calculation.amount,
                      report.calculation.currency,
                    )}
                  </h3>
                </div>
                <code>{report.calculation.explanation}</code>
                <div className="calculation-details">
                  <span>
                    Basis: {report.calculation.billing_basis.replace("_", " ")}
                  </span>
                  <span>
                    Prior allocated speech: {report.calculation.prior_seconds}s
                  </span>
                  <span>{report.calculation.rounding}</span>
                </div>
                <p className="small">
                  {["NEEDS_REVIEW", "RESTRICTED_USAGE"].includes(report.status)
                    ? "Illustrative calculation only. No royalty or invoice was created."
                    : "A positive amount requires artist approval before a simulated invoice can be created."}
                </p>
              </div>
            )}
            <p className="small">Assessment source: {report.provider}</p>
            <details className="speech-details">
              <summary>Supporting approved contract clauses</summary>
              <div className="evidence-list">
                {report.source_pages.map((evidence, index) => (
                  <article key={index}>
                    <span className="eyebrow">
                      {evidence.field.replaceAll("_", " ")}
                    </span>
                    <blockquote>“{evidence.quote}”</blockquote>
                    <a
                      className="text-link"
                      href={`${endpoint(`/licenses/${asset.license_id}/contract`)}#page=${evidence.page}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open source page {evidence.page} ↗
                    </a>
                  </article>
                ))}
              </div>
            </details>
            <p className="small">
              {report.metadata_note} {report.legal_note}
            </p>
            {asset.royalty && (
              <Link className="button secondary" href="/dashboard/royalties">
                Review royalty entry →
              </Link>
            )}
          </div>
        </section>
      )}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Declared campaign metadata</h2>
            <p>
              Provided by the studio. These fields do not prove publication or
              geographic distribution.
            </p>
          </div>
        </div>
        <div className="metadata-grid">
          {Object.entries(asset.campaign).map(([key, value]) => (
            <div key={key}>
              <span>{key.replaceAll("_", " ")}</span>
              <strong>{value || "Not supplied"}</strong>
            </div>
          ))}
        </div>
        {role === "studio" && !asset.royalty && (
          <details className="edit-campaign">
            <summary>Correct metadata and reevaluate</summary>
            <CampaignEditor
              key={JSON.stringify(asset.campaign)}
              asset={asset}
            />
          </details>
        )}
      </section>
    </>
  );
}
function CampaignEditor({ asset }: { asset: Asset }) {
  const [campaign, setCampaign] = useState<Campaign>(asset.campaign);
  const { busy, error, run } = useAction();
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void run(async () => {
          await api(`/assets/${asset.id}/campaign`, {
            method: "PATCH",
            body: JSON.stringify(campaign),
          });
        }, "Metadata saved. Evaluate again to create an updated report.");
      }}
    >
      <CampaignForm value={campaign} onChange={setCampaign} />
      {error && <ErrorPanel message={error} />}
      <BusyButton busy={busy}>Save corrected metadata</BusyButton>
    </form>
  );
}
