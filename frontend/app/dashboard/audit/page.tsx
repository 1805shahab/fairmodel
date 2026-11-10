"use client";
import {
  Badge,
  Empty,
  ErrorPanel,
  Loading,
  PageHeading,
  useData,
} from "@/components/ui";
import type { Audit } from "@/components/types";
export default function AuditPage() {
  const { data, error, loading, retry } = useData<Audit[]>("/audit");
  return (
    <>
      <PageHeading
        eyebrow="ACCOUNTABILITY, BUILT IN"
        title="Audit trail"
        description="Contract decisions, audio processing, artist reviews and provider-labeled payment events."
      />
      {error && <ErrorPanel message={error} retry={retry} />}
      <section className="panel">
        {loading ? (
          <Loading />
        ) : !data?.length ? (
          <Empty
            title="A clean slate"
            description="Workflow actions will appear here as you create agreements and submit audio."
          />
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>EVENT</th>
                  <th>RECORD</th>
                  <th>TIME · PKT</th>
                  <th>DETAILS</th>
                </tr>
              </thead>
              <tbody>
                {data.map((x) => (
                  <tr key={x.id}>
                    <td>
                      <strong>{x.action.replaceAll("_", " ")}</strong>
                    </td>
                    <td className="mono">{x.entity_id.slice(0, 10)}</td>
                    <td className="nowrap muted">
                      {new Date(x.created_at).toLocaleString("en", {
                        timeZone: "Asia/Karachi",
                      })}
                    </td>
                    <td>
                      {Object.keys(x.detail).length ? (
                        <details>
                          <summary>Evidence & context</summary>
                          <pre className="audit-json">
                            {JSON.stringify(x.detail, null, 2)}
                          </pre>
                        </details>
                      ) : (
                        <Badge status="RECORDED" />
                      )}
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
