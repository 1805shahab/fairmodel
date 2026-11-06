"use client";
import Link from "next/link";
import { ArrowUpRight, AudioLines, Upload } from "lucide-react";
import {
  Badge,
  Empty,
  ErrorPanel,
  Loading,
  PageHeading,
  useData,
} from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { date } from "@/components/api";
import type { Asset } from "@/components/types";
export default function Submissions() {
  const { role } = useWorkspace();
  const { data, error, loading, retry } = useData<Asset[]>("/assets");
  return (
    <>
      <PageHeading
        eyebrow="EVERY SECOND, ACCOUNTED FOR"
        title="Audio submissions"
        description="Real audio, transparent measurements, and explainable compliance."
        action={
          role === "studio" && (
            <Link className="button" href="/dashboard/submissions/new">
              <Upload size={16} />
              Submit audio
            </Link>
          )
        }
      />
      {error && <ErrorPanel message={error} retry={retry} />}
      <section className="panel">
        {loading ? (
          <Loading />
        ) : !data?.length ? (
          <Empty
            title="Ready when your campaign is"
            description="The studio can upload authorized audio against an active, artist-approved license."
            href={
              role === "studio"
                ? "/dashboard/submissions/new"
                : "/dashboard/licenses"
            }
            label={role === "studio" ? "Submit audio" : "Review licenses"}
          />
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>CAMPAIGN</th>
                  <th>DECLARED REGION</th>
                  <th>MEDIUM</th>
                  <th>SUBMITTED</th>
                  <th>STATUS</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.map((x) => (
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
                    <td>{x.campaign.region || "Not supplied"}</td>
                    <td>{x.campaign.medium || "Not supplied"}</td>
                    <td className="nowrap muted">{date(x.created_at)}</td>
                    <td>
                      <Badge status={x.status} />
                    </td>
                    <td>
                      <Link
                        href={`/dashboard/submissions/${x.id}`}
                        aria-label={`Open ${x.campaign.name}`}
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
    </>
  );
}
