"use client";
import dynamic from "next/dynamic";
import { ErrorPanel, Loading, PageHeading, useData } from "@/components/ui";
import { PAYMENT_NOTICE, money } from "@/components/api";
import type { Analytics } from "@/components/types";
const Grid = dynamic(() => import("@/components/analytics-grid"), {
  ssr: false,
  loading: () => <Loading />,
});
export default function AnalyticsPage() {
  const { data, error, loading, retry } = useData<Analytics>("/analytics");
  return (
    <>
      <PageHeading
        eyebrow="THE VALUE OF YOUR VOICE"
        title="Royalty analytics"
        description="Explore your royalty ledger with AG Grid Community. Currencies are never combined."
      />
      <div className="alert warning">{PAYMENT_NOTICE}</div>
      {error && <ErrorPanel message={error} retry={retry} />}{" "}
      {loading ? (
        <Loading />
      ) : (
        data && (
          <>
            {Object.entries(data.totals_by_currency).map(
              ([currency, values]) => (
                <div className="measurement-grid" key={currency}>
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
                  ].map((x) => (
                    <article className="stat-card" key={x.label}>
                      <span className="stat-top">
                        {x.label} · {currency}
                      </span>
                      <strong>{money(x.value, currency)}</strong>
                      <span className="stat-note">
                        From persistent ledger records
                      </span>
                    </article>
                  ))}
                </div>
              ),
            )}
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Royalty ledger</h2>
                  <p>Approved, pending, rejected and no-charge allocations.</p>
                </div>
                <span className="pill blue">AG Grid Community</span>
              </div>
              <Grid rows={data.rows} />
            </section>
          </>
        )
      )}
    </>
  );
}
