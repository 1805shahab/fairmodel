"use client";
import { useState } from "react";
import Link from "next/link";
import { Check, Send } from "lucide-react";
import {
  Badge,
  BusyButton,
  Empty,
  ErrorPanel,
  Loading,
  PageHeading,
  useAction,
  useData,
} from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { PAYMENT_NOTICE, date, money, post } from "@/components/api";
import type { Invoice } from "@/components/types";

export default function Invoices() {
  const { data, error, loading, retry } = useData<Invoice[]>("/invoices");
  return (
    <>
      <PageHeading
        eyebrow="TRANSPARENT SETTLEMENT"
        title="Invoices & payments"
        description="Persistent simulated invoices, deliberate state transitions, and a clear event history."
      />
      <div className="payment-notice">
        <strong>{PAYMENT_NOTICE}</strong>
        <p>
          Local mock provider. No PayPal connection, payment request, email, or
          transfer occurs.
        </p>
      </div>
      {error && <ErrorPanel message={error} retry={retry} />}{" "}
      {loading ? (
        <Loading />
      ) : !data?.length ? (
        <section className="panel">
          <Empty
            title="No simulated invoices yet"
            description="The artist must approve a positive royalty before creating an invoice."
            href="/dashboard/royalties"
            label="Review royalties"
          />
        </section>
      ) : (
        data.map((x) => <InvoiceCard key={`${x.id}-${x.status}`} invoice={x} />)
      )}
    </>
  );
}
function InvoiceCard({ invoice: x }: { invoice: Invoice }) {
  const { role } = useWorkspace();
  const { busy, error, run } = useAction();
  const [showEvents, setShowEvents] = useState(false);
  const events = useData<Invoice>(`/invoices/${x.id}`);
  return (
    <section className="panel invoice-card">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">LOCAL SIMULATED INVOICE</span>
          <h2>{x.provider_id}</h2>
          <p>
            {date(x.created_at)} · Recipient: {x.recipient}
          </p>
        </div>
        <div className="invoice-total">
          <strong>{money(x.amount, x.currency)}</strong>
          <Badge status={x.status} />
        </div>
      </div>
      <div className="invoice-body">
        <p className="simulation-inline">{PAYMENT_NOTICE}</p>
        <p className="small">
          Linked royalty entry:{" "}
          <Link className="text-link" href="/dashboard/royalties">
            {x.royalty_id.slice(0, 10)} ↗
          </Link>
        </p>
        <div className="invoice-flow">
          <span className="complete">1 · Created</span>
          <i />
          <span className={x.status !== "DRAFT" ? "complete" : ""}>
            2 · Simulated send
          </span>
          <i />
          <span className={x.status === "PAID_SIMULATED" ? "complete" : ""}>
            3 · Simulated paid
          </span>
        </div>
        <div className="button-row">
          {role === "artist" && x.status === "DRAFT" && (
            <BusyButton
              busy={busy}
              onClick={() =>
                void run(async () => {
                  await post(`/invoices/${x.id}/send`, {
                    event_key: crypto.randomUUID(),
                  });
                }, "Simulated send recorded. No email was sent.")
              }
            >
              <Send size={15} />
              Simulate sending invoice
            </BusyButton>
          )}
          {role === "studio" && x.status === "SENT" && (
            <BusyButton
              busy={busy}
              onClick={() =>
                void run(async () => {
                  await post(`/invoices/${x.id}/simulate-payment`, {
                    event_key: crypto.randomUUID(),
                  });
                }, "Simulated payment completion recorded. No real funds transferred.")
              }
            >
              <Check size={15} />
              Simulate payment completion
            </BusyButton>
          )}
          {role === "artist" && x.status === "SENT" && (
            <span className="small">
              Switch to Studio view to deliberately simulate completion.
            </span>
          )}
          <button
            className="button secondary"
            onClick={() => setShowEvents(!showEvents)}
          >
            {showEvents ? "Hide" : "Show"} event history
          </button>
        </div>
        {showEvents && (
          <div className="event-list">
            {events.error ? (
              <ErrorPanel message={events.error} retry={events.retry} />
            ) : (
              events.data?.events?.map((e) => (
                <div key={e.id}>
                  <span className="status-dot" />
                  <strong>{e.kind.replaceAll("_", " ")}</strong>
                  <span>
                    {new Date(e.created_at).toLocaleString("en", {
                      timeZone: "Asia/Karachi",
                    })}{" "}
                    PKT
                  </span>
                </div>
              ))
            )}
          </div>
        )}
        {error && <ErrorPanel message={error} />}
      </div>
    </section>
  );
}
