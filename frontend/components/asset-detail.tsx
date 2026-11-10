"use client";
import { useRef, useState, useCallback } from "react";
import Link from "next/link";
import {
  AudioLines,
  Check,
  ClipboardCheck,
  FileText,
  Sparkles,
} from "lucide-react";
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
import { useWorkspace } from "./workspace";
import { api, money, post } from "./api";
import CampaignForm from "./campaign-form";
import { Metric, Tabs, TabPanel } from "./product-ui";
import SourceCitations from "./source-citations";
import RecordingPlayer from "./recording-player";
import OverlapReview from "./overlap-review";
import { PaymentModeNotice } from "./invoice-actions";
import type { Asset, Campaign } from "./types";

export default function AssetDetail({ id }: { id: string }) {
  const { data, error, loading, retry } = useData<Asset>(`/assets/${id}`);
  const [tab, setTab] = useState("overview");
  return loading ? (
    <Loading />
  ) : error ? (
    <ErrorPanel message={error} retry={retry} />
  ) : data ? (
    <Analysis asset={data} tab={tab} setTab={setTab} />
  ) : null;
}
function Analysis({
  asset,
  tab,
  setTab,
}: {
  asset: Asset;
  tab: string;
  setTab: (value: string) => void;
}) {
  const { role } = useWorkspace();
  const result = asset.analysis?.result,
    report = asset.report?.result;
  const player = useRef<HTMLAudioElement>(null);
  const connectPlayer = useCallback((node: HTMLAudioElement | null) => {
    player.current = node;
  }, []);
  const [activeSegment, setActiveSegment] = useState(-1);
  const calculation = asset.royalty?.calculation || report?.calculation;
  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "transcript", label: "Transcript" },
    { id: "compliance", label: "Compliance" },
    { id: "identity", label: "Identity & authorization" },
    { id: "overlap", label: "Overlap review" },
    { id: "royalties", label: "Royalties" },
    { id: "evidence", label: "Contract evidence" },
  ];
  function openPanel(value: string) {
    setTab(value);
    requestAnimationFrame(() =>
      document.getElementById(`recording-tab-${value}`)?.focus(),
    );
  }
  const reviewTab = !result
    ? "overview"
    : !report
      ? "overview"
      : report.status === "RESTRICTED_USAGE"
        ? "compliance"
        : report.billing_usage?.unresolved.length ||
            report.billing_usage?.reconciliation_required
          ? "overlap"
          : asset.authorization_state !== "artist_confirmed"
            ? "identity"
            : report.eligible_for_charge
              ? "royalties"
              : "compliance";
  return (
    <>
      <PageHeading
        eyebrow={`RECORDING · LICENSE VERSION ${asset.license_version}`}
        title={asset.campaign.name}
        description={asset.original_name}
        action={
          <Link
            className="button secondary"
            href={`/dashboard/licenses/${asset.license_id}`}
          >
            <FileText size={15} />
            View license
          </Link>
        }
      />
      {asset.error && <ErrorPanel message={asset.error} />}
      <div
        className="workflow-strip"
        aria-label="Independent submission states"
      >
        <div>
          <span>Audio processing</span>
          <Badge
            status={
              asset.processing_state || (result ? "ANALYZED" : "UPLOADED")
            }
          />
        </div>
        <div>
          <span>License compliance</span>
          <Badge
            status={asset.compliance_state || report?.status || "PENDING"}
          />
        </div>
        <div>
          <span>Artist attestation</span>
          <Badge
            status={
              asset.authorization_state ||
              asset.authorization?.status ||
              "unresolved"
            }
          />
        </div>
        <div>
          <span>Payment state</span>
          <Badge status={asset.invoice_state || "NOT_CREATED"} />
        </div>
      </div>
      {asset.next_action && (
        <div
          className={`alert ${report?.status === "RESTRICTED_USAGE" ? "error" : report?.eligible_for_charge ? "info" : "warning"} next-action`}
        >
          <div>
            <strong>Next action</strong>
            <p>{asset.next_action}</p>
          </div>
          <button
            className="button secondary"
            onClick={() => openPanel(reviewTab)}
          >
            Open relevant review
          </button>
        </div>
      )}
      {result?.measurement_uncertain && (
        <div className="alert warning">
          <strong>Speech measurement needs review</strong>
          <p>{result.measurement_note}</p>
        </div>
      )}
      <section
        className="panel audio-panel speech-workbench"
        id="recording-player"
      >
        <div className="audio-header">
          <span className="file-icon">
            <AudioLines size={23} />
          </span>
          <div>
            <h2>Listen to the submitted asset</h2>
            <p>
              {result
                ? `${result.format.split(",")[0].toUpperCase()} · ${result.sample_rate.toLocaleString()} Hz`
                : asset.original_name}
            </p>
          </div>
        </div>
        <RecordingPlayer
          id={asset.id}
          result={result}
          onPlayer={connectPlayer}
          onSegment={setActiveSegment}
        />
      </section>
      <div className="audio-summary">
        <Metric
          label="Total recording"
          value={
            result
              ? `${Number(result.duration_seconds).toFixed(2)}s`
              : "Not measured"
          }
          note="FFprobe · total duration"
        />
        <Metric
          label="Estimated speech"
          value={
            result?.spoken_seconds != null
              ? `${Number(result.spoken_seconds).toFixed(2)}s`
              : "Unknown"
          }
          note={result?.vad || "Awaiting audio analysis"}
        />
        <Metric
          label="Included allowance"
          value={
            calculation ? `${calculation.included_seconds}s` : "Not evaluated"
          }
          note={
            calculation
              ? calculation.billing_basis.replaceAll("_", " ")
              : "Evaluate approved contract rules"
          }
        />
        <Metric
          label={
            asset.royalty ? "Recorded royalty" : "Additional royalty estimate"
          }
          value={
            calculation
              ? money(calculation.amount, calculation.currency)
              : "Not evaluated"
          }
          note={
            calculation
              ? Number(calculation.amount) === 0
                ? "Included usage · no payable invoice"
                : asset.royalty
                  ? "Requires current charge approval"
                  : "Eligibility unresolved · not a charge"
              : "Deterministic calculation only"
          }
        />
      </div>
      <p className="small recording-disclosure">
        Audio analyzed means processing succeeded; it does not establish
        compliance. Speaker identity has not been automatically verified. Manual
        artist attestation is separate.
      </p>
      <Tabs id="recording" items={tabs} value={tab} onChange={setTab} />
      <TabPanel group="recording" id="overview" active={tab}>
        <ProcessingControls asset={asset} />
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
      </TabPanel>
      <TabPanel group="recording" id="transcript" active={tab}>
        {result ? (
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
              <Badge status={result.demo_fixture ? "FIXTURE" : "ANALYZED"} />
            </div>
            <div className="transcript-provider">
              <strong>
                {result.demo_fixture
                  ? "Offline development fixture"
                  : result.provider.startsWith("groq:")
                    ? "Live Groq Whisper"
                    : "Unknown source"}
              </strong>
              <span>{result.provider}</span>
            </div>
            <div className="transcript">
              {result.timestamps.length ? (
                result.timestamps.map((x, i) => (
                  <p
                    key={i}
                    className={activeSegment === i ? "transcript-active" : ""}
                    aria-current={activeSegment === i ? "true" : undefined}
                  >
                    <button
                      className="timestamp"
                      aria-label={`Seek to ${x.start.toFixed(1)} seconds`}
                      onClick={() => {
                        if (player.current)
                          player.current.currentTime = x.start;
                      }}
                    >
                      {x.start.toFixed(1)}–{x.end.toFixed(1)}s
                    </button>
                    <span>{x.text}</span>
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
              <p className="small">{result.measurement_note}</p>
            </details>
          </section>
        ) : (
          <section className="panel compact-panel">
            <h2>Transcript pending</h2>
            <p>
              Run audio analysis from Overview to measure speech and obtain a
              transcript.
            </p>
          </section>
        )}
      </TabPanel>
      <TabPanel group="recording" id="compliance" active={tab}>
        <div className="detail-toolbar">
          <button
            className="button secondary"
            onClick={() => openPanel("overview")}
          >
            Open analysis controls
          </button>
          <span className="small">
            Live provider failures never switch to fixtures.
          </span>
        </div>
        {report && (
          <section className="panel report-panel" id="compliance-report">
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
              {report.primary_reason && (
                <p>
                  <strong>Primary conclusion: </strong>
                  {report.primary_reason}
                </p>
              )}

              {(report.policy_version || 0) < 4 && (
                <div className="alert warning">
                  Historical assessment: rerun compliance to apply the current
                  contract normalization, workflow and source-evidence checks.
                </div>
              )}
              <div
                className={`alert ${report.assessment_fixture || report.provider.startsWith("demo") ? "warning" : "info"}`}
              >
                <strong>
                  {report.provider.startsWith("gemini:")
                    ? "Live Gemini compliance assessment"
                    : report.provider.startsWith("demo")
                      ? "Offline fixture compliance — not a live AI result"
                      : "Assessment provenance unknown"}
                </strong>
                <p>
                  Assessment source: {report.provider}. Transcript source:{" "}
                  {result?.provider || "unknown"}.
                </p>
                <p>
                  Uses approved contract version {asset.license_version}. AI
                  findings are advisory; contract scope and money use
                  deterministic rules.
                </p>
                {report.assessment_fixture ||
                report.provider.startsWith("demo") ? (
                  <p>
                    Explicit offline fixture. No Gemini request was made for
                    this assessment.
                  </p>
                ) : report.provider_receipt?.succeeded_at ? (
                  <p>
                    Successful provider response recorded at{" "}
                    {new Date(
                      report.provider_receipt.succeeded_at,
                    ).toLocaleString()}
                    . Returned model:{" "}
                    {report.provider_receipt.returned_model ||
                      "not supplied by provider"}
                    .
                  </p>
                ) : (
                  <p>
                    Historical successful-response record. Provider response
                    identifiers were not retained; configuration alone is not
                    proof of a request.
                  </p>
                )}
              </div>
              {report.billing_usage?.disposition === "SAME_USAGE" &&
              !report.billing_usage.unresolved.length &&
              !report.billing_usage.reconciliation_required ? (
                <div className="alert info">
                  This edited version is linked to the canonical licensed usage
                  and receives no separate royalty allocation.
                </div>
              ) : (
                !report.eligible_for_charge && (
                  <div className="alert warning">
                    Charges are on hold. Resolve identity, authorization and
                    contractual eligibility, then reevaluate. No new royalty is
                    proposed while review is required.
                  </div>
                )
              )}
              {report.assessment_reused && (
                <p className="small">
                  Content assessment reused from its original recorded provider
                  response; current workflow and financial checks were
                  recomputed. No fresh AI call is claimed.
                </p>
              )}
              {report.reasons.length ? (
                <ul className="findings-list">
                  {Array.from(new Set(report.reasons)).map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              ) : (
                <div className="alert success">
                  <Check size={17} />
                  No conflicts found in the evaluated evidence.
                </div>
              )}
              <div className="condition-columns">
                <section>
                  <h3>Satisfied conditions</h3>
                  <ul>
                    {report.satisfied_conditions?.length ? (
                      report.satisfied_conditions.map((r, i) => (
                        <li key={i}>{r.explanation}</li>
                      ))
                    ) : (
                      <li>No satisfied conditions recorded.</li>
                    )}
                  </ul>
                </section>
                <section>
                  <h3>Substantiated restrictions</h3>
                  <ul>
                    {report.substantiated_violations?.length ? (
                      report.substantiated_violations.map((r, i) => (
                        <li key={i}>{r.explanation}</li>
                      ))
                    ) : (
                      <li>No substantiated violation recorded.</li>
                    )}
                  </ul>
                </section>
                <section>
                  <h3>Needs review</h3>
                  <ul>
                    {report.unresolved_conditions?.length ? (
                      report.unresolved_conditions.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))
                    ) : (
                      <li>
                        {report.unresolved_conditions
                          ? "No unresolved conditions recorded."
                          : "No structured unresolved list recorded. Check the conclusion and rule evidence."}
                      </li>
                    )}
                  </ul>
                </section>
              </div>
              <h3 className="report-section-title">AI content observations</h3>
              <p className="small">
                Advisory transcript interpretation, separate from deterministic
                scope and workflow checks.
              </p>
              {!report.findings.findings.length && (
                <p className="small">No advisory content findings recorded.</p>
              )}
              {report.findings.uncertainty.length > 0 && (
                <div className="alert warning">
                  <strong>AI uncertainty</strong>
                  <ul>
                    {report.findings.uncertainty.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {report.rule_checks?.some((r) => r.kind === "administrative") && (
                <details className="speech-details">
                  <summary>Administrative workflow conditions</summary>
                  <div className="evidence-list">
                    {report.rule_checks
                      .filter((r) => r.kind === "administrative")
                      .map((r, i) => (
                        <article key={i}>
                          <strong>{r.outcome.replaceAll("_", " ")}</strong>
                          <p>{r.explanation}</p>
                        </article>
                      ))}
                  </div>
                </details>
              )}
              {report.findings.findings.map((finding, i) => (
                <article className="finding" key={i}>
                  <strong>{finding.category}</strong>
                  {finding.passage?.trim() && (
                    <blockquote>{finding.passage}</blockquote>
                  )}
                  <p>{finding.explanation}</p>
                </article>
              ))}
              {report.rule_checks?.some(
                (rule) => rule.kind !== "administrative",
              ) ? (
                <details className="speech-details">
                  <summary>Deterministic rules and workflow evidence</summary>
                  <div className="evidence-list">
                    {report.rule_checks
                      .filter((rule) => rule.kind !== "administrative")
                      .map((rule, index) => (
                        <article key={index}>
                          <strong>
                            {rule.rule.replaceAll("_", " ")} ·{" "}
                            {rule.outcome.replaceAll("_", " ")}
                          </strong>
                          {rule.kind && (
                            <p className="small">
                              Condition type: {rule.kind.replaceAll("_", " ")}
                            </p>
                          )}
                          <p>{rule.explanation}</p>
                        </article>
                      ))}
                  </div>
                </details>
              ) : null}
              {report.overlap?.length ? (
                <div
                  className={`alert ${report.billing_usage?.unresolved.length || report.billing_usage?.reconciliation_required ? "warning" : "info"}`}
                >
                  <strong>
                    Overlap review{" "}
                    {report.billing_usage?.unresolved.length ||
                    report.billing_usage?.reconciliation_required
                      ? "required"
                      : "resolved"}
                  </strong>
                  <p>
                    Review the recorded determination and related recordings in
                    the Overlap review tab. Resolved relationships remain
                    recorded and do not create a repeated hold without changed
                    evidence.
                  </p>
                  {report.overlap.map((item) => (
                    <p key={item.asset_id}>
                      <Link
                        className="text-link"
                        href={`/dashboard/submissions/${item.asset_id}`}
                      >
                        Review related asset
                      </Link>{" "}
                      · {item.basis}
                    </p>
                  ))}
                </div>
              ) : null}
              {report.source_review?.missing_fields.length ? (
                <div className="alert warning">
                  Missing source provenance:{" "}
                  {report.source_review.missing_fields.join(", ")}. Review is
                  required.
                </div>
              ) : null}
              <p className="small">Assessment source: {report.provider}</p>
              <details className="speech-details">
                <summary>Supporting approved contract clauses</summary>
                <SourceCitations
                  items={report.source_pages}
                  licenseId={asset.license_id}
                />
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

        {!report && (
          <section className="panel compact-panel">
            <h2>Compliance pending</h2>
            <p>
              Analyze the audio, then evaluate compliance from Overview. No
              licensing decision has been recorded.
            </p>
          </section>
        )}
      </TabPanel>
      <TabPanel group="recording" id="identity" active={tab}>
        {result && (
          <section className="panel compact-panel">
            <h2>Voice verification</h2>
            <p>
              <strong>Identity not automatically verified</strong>
            </p>
            <Badge status={result.speaker.status.toUpperCase()} />
            <p>{result.speaker.note}</p>
            <p className="small">
              Similarity is not proof of cloning, authorization or infringement.
              No score is displayed unless the model actually runs.
            </p>
          </section>
        )}
        {result ? (
          <UsageReview asset={asset} />
        ) : (
          <p className="alert info">
            Analyze the recording before artist review.
          </p>
        )}
      </TabPanel>
      <TabPanel group="recording" id="overlap" active={tab}>
        {result ? (
          <>
            <OverlapReview assetId={asset.id} />
            <p className="small">
              Only recorded overlap evidence appears above. Transcript
              similarity is possible reuse evidence, not proof of identical
              audio or infringement.
            </p>
          </>
        ) : (
          <p className="alert info">
            Related usage is checked after audio analysis.
          </p>
        )}
      </TabPanel>
      <TabPanel group="recording" id="royalties" active={tab}>
        {result && <AssetFinance asset={asset} />}
        {report && (
          <section className="panel compact-panel">
            <h2>Calculation evidence</h2>
            {report.calculation && (
              <div className="calculation">
                <div>
                  <span className="eyebrow">
                    {report.billing_usage?.disposition === "SAME_USAGE"
                      ? "EDIT MEASUREMENT ESTIMATE — NO SEPARATE ALLOCATION"
                      : "DETERMINISTIC ROYALTY CALCULATION"}
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
                  {report.billing_usage?.disposition === "SAME_USAGE"
                    ? "This formula describes only the edit's measured duration. No new charge is allocated; use the canonical recording for billing."
                    : ["NEEDS_REVIEW", "RESTRICTED_USAGE"].includes(
                          report.status,
                        )
                      ? "Estimate only. No new royalty is proposed by this assessment. Historical entries remain visible but require current eligibility before approval."
                      : "A positive amount requires artist approval before an invoice can be created."}
                </p>
              </div>
            )}

            {!report.calculation && (
              <p>
                No eligible calculation is available. Resolve the outstanding
                licensing review first.
              </p>
            )}
          </section>
        )}
        {!report && (
          <p className="alert info">
            Evaluate licensing eligibility before proposing a royalty.
          </p>
        )}
      </TabPanel>
      <TabPanel group="recording" id="evidence" active={tab}>
        <section className="panel compact-panel">
          <h2>Approved contract evidence</h2>
          <p>
            Source clauses used by this assessment, bound to approved license
            version {asset.license_version}. Missing provenance remains a review
            requirement.
          </p>
          {report ? (
            <SourceCitations
              items={report.source_pages}
              licenseId={asset.license_id}
            />
          ) : (
            <p className="small">
              No assessed source evidence yet. Open the associated license to
              inspect its PDF and terms.
            </p>
          )}
        </section>
      </TabPanel>
    </>
  );
}
function ProcessingControls({ asset }: { asset: Asset }) {
  const { role } = useWorkspace();
  const [audioMode, setAudioMode] = useState("live");
  const [complianceMode, setComplianceMode] = useState("live");
  const { busy, error, run } = useAction();
  const result = asset.analysis?.result;
  return (
    <section className="panel compact-panel">
      <h2>Analysis providers</h2>
      <p>
        Live services are selected by default. Each saved result records the
        provider that actually ran. Failed requests display an error and never
        switch to fixtures.
      </p>
      {role === "studio" && !asset.royalty && (
        <div className="extraction-bar">
          <Field label="Transcription provider">
            <select
              value={audioMode}
              onChange={(e) => setAudioMode(e.target.value)}
              disabled={busy}
            >
              <option value="live">Live Groq Whisper</option>
              <option value="fixture">Offline development fixture</option>
            </select>
          </Field>
          <BusyButton
            busy={busy}
            onClick={() =>
              void run(async () => {
                await post(`/assets/${asset.id}/analyze`, {
                  use_demo_fixture: audioMode === "fixture",
                  reprocess: Boolean(result),
                });
              }, "Audio processing completed. Compliance and identity require separate review.")
            }
          >
            <Sparkles size={16} />
            {result ? "Rerun audio analysis" : "Analyze audio"}
          </BusyButton>
        </div>
      )}
      {result && (
        <div className="extraction-bar">
          <Field label="Compliance provider">
            <select
              value={complianceMode}
              onChange={(e) => setComplianceMode(e.target.value)}
              disabled={busy}
            >
              <option value="live">Live Gemini</option>
              <option value="fixture">Offline development fixture</option>
            </select>
          </Field>
          <BusyButton
            busy={busy}
            onClick={() =>
              void run(async () => {
                await post(`/assets/${asset.id}/evaluate`, {
                  use_demo_fixture: complianceMode === "fixture",
                  reprocess: true,
                });
              }, "Compliance assessment saved with provider provenance.")
            }
          >
            <ClipboardCheck size={16} />
            Evaluate compliance
          </BusyButton>
        </div>
      )}
      {asset.report?.result.content_input_hash && (
        <div className="extraction-bar">
          <p className="small">
            Refresh workflow eligibility using the saved, labeled content
            assessment. The provider controls above explicitly request fresh AI
            analysis.
          </p>
          <BusyButton
            busy={busy}
            disabled={asset.report.result.latest_attempt_failed}
            className="button secondary"
            onClick={() =>
              void run(async () => {
                await post(`/assets/${asset.id}/evaluate`, {
                  use_demo_fixture: asset.report!.result.assessment_fixture,
                  reprocess: false,
                });
              }, "Workflow checks updated using the recorded content evidence.")
            }
          >
            Update workflow checks
          </BusyButton>
        </div>
      )}
      {audioMode === "fixture" || complianceMode === "fixture" ? (
        <div className="alert warning">
          Offline fixture selected — not a live AI result. Development/test
          only; bundled matching files are required. Other provider selections
          remain independent.
        </div>
      ) : null}
      {result?.demo_fixture && (
        <p className="small">
          The saved transcript is an offline fixture. Select live transcription
          to obtain a live Groq result. Live Gemini can assess fixture text, but
          that does not make the transcript live evidence.
        </p>
      )}
      {!result && role !== "studio" && (
        <p>The studio must run audio analysis first.</p>
      )}
      {error && <ErrorPanel message={error} />}
      {busy && (
        <div className="alert info" role="status">
          Processing may take up to 90 seconds. Please wait for the provider
          response.
        </div>
      )}
    </section>
  );
}
function UsageReview({ asset }: { asset: Asset }) {
  const { role } = useWorkspace();
  const [identity, setIdentity] = useState(
    asset.authorization?.status === "artist_confirmed" &&
      asset.authorization.identity_confirmed,
  );
  const [authorized, setAuthorized] = useState(
    asset.authorization?.status === "artist_confirmed" &&
      asset.authorization.use_authorized,
  );
  const [note, setNote] = useState(asset.authorization?.note || "");
  const { busy, error, run } = useAction();
  const confirmed = asset.authorization?.status === "artist_confirmed";
  return (
    <section className="panel compact-panel" id="artist-review">
      <h2>Artist identity & usage review</h2>
      <div className="review-context">
        <strong>{asset.original_name}</strong>
        <span>
          {asset.campaign.name} · License version {asset.license_version}
        </span>
        <span>
          Review binds the current file, transcript and declared campaign.
        </span>
      </div>
      <p>
        {confirmed
          ? "Artist confirmation recorded for this exact asset, campaign, transcript and approved contract version."
          : "Identity and usage authorization remain unresolved until the artist reviews the evidence. No charge can be proposed before confirmation."}
      </p>
      <p className="small">
        Manual artist attestation is separate from optional speaker similarity.
        It is not biometric or legal proof. Changes to campaign metadata or
        transcription require a fresh review.
      </p>
      {asset.analysis?.result.demo_fixture && (
        <div className="alert warning">
          Fixture exercise only: these confirmations simulate the artist review
          for the bundled synthetic sample. They do not verify a real
          artist&apos;s voice or authorize real use.
        </div>
      )}
      {asset.authorization && (
        <p className="small">
          Review note: {asset.authorization.note}
          <br />
          Recorded by {asset.authorization.artist_id} ·{" "}
          {new Date(asset.authorization.updated_at).toLocaleString()} · state:{" "}
          {asset.authorization.status}
        </p>
      )}
      {role === "artist" ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              await post(`/assets/${asset.id}/authorization`, {
                identity_confirmed: identity,
                use_authorized: authorized,
                note,
              });
            }, "Artist review saved. Reevaluate compliance before proposing a charge.");
          }}
        >
          <label className="checkbox">
            <input
              type="checkbox"
              checked={identity}
              onChange={(e) => setIdentity(e.target.checked)}
            />
            I confirm the licensed speaker identity for this asset
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={authorized}
              onChange={(e) => setAuthorized(e.target.checked)}
            />
            I authorize this asset and its declared campaign
          </label>
          <Field
            label="Identity and authorization review note"
            hint="Record the evidence reviewed; at least 10 characters."
          >
            <textarea
              required
              minLength={10}
              maxLength={2000}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </Field>
          <p className="small">
            Saving unchecked confirmations records unresolved status and holds
            any existing proposal for review.
          </p>
          {error && <ErrorPanel message={error} />}
          <BusyButton busy={busy}>Save artist usage review</BusyButton>
        </form>
      ) : (
        <p>
          Switch to the artist demo persona to review identity and
          authorization.
        </p>
      )}
    </section>
  );
}
function AssetFinance({ asset }: { asset: Asset }) {
  const usage = asset.report?.result.billing_usage;
  const calculation =
    asset.royalty?.calculation || asset.report?.result.calculation;
  if (!calculation && !asset.invoice) return null;
  return (
    <section className="panel compact-panel" id="usage-finance">
      <h2>Usage, royalties & invoice status</h2>
      <PaymentModeNotice invoice={asset.invoice} />
      {usage?.disposition === "SAME_USAGE" ? (
        <p>
          No separate allocation for this edited version.{" "}
          <Link
            className="text-link"
            href={`/dashboard/submissions/${usage.canonical_asset_id}`}
          >
            Open canonical licensed usage
          </Link>
          .
        </p>
      ) : (
        calculation && (
          <p>
            <strong>{money(calculation.amount, calculation.currency)}</strong> ·{" "}
            {Number(calculation.amount) === 0
              ? "Included usage — no payable invoice"
              : asset.royalty
                ? "Recorded royalty proposal"
                : "Estimate only; eligibility review required"}
          </p>
        )
      )}
      {asset.royalty && (
        <p>
          Royalty: <Badge status={asset.royalty.status} /> · current
          eligibility:{" "}
          {asset.royalty.eligible_for_charge ? "satisfied" : "held for review"}
          {asset.royalty.status === "APPROVED" &&
            ` · charge approval ${asset.royalty.approval_current ? "current" : "requires renewal"}`}
        </p>
      )}
      {asset.invoice ? (
        <p>
          {asset.invoice.provider === "paypal_sandbox"
            ? "PayPal Sandbox invoice"
            : "Simulated invoice"}{" "}
          <strong>{asset.invoice.provider_id}</strong> ·{" "}
          <Badge status={asset.invoice.status} />
        </p>
      ) : (
        <p className="small">No invoice has been created for this asset.</p>
      )}
      <div className="button-row">
        {asset.royalty && (
          <Link className="button secondary" href="/dashboard/royalties">
            Review royalty & approval
          </Link>
        )}
        {asset.invoice && (
          <Link className="button secondary" href="/dashboard/invoices">
            Open invoice history
          </Link>
        )}
      </div>
    </section>
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
