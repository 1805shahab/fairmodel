"use client";
import Link from "next/link";
import { ArrowUpRight, FilePlus2, FileText } from "lucide-react";
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
import type { License } from "@/components/types";

export default function Licenses() {
  const { role } = useWorkspace();
  const { data, error, loading, retry } = useData<License[]>("/licenses");
  return (
    <>
      <PageHeading
        eyebrow="PERMISSION, IN WRITING"
        title="Voice licenses"
        description="Clear terms. Source evidence. Artist-approved agreements."
        action={
          role === "artist" && (
            <Link className="button" href="/dashboard/licenses/new">
              <FilePlus2 size={16} />
              New voice license
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
            title="Build your first agreement"
            description={
              role === "artist"
                ? "Start with a PDF. Gemini extracts the terms when configured, and you stay in control of approval."
                : "Your artist will assign an approved agreement before you can submit audio."
            }
            href={role === "artist" ? "/dashboard/licenses/new" : undefined}
            label="Create a license"
          />
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>AGREEMENT</th>
                  <th>VERSION</th>
                  <th>EXTRACTION SOURCE</th>
                  <th>CREATED</th>
                  <th>STATUS</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.map((x) => (
                  <tr key={x.id}>
                    <td>
                      <Link
                        href={`/dashboard/licenses/${x.id}`}
                        className="asset-cell"
                      >
                        <span className="file-icon">
                          <FileText size={20} />
                        </span>
                        <strong>{x.title}</strong>
                      </Link>
                    </td>
                    <td>v{x.version}</td>
                    <td className="muted">{x.extraction_provider}</td>
                    <td className="muted nowrap">{date(x.created_at)}</td>
                    <td>
                      <Badge status={x.status} />
                    </td>
                    <td>
                      <Link
                        href={`/dashboard/licenses/${x.id}`}
                        aria-label={`Open ${x.title}`}
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
