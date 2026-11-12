"use client";
import { useState } from "react";
import { ArrowRight, Check, CircleHelp, Play, ShieldAlert } from "lucide-react";
import { Badge } from "./ui";
import SourceCitations from "./source-citations";
import type { AudioResult, Evidence, ReportResult, Campaign } from "./types";

const fields: Record<string, string> = {
  region: "territories",
  medium: "permitted_media",
  language: "languages",
  campaign: "campaigns",
  start_date: "start_date",
  end_date: "end_date",
  restricted_category: "restricted_categories",
  additional_usage: "additional_usage_permitted",
  duration: "included_seconds",
};
const normal = (value: string) =>
  value.trim().replace(/\s+/g, " ").toLowerCase();

export default function EvidenceExplorer({
  report,
  audio,
  campaign,
  licenseId,
  onSeek,
}: {
  report: ReportResult;
  audio?: AudioResult;
  campaign: Campaign;
  licenseId: string;
  onSeek?: (seconds: number) => void;
}) {
  const [selected, setSelected] = useState("rule-0");
  const items = [
    ...(report.rule_checks || []).map((rule, i) => ({
      id: `rule-${i}`,
      label: rule.rule.replaceAll("_", " "),
      status: rule.outcome,
      explanation: rule.explanation,
      citations: rule.citations?.length
        ? rule.citations
        : report.source_pages.filter((c) => c.field === fields[rule.rule]),
      passage: "",
      provider: "Deterministic rules / recorded workflow",
      next:
        rule.outcome === "needs_review" || rule.outcome === "violation"
          ? report.next_action
          : "No action for this satisfied condition.",
    })),
    ...report.findings.findings.map((finding, i) => ({
      id: `ai-${i}`,
      label: finding.category,
      status:
        finding.possible_conflict || finding.needs_review
          ? "needs_review"
          : "observation",
      explanation: finding.explanation,
      citations: report.source_pages.filter(
        (c) =>
          c.field === "restricted_categories" ||
          c.field === "special_conditions",
      ),
      passage: finding.passage,
      provider: `${report.assessment_fixture ? "Local fixture" : report.provider} — advisory content observation`,
      next:
        finding.needs_review || finding.possible_conflict
          ? "Artist: inspect the passage and approved clause. This observation is not a legal determination."
          : "No prohibited category is established by this observation.",
    })),
    ...(report.unresolved_conditions || report.reasons).map((reason, i) => ({
      id: `review-${i}`,
      label: `Review requirement ${i + 1}`,
      status: "needs_review",
      explanation: reason,
      citations: [] as Evidence[],
      passage: "",
      provider: "Combined evidence / human review",
      next: report.next_action,
    })),
  ];
  const active = items.find((item) => item.id === selected) || items[0];
  const candidates =
    active?.passage && normal(active.passage).length >= 8
      ? audio?.timestamps.filter(
          (segment) =>
            Number.isFinite(segment.start) &&
            Number.isFinite(segment.end) &&
            segment.start >= 0 &&
            segment.end > segment.start &&
            segment.end <= Number(audio.duration_seconds) &&
            segment.start < Number(audio.duration_seconds) &&
            normal(segment.text).includes(normal(active.passage)),
        ) || []
      : [];
  const timestamp = candidates.length === 1 ? candidates[0] : undefined;
  return (
    <section
      className="panel evidence-explorer"
      aria-label="Compliance evidence explorer"
    >
      <header className="section-heading">
        <div>
          <span className="eyebrow">FOLLOW THE EVIDENCE</span>
          <h2>Why this decision?</h2>
          <p className="muted">
            Select a condition to inspect its source and the next action.
          </p>
        </div>
      </header>
      {active ? (
        <div className="explorer-grid">
          <div
            className="explorer-list"
            role="group"
            aria-label="Evidence conditions"
          >
            {items.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={item.id === active.id}
                onClick={() => setSelected(item.id)}
              >
                {item.status === "satisfied" ? (
                  <Check size={16} />
                ) : item.status === "violation" ? (
                  <ShieldAlert size={16} />
                ) : (
                  <CircleHelp size={16} />
                )}
                <span>
                  {item.label}
                  <small>{item.status.replaceAll("_", " ")}</small>
                </span>
                <ArrowRight size={14} />
              </button>
            ))}
          </div>
          <article
            className="explorer-detail"
            aria-live="polite"
            aria-label="Selected evidence"
          >
            <Badge status={active.status.toUpperCase()} />
            <h3>{active.label}</h3>
            <p>{active.explanation}</p>
            <p className="small muted">Conclusion source: {active.provider}</p>
            {active.passage && (
              <div className="evidence-passage">
                <h4>Transcript evidence</h4>
                <blockquote>{active.passage}</blockquote>
                {timestamp && onSeek ? (
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => onSeek(timestamp.start)}
                  >
                    <Play size={14} />
                    Seek containing segment at {timestamp.start.toFixed(2)}s
                  </button>
                ) : (
                  <p className="small muted">
                    No unique containing transcript segment is available. No
                    timestamp inferred.
                  </p>
                )}
              </div>
            )}
            <details open>
              <summary>Approved contract support</summary>
              <SourceCitations items={active.citations} licenseId={licenseId} />
            </details>
            <details>
              <summary>Declared campaign metadata</summary>
              <dl className="passport-facts">
                {Object.entries(campaign).map(([key, value]) => (
                  <div key={key}>
                    <dt>{key.replaceAll("_", " ")}</dt>
                    <dd>{value || "Not supplied"}</dd>
                  </div>
                ))}
              </dl>
              <p className="small muted">
                Studio declarations do not independently prove distribution or
                publication.
              </p>
            </details>
            <div className="alert info">
              <strong>Next action</strong>
              <p>
                {active.next ||
                  report.next_action ||
                  "Review the current report."}
              </p>
            </div>
          </article>
        </div>
      ) : (
        <p className="muted">
          This historical report has no structured conditions. Reevaluate to
          obtain current evidence.
        </p>
      )}
    </section>
  );
}
