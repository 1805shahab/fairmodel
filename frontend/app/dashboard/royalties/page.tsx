"use client";
import { useState } from "react";
import Link from "next/link";
import { Check, ReceiptText, X } from "lucide-react";
import {
  Badge,
  BusyButton,
  Empty,
  ErrorPanel,
  Field,
  Loading,
  PageHeading,
  useAction,
  useData,
} from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { PAYMENT_NOTICE, date, money, post } from "@/components/api";
import type { Royalty } from "@/components/types";

export default function Royalties() {
  const { data, error, loading, retry } = useData<Royalty[]>("/royalties");
  return (
    <>
      <PageHeading
        eyebrow="FAIRNESS, DOWN TO THE SECOND"
        title="Royalties"
        description="Deterministic calculations. Clear explanations. The artist has the final say."
      />
      <div className="alert warning">{PAYMENT_NOTICE}</div>
      {error && <ErrorPanel message={error} retry={retry} />}{" "}
      {loading ? (
        <Loading />
      ) : !data?.length ? (
        <section className="panel">
          <Empty
            title="Every fair share starts with evidence"
            description="Royalty entries appear after a permitted audio asset passes compliance. Restricted and uncertain submissions cannot be invoiced."
            href="/dashboard/submissions"
            label="View submissions"
          />
        </section>
      ) : (
        <div className="royalty-list">
          {data.map((x) => (
            <RoyaltyCard key={`${x.id}-${x.status}`} royalty={x} />
          ))}
        </div>
      )}
    </>
  );
}
function RoyaltyCard({ royalty: r }: { royalty: Royalty }) {
  const { role } = useWorkspace();
  const [note, setNote] = useState("");
  const { busy, error, run } = useAction();
  return (
    <section className="panel royalty-card">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">ROYALTY · {r.id.slice(0, 8)}</span>
          <h2 className="royalty-amount">{money(r.amount, r.currency)}</h2>
          <p>
            {date(r.created_at)} ·{" "}
            <Link
              className="text-link"
              href={`/dashboard/submissions/${r.asset_id}`}
            >
              Open audio & evidence ↗
            </Link>
          </p>
        </div>
        <Badge status={r.status} />
      </div>
      <div className="royalty-body">
        <code className="formula">{r.calculation.explanation}</code>
        <div className="calculation-details">
          <span>{r.calculation.spoken_seconds}s speech</span>
          <span>{r.calculation.allowance_remaining}s available allowance</span>
          <span>{r.calculation.additional_seconds}s additional use</span>
          <span>
            {r.calculation.billing_basis.replace("_", " ")} ·{" "}
            {r.calculation.rounding}
          </span>
        </div>
        {r.decision_note && (
          <p className="small">Artist decision: {r.decision_note}</p>
        )}
        {role === "artist" && r.status === "PENDING" && (
          <>
            <Field label="Approval / rejection note">
              <input
                minLength={5}
                maxLength={2000}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="I reviewed the measured usage and approved terms."
              />
            </Field>
            <div className="button-row">
              <BusyButton
                busy={busy}
                disabled={note.trim().length < 5}
                onClick={() =>
                  void run(async () => {
                    await post(`/royalties/${r.id}/decision`, {
                      approve: true,
                      note,
                    });
                  }, "Royalty approved.")
                }
              >
                <Check size={15} />
                Approve charge
              </BusyButton>
              <BusyButton
                className="button secondary"
                busy={busy}
                disabled={note.trim().length < 5}
                onClick={() =>
                  void run(async () => {
                    await post(`/royalties/${r.id}/decision`, {
                      approve: false,
                      note,
                    });
                  }, "Royalty rejected. No invoice can be created.")
                }
              >
                <X size={15} />
                Reject charge
              </BusyButton>
            </div>
          </>
        )}
        {role === "artist" && r.status === "APPROVED" && (
          <BusyButton
            busy={busy}
            onClick={() =>
              void run(async () => {
                await post(`/royalties/${r.id}/invoice`);
              }, "Simulated invoice ready. No funds were transferred.")
            }
          >
            <ReceiptText size={15} />
            Create / open simulated invoice
          </BusyButton>
        )}
        {r.status === "APPROVED" && (
          <Link className="text-link inline-link" href="/dashboard/invoices">
            View invoice history →
          </Link>
        )}
        {error && <ErrorPanel message={error} />}
      </div>
    </section>
  );
}
