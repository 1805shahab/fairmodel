"use client";
import { money } from "@/components/display-money";

import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  AudioLines,
  FileCheck2,
  Plus,
  ReceiptText,
} from "lucide-react";
import { Badge, Empty, ErrorPanel, Loading, useData } from "@/components/ui";
import VoiceSculpture from "@/components/voice-sculpture";
import { useWorkspace } from "@/components/workspace";
import { date } from "@/components/api";
import type { Analytics, Asset, License, Invoice } from "@/components/types";

export default function Dashboard() {
  const { role } = useWorkspace();
  const stats = useData<Analytics>("/analytics"),
    licenses = useData<License[]>("/licenses"),
    assets = useData<Asset[]>("/assets"),
    invoices = useData<Invoice[]>("/invoices");
  const all = stats.data,
    artist = role === "artist",
    recordings = assets.data;
  const totals = Object.entries(all?.totals_by_currency || {});
  const signals = artist
    ? [
        ["Active agreements", all?.active_license_count, "licenses"],
        ["Compliance review holds", all?.review_count, "submissions"],
        ["Charge approvals pending", all?.pending_approvals, "royalties"],
        [
          "Outstanding test invoices",
          all?.outstanding_invoice_count,
          "invoices",
        ],
      ]
    : [
        ["Active agreements", all?.active_license_count, "licenses"],
        ["Submitted recordings", all?.asset_count, "submissions"],
        [
          "Awaiting audio analysis",
          recordings?.filter(
            (x) => (x.processing_state || x.status) !== "ANALYZED",
          ).length,
          "submissions",
        ],
        [
          "Needs review / restricted",
          recordings?.filter((x) =>
            ["NEEDS_REVIEW", "RESTRICTED_USAGE"].includes(
              x.compliance_state || "",
            ),
          ).length,
          "submissions",
        ],
      ];
  return (
    <div className="studio-console">
      <section className="console-hero" aria-labelledby="console-title">
        <div className="console-intro">
          <span className="console-kicker">
            <i /> {artist ? "THE ARTIST WORKSPACE" : "THE STUDIO WORKSPACE"}
          </span>
          <h1 id="console-title">
            {artist ? (
              <>
                Your voice.
                <br />
                <em>Your call.</em>
              </>
            ) : (
              <>
                Create with
                <br />
                <em>permission.</em>
              </>
            )}
          </h1>
          <p>
            {artist
              ? "The terms are yours. See where your voice goes, inspect the evidence, and make the next decision."
              : "From the first agreement to the final test invoice. Keep your campaign, its permissions and its evidence together."}
          </p>
          <div className="console-intro-actions">
            <Link
              className="button"
              href={
                artist
                  ? "/dashboard/licenses/new"
                  : "/dashboard/submissions/new"
              }
            >
              <Plus size={17} />
              {artist ? "New voice license" : "Submit audio"}
            </Link>
            <a className="console-review-link" href="#review-desk">
              {artist ? "Go to your review desk" : "See campaign actions"}
              <ArrowRight size={17} />
            </a>
          </div>
          <div className="console-hero-note">
            <span>HUMAN DECISIONS. RECORDED.</span>
            <p>
              AI assists. Artist authorization stays separate from automatic
              speaker verification.
            </p>
          </div>
        </div>
        <VoiceSculpture />
      </section>
      {stats.error && <ErrorPanel message={stats.error} retry={stats.retry} />}
      <nav className="console-signals" aria-label="Workspace records">
        {signals.map(([label, value, route], index) => (
          <Link key={String(label)} href={`/dashboard/${route}`}>
            <span className="signal-index">0{index + 1}</span>
            <strong>{value ?? "—"}</strong>
            <span>{label}</span>
            <ArrowUpRight size={16} />
          </Link>
        ))}
      </nav>
      <div className="console-desk" id="review-desk">
        <section className="review-desk" aria-labelledby="review-desk-heading">
          <div className="console-section-heading">
            <div>
              <span className="eyebrow">MAKE THE NEXT CALL</span>
              <h2 id="review-desk-heading">
                {artist ? "Your review desk." : "Campaign actions."}
              </h2>
            </div>
            <Link href="/dashboard/submissions">
              All submissions <ArrowUpRight size={16} />
            </Link>
          </div>
          {stats.loading ? (
            <Loading />
          ) : stats.error ? (
            <p className="alert warning">
              Review requests are unavailable. Retry the request above.
            </p>
          ) : all?.review_queue?.length ? (
            <div className="case-collection">
              {all.review_queue.slice(0, 3).map((asset, index) => (
                <Link
                  className={`review-case ${index === 0 ? "featured-case" : ""}`}
                  key={asset.id}
                  href={`/dashboard/submissions/${asset.id}`}
                >
                  <div className="review-case-top">
                    <span className="case-number">
                      CASE / {asset.id.slice(0, 6).toUpperCase()}
                    </span>
                    <Badge
                      status={
                        asset.compliance_state ||
                        asset.workflow_stage ||
                        asset.status
                      }
                    />
                  </div>
                  <h3>{asset.campaign.name}</h3>
                  <p>{asset.next_action}</p>
                  <div className="review-case-bottom">
                    <span>
                      License v{asset.license_version} ·{" "}
                      {asset.campaign.medium || "Medium undeclared"}
                    </span>
                    <span className="case-open">
                      <ArrowUpRight size={21} />
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <Empty
              title="Nothing waiting on your decision"
              description="New action requests appear here with the evidence you need to review them."
            />
          )}
        </section>
        <aside className="console-finance" aria-label="Recorded royalties">
          <div className="finance-panel-heading">
            <span className="eyebrow">THE FINANCIAL PICTURE</span>
            <ReceiptText size={20} />
          </div>
          <h2>{artist ? "Value, accounted for." : "Usage, accounted for."}</h2>
          {stats.loading ? (
            <Loading />
          ) : stats.error ? (
            <p>Financial records unavailable.</p>
          ) : totals.length ? (
            totals.map(([currency, v]) => (
              <div className="console-currency" key={currency}>
                <span className="finance-caption">
                  Outstanding test invoices · {currency}
                </span>
                <strong className="finance-amount">
                  {money(v.outstanding || "0", currency)}
                </strong>
                <dl>
                  <div>
                    <dt>Awaiting charge approval</dt>
                    <dd>{money(v.proposed, currency)}</dd>
                  </div>
                  <div>
                    <dt>Approved royalties</dt>
                    <dd>{money(v.approved, currency)}</dd>
                  </div>
                  <div>
                    <dt>Paid · local simulation</dt>
                    <dd>{money(v.paid_simulated, currency)}</dd>
                  </div>
                  <div>
                    <dt>Received · PayPal Sandbox</dt>
                    <dd>{money(v.paid_sandbox || "0", currency)}</dd>
                  </div>
                </dl>
              </div>
            ))
          ) : (
            <p className="small">No royalty amounts recorded yet.</p>
          )}
          <p className="finance-test-note">
            Test activity only. Mock payments are simulated; PayPal Sandbox uses
            test funds. No real money is represented here.
          </p>
          <Link className="finance-inspect" href="/dashboard/analytics">
            Inspect the ledger <ArrowUpRight size={16} />
          </Link>
        </aside>
      </div>
      <section
        className="console-submissions"
        aria-labelledby="console-submissions-heading"
      >
        <div className="console-section-heading">
          <div>
            <span className="eyebrow">THE WORK IN PROGRESS</span>
            <h2 id="console-submissions-heading">Recent submissions.</h2>
          </div>
          <Link href="/dashboard/submissions">
            View history <ArrowUpRight size={16} />
          </Link>
        </div>
        {assets.loading ? (
          <Loading />
        ) : assets.error ? (
          <ErrorPanel message={assets.error} retry={assets.retry} />
        ) : !recordings?.length ? (
          <Empty
            title="Your first recording starts here"
            description="Choose an approved license, declare the campaign and submit authorized audio."
            href={artist ? "/dashboard/licenses" : "/dashboard/submissions/new"}
            label={artist ? "View agreements" : "Submit audio"}
          />
        ) : (
          <div className="recording-collection">
            {recordings.slice(0, 4).map((asset) => (
              <Link
                className="recording-object"
                key={asset.id}
                href={`/dashboard/submissions/${asset.id}`}
              >
                <div className="recording-object-top">
                  <AudioLines size={29} strokeWidth={1.3} />
                  <ArrowUpRight size={17} />
                </div>
                <span className="recording-file">{asset.original_name}</span>
                <h3>{asset.campaign.name}</h3>
                <div className="recording-state">
                  <span>Audio</span>
                  <Badge status={asset.processing_state || asset.status} />
                </div>
                <div className="recording-state">
                  <span>Compliance</span>
                  <Badge status={asset.compliance_state || "PENDING"} />
                </div>
                <footer>
                  <span>
                    V{asset.license_version} ·{" "}
                    {asset.campaign.region || "Region undeclared"}
                  </span>
                  <time dateTime={asset.created_at}>
                    {date(asset.created_at)}
                  </time>
                </footer>
              </Link>
            ))}
          </div>
        )}
      </section>
      <div className="console-records">
        <section>
          <div className="console-section-heading">
            <h2>{artist ? "Your agreements" : "Assigned agreements"}</h2>
            <Link href="/dashboard/licenses">
              View all <ArrowUpRight size={15} />
            </Link>
          </div>
          {licenses.loading ? (
            <Loading />
          ) : licenses.error ? (
            <ErrorPanel message={licenses.error} retry={licenses.retry} />
          ) : licenses.data?.length ? (
            licenses.data.slice(0, 3).map((license) => (
              <Link
                className="console-record"
                href={`/dashboard/licenses/${license.id}`}
                key={license.id}
              >
                <FileCheck2 size={20} />
                <div>
                  <strong>{license.title}</strong>
                  <span>
                    Version {license.version} ·{" "}
                    {license.terms.included_seconds ?? "Unknown"}s allowance
                  </span>
                </div>
                <Badge status={license.status} />
              </Link>
            ))
          ) : (
            <p className="small">Upload an agreement to start the workflow.</p>
          )}
        </section>
        <section>
          <div className="console-section-heading">
            <h2>Invoice activity</h2>
            <Link href="/dashboard/invoices">
              View all <ArrowUpRight size={15} />
            </Link>
          </div>
          {invoices.loading ? (
            <Loading />
          ) : invoices.error ? (
            <ErrorPanel message={invoices.error} retry={invoices.retry} />
          ) : invoices.data?.length ? (
            invoices.data.slice(0, 3).map((invoice) => (
              <Link
                className="console-record"
                href="/dashboard/invoices"
                key={invoice.id}
              >
                <ReceiptText size={20} />
                <div>
                  <strong>{money(invoice.amount, invoice.currency)}</strong>
                  <span>
                    {invoice.provider === "paypal_sandbox"
                      ? "PayPal Sandbox (test funds)"
                      : "Mock provider"}{" "}
                    · {invoice.recipient}
                  </span>
                </div>
                <Badge status={invoice.status} />
              </Link>
            ))
          ) : (
            <p className="small">
              An eligible, artist-approved charge is required before invoicing.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
