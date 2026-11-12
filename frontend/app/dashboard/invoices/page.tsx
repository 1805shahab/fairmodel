"use client";
import { money } from "@/components/display-money";

import { useState } from "react";
import Link from "next/link";
import { Check, Send, RefreshCw, ExternalLink } from "lucide-react";
import {
  PaymentModeNotice,
  SANDBOX_NOTICE,
} from "@/components/invoice-actions";
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
import { PAYMENT_NOTICE, date, post } from "@/components/api";
import type { Invoice, Royalty } from "@/components/types";

export default function Invoices() {
  const { data, error, loading, retry } = useData<Invoice[]>("/invoices");
  const context = useData<Royalty[]>("/royalties");
  const [query, setQuery] = useState("");
  const [provider, setProvider] = useState("all");
  const visible = data?.filter(
    (x) =>
      (provider === "all" || (x.provider || "mock") === provider) &&
      `${x.provider_id} ${x.recipient} ${x.status}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <>
      <PageHeading
        eyebrow="TRANSPARENT SETTLEMENT"
        title="Invoices & payments"
        description="Artist-approved invoices, provider-specific states, and an auditable payment history."
      />
      <PaymentModeNotice />
      <div className="list-filters">
        <label>
          Find invoice
          <input
            type="search"
            placeholder="Invoice ID, recipient or status"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <label>
          Payment provider
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            <option value="all">All providers</option>
            <option value="mock">Local simulation</option>
            <option value="paypal_sandbox">PayPal Sandbox</option>
          </select>
        </label>
        <span>
          {data
            ? `${visible?.length} of ${data.length} invoices`
            : "Loading invoices…"}
        </span>
      </div>
      <details className="payment-notice">
        <summary>How test invoices work</summary>
        <strong>Invoice providers stay separate</strong>
        <p>
          Mock records use local simulation. PayPal Sandbox records use actual
          test API responses; no real money is transferred.
        </p>
        <p>
          For actual Sandbox invoices: create a draft after artist approval,
          explicitly send it, pay manually as the test buyer, then refresh
          status. The walkthrough below applies only to mock invoices.
        </p>
        <ol
          className="payment-demo-steps"
          aria-label="Simulated payment demonstration steps"
        >
          <li>
            <strong>Artist</strong>
            <span>
              Approves the royalty, then simulates sending the invoice.
            </span>
          </li>
          <li>
            <strong>Studio</strong>
            <span>Simulates payment completion; no funds move.</span>
          </li>
          <li>
            <strong>Both</strong>
            <span>Review the locally recorded invoice event history.</span>
          </li>
        </ol>
        <Link
          className="text-link payment-status-link"
          href="/dashboard/settings"
        >
          See PayPal Sandbox status
        </Link>
      </details>
      {error && <ErrorPanel message={error} retry={retry} />}{" "}
      {context.error && (
        <ErrorPanel
          message={`Linked royalty details: ${context.error}`}
          retry={context.retry}
        />
      )}
      {loading ? (
        <Loading />
      ) : !data?.length ? (
        <section className="panel">
          <Empty
            title="No invoices yet"
            description="The artist must approve a positive royalty before creating an invoice."
            href="/dashboard/royalties"
            label="Review royalties"
          />
        </section>
      ) : visible?.length ? (
        visible.map((x) => (
          <InvoiceCard
            key={`${x.id}-${x.status}`}
            invoice={x}
            royalty={context.data?.find((r) => r.id === x.royalty_id)}
          />
        ))
      ) : (
        <section className="panel">
          <Empty
            title="No matching invoices"
            description="Change the search or payment provider to see other records."
          />
        </section>
      )}
    </>
  );
}
function InvoiceCard({
  invoice: x,
  royalty,
}: {
  invoice: Invoice;
  royalty?: Royalty;
}) {
  const { role, notify } = useWorkspace();
  const sandbox = x.provider === "paypal_sandbox";
  const { busy, error, run } = useAction();
  const [showEvents, setShowEvents] = useState(false);
  const events = useData<Invoice>(`/invoices/${x.id}`);
  return (
    <section className="panel invoice-card">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            {sandbox
              ? "ACTUAL PAYPAL SANDBOX INVOICE"
              : "LOCAL SIMULATED INVOICE"}
          </span>
          <h2>{x.provider_id}</h2>
          <span className="provider-badge">
            {sandbox ? "PayPal Sandbox (test funds)" : "Mock provider"}
          </span>
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
        {royalty && (
          <div className="invoice-context">
            <div>
              <span>Campaign</span>
              <Link
                className="text-link"
                href={`/dashboard/submissions/${royalty.asset_id}`}
              >
                {royalty.campaign_name || "Open recording"}
              </Link>
            </div>
            <div>
              <span>Agreement</span>
              <Link
                className="text-link"
                href={`/dashboard/licenses/${royalty.license_id}`}
              >
                {royalty.license_title || "Open approved agreement"}
              </Link>
            </div>
            <div>
              <span>Licensed artist / studio</span>
              <strong>
                {royalty.artist_name || "Not supplied"} /{" "}
                {royalty.studio_name || "Not supplied"}
              </strong>
            </div>
          </div>
        )}
        <p className="simulation-inline">
          {sandbox ? SANDBOX_NOTICE : PAYMENT_NOTICE}
        </p>
        {sandbox && (
          <div className="measurement-grid">
            <div>
              <span>Issuer (configured Sandbox merchant)</span>
              <strong>
                {x.sandbox?.issuer || "Awaiting provider evidence"}
              </strong>
            </div>
            <div>
              <span>Invoice number</span>
              <strong>{x.sandbox?.invoice_number || "Not supplied"}</strong>
            </div>
            <div>
              <span>Provider status</span>
              <strong>{x.sandbox?.provider_status || "Unknown"}</strong>
            </div>
            <div>
              <span>Due date</span>
              <strong>
                {x.sandbox?.due_date || "Due on receipt / not supplied"}
              </strong>
            </div>
            <div>
              <span>Reported paid amount (Sandbox)</span>
              <strong>
                {money(x.sandbox?.paid_amount || "0", x.currency)}
              </strong>
            </div>
            <div>
              <span>Outstanding balance</span>
              <strong>
                {x.sandbox?.due_amount != null
                  ? money(x.sandbox.due_amount, x.currency)
                  : "Not yet verified"}
              </strong>
            </div>
            <div>
              <span>Last successful status sync</span>
              <strong>
                {x.sandbox?.last_synced_at
                  ? new Date(x.sandbox.last_synced_at).toLocaleString()
                  : "Not synchronized"}
              </strong>
            </div>
          </div>
        )}
        {sandbox && x.sandbox?.error && (
          <div className="alert warning">
            Latest provider attempt: {x.sandbox.error}. Historical financial
            amounts are unchanged; refresh to retry reconciliation.
          </div>
        )}
        <p className="small">
          Linked royalty entry:{" "}
          <Link className="text-link" href="/dashboard/royalties">
            {x.royalty_id.slice(0, 10)} ↗
          </Link>
        </p>
        <div className="invoice-flow">
          <span className="complete">1 · Created</span>
          <i />
          <span
            className={
              [
                "SENT",
                "VIEWED",
                "UNPAID",
                "PAYMENT_PENDING",
                "PARTIALLY_PAID",
                "PAID",
                "PAID_SIMULATED",
              ].includes(x.status)
                ? "complete"
                : ""
            }
          >
            2 · {sandbox ? "Sent / awaiting payment" : "Simulated send"}
          </span>
          <i />
          <span
            className={
              ["PAID_SIMULATED", "PAID"].includes(x.status) ? "complete" : ""
            }
          >
            3 · {sandbox ? "Verified Sandbox settlement" : "Simulated paid"}
          </span>
        </div>
        {sandbox && !["PAID", "CANCELLED", "REFUNDED"].includes(x.status) && (
          <p className="payment-awaiting">
            <strong>Awaiting payment confirmation</strong> · Sending an invoice
            does not confirm payment. Refresh status to retrieve PayPal’s latest
            evidence.
          </p>
        )}
        <div className="button-row">
          {role === "artist" && x.status === "DRAFT" && (
            <BusyButton
              busy={busy}
              disabled={x.eligible_for_send === false}
              onClick={() =>
                void run(async () => {
                  if (
                    sandbox &&
                    !window.confirm(
                      `Send actual PayPal SANDBOX invoice ${x.provider_id} to ${x.recipient} for ${x.amount} ${x.currency}? PayPal may notify this Sandbox buyer. No real money is involved.`,
                    )
                  )
                    return;
                  await post(`/invoices/${x.id}/send`, {
                    event_key: crypto.randomUUID(),
                    confirm_sandbox: sandbox,
                  });
                  notify(
                    sandbox
                      ? "Sandbox send accepted; displayed payment status comes from PayPal synchronization."
                      : "Simulated send recorded. No email was sent.",
                  );
                })
              }
            >
              <Send size={15} />
              {sandbox ? "Send Sandbox invoice" : "Simulate sending invoice"}
            </BusyButton>
          )}
          {!sandbox && role === "studio" && x.status === "SENT" && (
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
          {!sandbox && role === "artist" && x.status === "SENT" && (
            <span className="small">
              Switch to Studio view to deliberately simulate completion.
            </span>
          )}
          {sandbox && (
            <>
              <BusyButton
                className="button secondary"
                busy={busy}
                onClick={() =>
                  void run(async () => {
                    await post(`/invoices/${x.id}/refresh`);
                  }, "Status synchronized from PayPal Sandbox.")
                }
              >
                <RefreshCw size={15} />
                Refresh PayPal status
              </BusyButton>
              {x.sandbox?.payment_url && x.status !== "DRAFT" && (
                <a
                  className="button secondary"
                  href={x.sandbox.payment_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink size={15} />
                  Open PayPal Sandbox invoice
                </a>
              )}
            </>
          )}
          <button
            className="button secondary"
            onClick={() => setShowEvents(!showEvents)}
          >
            {showEvents ? "Hide" : "Show"} event history
          </button>
        </div>
        {x.status === "DRAFT" && x.eligible_for_send === false && (
          <div className="alert warning">
            Sending is blocked until current usage eligibility and artist charge
            approval are confirmed. Open Royalties to review or renew approval.
            The historical invoice remains unchanged.
          </div>
        )}
        {sandbox && (
          <p className="small">
            The payment link is displayed only when returned by PayPal. Sign in
            manually with the configured Sandbox buyer. No buyer password is
            stored. Sending, viewing, partial payment and full settlement are
            separate states.
          </p>
        )}
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
