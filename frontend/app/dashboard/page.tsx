"use client";
import Link from "next/link";
import {
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  AudioLines,
  FileCheck2,
  FilePlus2,
  Mic2,
  ShieldCheck,
  Sparkles,
  Wallet,
} from "lucide-react";
import {
  Badge,
  Empty,
  ErrorPanel,
  Loading,
  PageHeading,
  useData,
} from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { date, money } from "@/components/api";
import type { Analytics, Asset, License } from "@/components/types";

export default function Dashboard() {
  const { role } = useWorkspace();
  const stats = useData<Analytics>("/analytics"),
    licenses = useData<License[]>("/licenses"),
    assets = useData<Asset[]>("/assets");
  const all = stats.data;
  const totals = Object.entries(all?.totals_by_currency || {});
  return (
    <>
      <PageHeading
        eyebrow="YOUR VOICE. YOUR VALUE."
        title={
          role === "artist"
            ? "Good to see you, Amara."
            : "Let’s create responsibly."
        }
        description={
          role === "artist"
            ? "A clear view of your voice rights, usage, and what you’ve earned."
            : "Your licensed voices, campaign submissions, and royalty obligations in one place."
        }
        action={
          <Link
            className="button"
            href={
              role === "artist"
                ? "/dashboard/licenses/new"
                : "/dashboard/submissions/new"
            }
          >
            {role === "artist" ? (
              <FilePlus2 size={16} />
            ) : (
              <AudioLines size={16} />
            )}{" "}
            {role === "artist" ? "New voice license" : "Submit audio"}
          </Link>
        }
      />
      {stats.error && <ErrorPanel message={stats.error} retry={stats.retry} />}
      <div className="stat-grid">
        <article className="stat-card">
          <div className="stat-top">
            Approved royalties{" "}
            <span className="stat-icon blue-icon">
              <Wallet size={18} />
            </span>
          </div>
          <strong>
            {totals.length
              ? totals.map(([c, v]) => (
                  <span className="currency-line" key={c}>
                    {money(v.approved, c)}
                  </span>
                ))
              : "—"}
          </strong>
          <span className="stat-note">Artist approved · by currency</span>
        </article>
        <article className="stat-card">
          <div className="stat-top">
            Voice licenses{" "}
            <span className="stat-icon purple-icon">
              <FileCheck2 size={18} />
            </span>
          </div>
          <strong>{all?.license_count ?? "—"}</strong>
          <span className="stat-note">
            {licenses.data?.filter((x) => x.status === "ACTIVE").length ?? 0}{" "}
            active agreements
          </span>
        </article>
        <article className="stat-card">
          <div className="stat-top">
            Audio submissions{" "}
            <span className="stat-icon teal-icon">
              <AudioLines size={18} />
            </span>
          </div>
          <strong>{all?.asset_count ?? "—"}</strong>
          <span className="stat-note">Real audio. Measured usage.</span>
        </article>
        <article className="stat-card">
          <div className="stat-top">
            Needs your attention{" "}
            <span className="stat-icon amber-icon">
              <ShieldCheck size={18} />
            </span>
          </div>
          <strong>
            {all ? all.review_count + all.pending_approvals : "—"}
          </strong>
          <span className="stat-note">Reviews + pending charge approvals</span>
        </article>
      </div>
      <div className="dashboard-columns">
        <section className="panel activity-panel">
          <div className="panel-heading">
            <div>
              <h2>Recent audio submissions</h2>
              <p>Follow every asset from upload to approval.</p>
            </div>
            <Link href="/dashboard/submissions" className="text-link">
              View all <ArrowUpRight size={14} />
            </Link>
          </div>
          {assets.loading ? (
            <Loading />
          ) : assets.error ? (
            <ErrorPanel message={assets.error} retry={assets.retry} />
          ) : !assets.data?.length ? (
            <Empty
              title="Your next collaboration starts here"
              description="Approve a license, then switch to the studio persona to submit your first audio asset."
              href="/dashboard/licenses"
              label="Explore voice licenses"
            />
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>CAMPAIGN / ASSET</th>
                    <th>SUBMITTED</th>
                    <th>STATUS</th>
                    <th>
                      <span className="sr-only">Open</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {assets.data.slice(0, 5).map((x) => (
                    <tr key={x.id}>
                      <td>
                        <Link
                          className="asset-cell"
                          href={`/dashboard/submissions/${x.id}`}
                        >
                          <span className="file-icon">
                            <AudioLines size={20} />
                          </span>
                          <span>
                            <strong>{x.campaign.name}</strong>
                            <small>{x.original_name}</small>
                          </span>
                        </Link>
                      </td>
                      <td className="muted nowrap">{date(x.created_at)}</td>
                      <td>
                        <Badge status={x.status} />
                      </td>
                      <td>
                        <Link
                          aria-label={`Open ${x.campaign.name}`}
                          href={`/dashboard/submissions/${x.id}`}
                        >
                          <ArrowUpRight size={17} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        <aside className="voice-card">
          <div className="voice-card-top">
            <span className="pill translucent">
              <Mic2 size={12} /> BUILT AROUND YOUR VOICE
            </span>
            <AudioLines size={70} strokeWidth={0.8} />
          </div>
          <h2>
            Creative freedom.
            <br />
            Clear boundaries.
          </h2>
          <p>
            Put your terms in writing. Understand how your voice is used. Keep
            the final say.
          </p>
          <Link href="/dashboard/licenses">
            Manage voice rights <ArrowRight size={17} />
          </Link>
          <div className="voice-card-footer">
            <ShieldCheck size={14} /> Human approval at every key step
          </div>
        </aside>
      </div>
      <div className="dashboard-columns lower-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Your licensing agreements</h2>
              <p>The foundation of every fair collaboration.</p>
            </div>
            <Link href="/dashboard/licenses" className="text-link">
              View all <ArrowUpRight size={14} />
            </Link>
          </div>
          {licenses.loading ? (
            <Loading />
          ) : !licenses.data?.length ? (
            <Empty
              title="Make your terms clear"
              description="Upload a licensing PDF and review the AI-extracted rules before activation."
              href={
                role === "artist"
                  ? "/dashboard/licenses/new"
                  : "/dashboard/licenses"
              }
              label={
                role === "artist"
                  ? "Create a license"
                  : "View assigned licenses"
              }
            />
          ) : (
            <div className="license-mini-list">
              {licenses.data.slice(0, 3).map((x) => (
                <Link key={x.id} href={`/dashboard/licenses/${x.id}`}>
                  <span className="file-icon">
                    <FileCheck2 size={19} />
                  </span>
                  <div>
                    <strong>{x.title}</strong>
                    <span>
                      Version {x.version} ·{" "}
                      {x.terms.billing_basis?.replace("_", " ") ||
                        "Terms awaiting review"}
                    </span>
                  </div>
                  <Badge status={x.status} />
                  <ArrowUpRight size={16} />
                </Link>
              ))}
            </div>
          )}
        </section>
        <section className="panel next-steps">
          <div className="panel-heading">
            <div>
              <h2>A fairer workflow</h2>
              <p>From agreement to accountability.</p>
            </div>
            <Sparkles size={19} className="blue-text" />
          </div>
          {[
            {
              n: "01",
              title: "Define the permission",
              text: "Extract, review, and approve contract terms.",
              Icon: FileCheck2,
            },
            {
              n: "02",
              title: "Check the actual usage",
              text: "Measure speech and inspect content evidence.",
              Icon: AudioLines,
            },
            {
              n: "03",
              title: "Approve a fair share",
              text: "Review the math. Create a simulated invoice.",
              Icon: ArrowDownLeft,
            },
          ].map(({ n, title, text, Icon }) => (
            <div key={n} className="next-step">
              <span>{n}</span>
              <div>
                <strong>{title}</strong>
                <p>{text}</p>
              </div>
              <Icon size={18} />
            </div>
          ))}
        </section>
      </div>
      <div className="trust-strip">
        <ShieldCheck size={17} />
        <strong>Trust is in the details.</strong>
        <span>
          Source-backed contract terms. Transparent calculations. A complete
          audit trail.
        </span>
        <Link href="/dashboard/audit">
          View audit trail <ArrowRight size={14} />
        </Link>
      </div>
    </>
  );
}
