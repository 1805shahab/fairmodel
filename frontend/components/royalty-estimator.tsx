"use client";
import { useEffect, useState } from "react";
import { api, money } from "./api";
import { Badge, ErrorPanel, Field, Loading, PageHeading, useData } from "./ui";
import { useWorkspace } from "./workspace";
import SourceCitations from "./source-citations";
import type { Campaign, License } from "./types";
import type { Estimate } from "./passport-types";

export default function RoyaltyEstimator() {
  const { role, revision } = useWorkspace();
  const licenses = useData<License[]>("/licenses");
  const [id, setId] = useState(""),
    [duration, setDuration] = useState("45");
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [outcome, setOutcome] = useState<{
    key: string;
    result?: Estimate;
    error?: string;
  } | null>(null);
  const selected = licenses.data?.find(
    (l) => l.id === id && l.status === "ACTIVE",
  );
  function chooseLicense(value: string) {
    setId(value);
    const selected = licenses.data?.find(
      (l) => l.id === value && l.status === "ACTIVE",
    );
    if (!selected) {
      setCampaign(null);
      return;
    }
    const first = (items: string[] | null) =>
      items?.find((item) => item !== "*") || "";
    setCampaign({
      name: first(selected.terms.campaigns),
      region: first(selected.terms.territories),
      medium: first(selected.terms.permitted_media),
      language: first(selected.terms.languages),
      category: "",
      generation_provider: null,
      intended_use_date:
        selected.terms.start_date || new Date().toISOString().slice(0, 10),
    });
  }
  const valid = Boolean(
    selected &&
    id &&
    campaign &&
    Number.isFinite(Number(duration)) &&
    Number(duration) >= 0 &&
    Number(duration) <= 600 &&
    duration !== "" &&
    role === "studio",
  );
  const signature = JSON.stringify([
    id,
    campaign,
    duration,
    role,
    revision,
    selected?.version,
  ]);
  const estimate =
    valid && outcome?.key === signature ? outcome.result : undefined;
  const error = valid && outcome?.key === signature ? outcome.error : undefined;
  const busy = valid && outcome?.key !== signature;
  useEffect(() => {
    if (!valid) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      api<Estimate>(`/licenses/${id}/estimate`, {
        method: "POST",
        body: JSON.stringify({ spoken_seconds: duration, campaign }),
        signal: controller.signal,
      })
        .then((result) => {
          if (!controller.signal.aborted)
            setOutcome({ key: signature, result });
        })
        .catch((e) => {
          if (!controller.signal.aborted)
            setOutcome({
              key: signature,
              error: e instanceof Error ? e.message : "Estimate unavailable.",
            });
        });
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [valid, signature, id, campaign, duration]);
  const change = (key: keyof Campaign, value: string) =>
    setCampaign((c) => (c ? { ...c, [key]: value } : null));
  return (
    <>
      <PageHeading
        eyebrow="PLAN BEFORE YOU SUBMIT"
        title="Royalty simulator"
        description="Explore the cost of intended voice usage using an actual approved agreement."
      />
      <div className="alert info">
        Estimate only — actual charges depend on submitted usage, the approved
        agreement, compliance checks, and artist approval.
      </div>
      {role !== "studio" ? (
        <div className="panel">
          <h2>Studio planning tool</h2>
          <p>
            Switch to the studio role to estimate usage under an assigned
            agreement. Artist financial approvals remain separate.
          </p>
        </div>
      ) : (
        <div className="simulator-grid">
          <section className="panel">
            <h2>Intended usage</h2>
            {licenses.loading && <Loading />}
            {licenses.error && (
              <ErrorPanel message={licenses.error} retry={licenses.retry} />
            )}
            <Field label="Approved agreement">
              <select
                value={id}
                onChange={(e) => chooseLicense(e.target.value)}
              >
                <option value="">Choose an active agreement</option>
                {licenses.data
                  ?.filter((l) => l.status === "ACTIVE")
                  .map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.title} · v{l.version}
                    </option>
                  ))}
              </select>
            </Field>
            {selected && campaign && (
              <>
                <div className="duration-estimate">
                  <label htmlFor="estimated-seconds">
                    Estimated spoken duration
                  </label>
                  <div>
                    <input
                      id="estimated-seconds"
                      type="number"
                      min="0"
                      max="600"
                      step="0.01"
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                    />
                    <span>seconds</span>
                  </div>
                  <input
                    aria-label="Estimated spoken duration slider"
                    type="range"
                    min="0"
                    max="600"
                    step="0.01"
                    value={Number(duration) || 0}
                    onChange={(e) => setDuration(e.target.value)}
                  />
                </div>
                <div className="form-grid">
                  {(
                    [
                      ["name", "Intended campaign", selected.terms.campaigns],
                      [
                        "medium",
                        "Usage medium",
                        selected.terms.permitted_media,
                      ],
                      ["region", "Territory", selected.terms.territories],
                      ["language", "Language", selected.terms.languages],
                    ] as const
                  ).map(([key, label, values]) => (
                    <Field label={label} key={key}>
                      {values?.includes("*") ? (
                        <input
                          value={campaign[key] || ""}
                          onChange={(e) => change(key, e.target.value)}
                          placeholder="Contract permits any; declare intended value"
                        />
                      ) : (
                        <select
                          value={campaign[key] || ""}
                          onChange={(e) => change(key, e.target.value)}
                          disabled={!values?.length}
                        >
                          <option value="">
                            {values?.length
                              ? "Select intended value"
                              : "Unknown — contract review required"}
                          </option>
                          {values?.map((value) => (
                            <option key={value}>{value}</option>
                          ))}
                        </select>
                      )}
                    </Field>
                  ))}
                  <Field label="Intended use date">
                    <input
                      type="date"
                      value={campaign.intended_use_date}
                      onChange={(e) =>
                        change("intended_use_date", e.target.value)
                      }
                    />
                  </Field>
                  <Field label="Declared campaign category">
                    <input
                      maxLength={100}
                      value={campaign.category || ""}
                      onChange={(e) => change("category", e.target.value)}
                    />
                  </Field>
                </div>
                <p className="small muted">
                  Scope choices come from this approved contract. A wildcard
                  allows you to declare an intended value. This tool creates no
                  recording, allocation, approval or invoice.
                </p>
              </>
            )}
          </section>
          <section className="panel estimate-result" aria-live="polite">
            <span className="eyebrow">CONDITIONAL COST PREVIEW</span>
            <h2>Your estimate</h2>
            {busy && <Loading />}
            {error && <ErrorPanel message={error} />}{" "}
            {!id && <p>Choose an approved agreement to begin.</p>}
            {estimate && (
              <>
                <Badge status={estimate.scope_status} />
                {estimate.calculation ? (
                  <>
                    <p className="passport-amount">
                      {money(
                        estimate.calculation.amount,
                        estimate.calculation.currency,
                      )}
                    </p>
                    <dl className="passport-facts">
                      {[
                        [
                          "Estimated speech",
                          `${estimate.calculation.spoken_seconds}s`,
                        ],
                        [
                          "Allowance remaining",
                          `${estimate.calculation.allowance_remaining}s`,
                        ],
                        [
                          "Prior cumulative usage",
                          `${estimate.calculation.prior_seconds}s`,
                        ],
                        [
                          "Additional usage",
                          `${estimate.calculation.additional_seconds}s`,
                        ],
                        [
                          "Approved rate",
                          `${money(estimate.calculation.rate, estimate.calculation.currency)} / second`,
                        ],
                        [
                          "Billing",
                          estimate.calculation.billing_basis.replaceAll(
                            "_",
                            " ",
                          ),
                        ],
                      ].map(([label, value]) => (
                        <div key={label}>
                          <dt>{label}</dt>
                          <dd>{value}</dd>
                        </div>
                      ))}
                    </dl>
                    <p>{estimate.calculation.explanation}</p>
                  </>
                ) : (
                  <p className="alert warning">
                    A reliable payable estimate is unavailable for these terms
                    or scope. Review the agreement; no rate is invented.
                  </p>
                )}
                {estimate.reasons.map((reason, i) => (
                  <p className="alert warning" key={i}>
                    {reason}
                  </p>
                ))}
                <h3>Before this becomes actual usage</h3>
                <ul>
                  {estimate.requirements.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
                <details>
                  <summary>Approved clauses behind this preview</summary>
                  <SourceCitations items={estimate.citations} licenseId={id} />
                </details>
              </>
            )}
          </section>
        </div>
      )}
    </>
  );
}
