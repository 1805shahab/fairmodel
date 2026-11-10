"use client";
import { useState } from "react";
import dynamic from "next/dynamic";
import {
  Empty,
  ErrorPanel,
  Loading,
  PageHeading,
  useData,
} from "@/components/ui";
import { money, statusLabel } from "@/components/api";
import { PaymentModeNotice } from "@/components/invoice-actions";
import type { Analytics } from "@/components/types";
const Grid = dynamic(() => import("@/components/analytics-grid"), {
  ssr: false,
  loading: () => <Loading />,
});

export default function AnalyticsPage() {
  const { data, error, loading, retry } = useData<Analytics>("/analytics");
  const [state, setState] = useState("");
  const [currency, setCurrency] = useState("");
  const currencyRows = (data?.rows || []).filter(
    (row) => !currency || row.currency === currency,
  );
  const states = Array.from(
    new Set(currencyRows.map((row) => row.status)),
  ).sort();
  const rows = currencyRows.filter((row) => !state || row.status === state);
  return (
    <>
      <PageHeading
        eyebrow="THE VALUE OF YOUR VOICE"
        title="Royalty analytics"
        description="Follow every allocation from proposal to payment. Your records, with currencies kept separate."
      />
      <PaymentModeNotice />
      {error && <ErrorPanel message={error} retry={retry} />}
      {loading ? (
        <Loading />
      ) : (
        data && (
          <>
            {Object.entries(data.totals_by_currency).map(([code, values]) => (
              <section
                className="analytics-currency"
                key={code}
                aria-label={`${code} ledger totals`}
              >
                <div className="analytics-currency-heading">
                  <h2>{code} overview</h2>
                  <span className="small">
                    All recorded entries · filters below apply to the ledger
                  </span>
                </div>
                <div className="analytics-kpis">
                  {[
                    {
                      label: "Awaiting artist approval",
                      value: values.proposed,
                    },
                    { label: "Approved royalties", value: values.approved },
                    {
                      label: "Paid · simulated only",
                      value: values.paid_simulated,
                    },
                    {
                      label: "Received · Sandbox test funds",
                      value: values.paid_sandbox || "0",
                    },
                  ].map((x) => (
                    <article className="stat-card" key={x.label}>
                      <span className="stat-top">{x.label}</span>
                      <strong>{money(x.value, code)}</strong>
                    </article>
                  ))}
                </div>
              </section>
            ))}
            {data.rows.length > 0 && (
              <section className="panel allocation-explorer">
                <div className="panel-heading">
                  <div>
                    <h2>Follow the allocations</h2>
                    <p>
                      Choose a state to filter the ledger. Counts describe
                      entries, not financial totals.
                    </p>
                  </div>
                  <label className="ledger-currency">
                    Currency
                    <select
                      aria-label="Ledger currency"
                      value={currency}
                      onChange={(e) => {
                        setCurrency(e.target.value);
                        setState("");
                      }}
                    >
                      <option value="">All currencies · counts only</option>
                      {Array.from(new Set(data.rows.map((row) => row.currency)))
                        .sort()
                        .map((code) => (
                          <option key={code}>{code}</option>
                        ))}
                    </select>
                  </label>
                </div>
                <div
                  className="allocation-filters"
                  role="group"
                  aria-label="Filter ledger by royalty state"
                >
                  <button
                    className="allocation-filter"
                    aria-pressed={!state}
                    onClick={() => setState("")}
                  >
                    <span>All entries</span>
                    <strong>{currencyRows.length}</strong>
                  </button>
                  {states.map((value) => {
                    const count = currencyRows.filter(
                      (row) => row.status === value,
                    ).length;
                    return (
                      <button
                        key={value}
                        className="allocation-filter"
                        aria-pressed={state === value}
                        onClick={() => setState(state === value ? "" : value)}
                      >
                        <span>{statusLabel(value)}</span>
                        <strong>{count}</strong>
                        <span className="allocation-bar" aria-hidden="true">
                          <i
                            style={{
                              transform: `scaleX(${count / Math.max(currencyRows.length, 1)})`,
                            }}
                          />
                        </span>
                      </button>
                    );
                  })}
                </div>
              </section>
            )}
            <section className="panel" id="royalty-ledger">
              <div className="panel-heading">
                <div>
                  <h2>Royalty ledger</h2>
                  <p aria-live="polite">
                    {rows.length} {state ? statusLabel(state) + " " : ""}
                    {rows.length === 1 ? "entry" : "entries"}
                    {currency ? ` in ${currency}` : " across currencies"}.
                  </p>
                </div>
                <span className="pill blue">AG Grid Community</span>
              </div>
              {(state || currency) && (
                <button
                  className="button secondary small-button clear-ledger"
                  onClick={() => {
                    setState("");
                    setCurrency("");
                  }}
                >
                  Clear ledger filters
                </button>
              )}
              {data.rows.length ? (
                <Grid rows={rows} />
              ) : (
                <Empty
                  title="Your ledger starts with an approved usage"
                  description="Measured speech, approved terms and artist review determine each allocation."
                  href="/dashboard/submissions"
                  label="Review submissions"
                />
              )}
            </section>
          </>
        )
      )}
    </>
  );
}
