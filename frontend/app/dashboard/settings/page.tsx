"use client";
import { useState } from "react";
import Link from "next/link";
import {
  AudioLines,
  Download,
  KeyRound,
  PlugZap,
  ShieldCheck,
} from "lucide-react";
import {
  BusyButton,
  ErrorPanel,
  Loading,
  PageHeading,
  useAction,
  useData,
} from "@/components/ui";
import { endpoint, PAYMENT_NOTICE, post } from "@/components/api";
import { PaymentModeNotice } from "@/components/invoice-actions";
import type { Integrations } from "@/components/types";
export default function Settings() {
  const [diagnostic, setDiagnostic] = useState<Record<
    string,
    string | boolean | number | null
  > | null>(null);
  const action = useAction();
  const { data, error, loading, retry } =
    useData<Integrations>("/integrations");
  return (
    <>
      <PageHeading
        eyebrow="AN HONEST VIEW OF THE STACK"
        title="Settings & integrations"
        description="Know what is connected, what is simulated, and what needs configuration."
      />
      {error && <ErrorPanel message={error} retry={retry} />}{" "}
      {loading ? (
        <Loading />
      ) : (
        data && (
          <>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Provider status</h2>
                  <p>
                    Keys remain on the backend. Values are never returned to the
                    browser.
                  </p>
                </div>
                <PlugZap size={20} />
              </div>
              <div className="integration-list">
                {[
                  {
                    name: "Gemini contract & content intelligence",
                    text: data.gemini.model,
                    ready: data.gemini.configured,
                    status: data.gemini.configured
                      ? "Configured · live call not implied"
                      : "Key not configured",
                  },
                  {
                    name: "Groq speech transcription",
                    text: data.groq.model,
                    ready: data.groq.configured,
                    status: data.groq.configured
                      ? "Configured · live call not implied"
                      : "Key not configured",
                  },
                  {
                    name: "FFmpeg & ffprobe",
                    text: "Local decoding, validation and normalization",
                    ready: data.audio_tools.ffmpeg && data.audio_tools.ffprobe,
                    status:
                      data.audio_tools.ffmpeg && data.audio_tools.ffprobe
                        ? "Available"
                        : "Missing local tools",
                  },
                  {
                    name: "Local mock payment provider",
                    text: PAYMENT_NOTICE,
                    ready: false,
                    status:
                      data.payment_provider === "mock"
                        ? "Active · simulated"
                        : "Offline testing only",
                  },
                  {
                    name: "PayPal Sandbox",
                    text: data.paypal,
                    ready: diagnostic?.sandbox_authentication === "SUCCESS",
                    status:
                      diagnostic?.sandbox_authentication === "SUCCESS"
                        ? "OAuth verified"
                        : "Not yet verified",
                  },
                  {
                    name: "Experimental speaker verification",
                    text: "Separate optional worker. Core application never downloads speaker models.",
                    ready: false,
                    status: data.speaker_verification.status,
                  },
                ].map((x) => (
                  <article key={x.name}>
                    <span className="file-icon">
                      <KeyRound size={19} />
                    </span>
                    <div>
                      <strong>{x.name}</strong>
                      <p>{x.text}</p>
                    </div>
                    <span className={`pill ${x.ready ? "green" : "amber"}`}>
                      {x.status}
                    </span>
                  </article>
                ))}
              </div>
            </section>
            <section className="panel compact-panel">
              <h2>Sponsor integrations</h2>
              <p>
                These tools support this application&apos;s payment integration,
                analytics and API testing. They do not create separate
                applications.
              </p>
              <div className="integration-list">
                <article>
                  <div>
                    <strong>APIMatic PayPal Context Plugin</strong>
                    <p>
                      Developer guidance used for Sandbox authentication, safe
                      errors, retries and integration tests. Invoicing v2 uses
                      the official PayPal REST API through HTTPX; the plugin is
                      not a runtime payment service.
                    </p>
                  </div>
                </article>
                <article>
                  <div>
                    <strong>AG Grid Community</strong>
                    <p>
                      Explore actual royalty records with filters, sorting and
                      CSV export.
                    </p>
                    <Link className="text-link" href="/dashboard/analytics">
                      Open royalty analytics
                    </Link>
                  </div>
                </article>
                <article>
                  <div>
                    <strong>Postman API testing</strong>
                    <p>
                      Import the guarded collection into Postman. It contains
                      placeholders and skips write requests by default. No
                      credentials are included; exporting it does not prove a
                      Postman run.
                    </p>
                    <a className="text-link" href="/api/tools/postman" download>
                      Download Postman collection
                    </a>
                  </div>
                </article>
              </div>
            </section>
            <section className="panel compact-panel">
              <h2>PayPal Sandbox connection diagnostic</h2>
              <PaymentModeNotice />
              <p>
                This checks OAuth and reads invoice capability. It never creates
                or sends invoices. Existing mock invoices keep their provider.
              </p>
              <p className="small">
                Selected provider: {data.payment_provider || "mock"}. Sandbox
                merchant:{" "}
                {data.paypal_configuration?.merchant_configured
                  ? "configured"
                  : "not configured"}
                ; buyer:{" "}
                {data.paypal_configuration?.buyer_configured
                  ? "configured"
                  : "not configured"}
                ; drafts:{" "}
                {data.paypal_configuration?.drafts_enabled
                  ? "enabled for confirmed actions"
                  : "disabled"}
                ; sending:{" "}
                {data.paypal_configuration?.sending_enabled
                  ? "enabled for confirmed actions"
                  : "disabled"}
                .
              </p>
              <BusyButton
                busy={action.busy}
                onClick={() =>
                  void action.run(async () => {
                    setDiagnostic(
                      await post<
                        Record<string, string | boolean | number | null>
                      >("/paypal/diagnostic"),
                    );
                  })
                }
              >
                Test Sandbox connection (read-only)
              </BusyButton>
              {diagnostic && (
                <dl className="calculation-details">
                  {Object.entries(diagnostic).map(([key, value]) => (
                    <div key={key}>
                      <dt>{key.replaceAll("_", " ")}</dt>
                      <dd>{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              )}
              {action.error && <ErrorPanel message={action.error} />}
            </section>
            <div className="dashboard-columns lower-grid">
              <details className="panel compact-panel">
                <summary>Offline testing tools</summary>
                <Download size={24} className="blue-text" />
                <h2>Local fixture workflow</h2>
                <p>
                  Download both fixtures, create and approve a license, then
                  submit the narration as the studio. Explicitly enable fixture
                  mode for each AI processing step.
                </p>
                <div className="button-row">
                  <a
                    className="button secondary"
                    href={endpoint("/demo/fixtures/contract")}
                    download
                  >
                    Sample contract
                  </a>
                  <a
                    className="button secondary"
                    href={endpoint("/demo/fixtures/audio")}
                    download
                  >
                    <AudioLines size={15} />
                    Sample audio
                  </a>
                </div>
                <p className="small">
                  {data.fixtures_available
                    ? "Fixtures generated locally and ready. They are not live Gemini/Groq results."
                    : "Run ./scripts/create-demo.ps1 in PowerShell to generate fixtures."}
                </p>
              </details>
              <section className="panel compact-panel">
                <ShieldCheck size={24} className="blue-text" />
                <h2>Local role access & privacy</h2>
                <p>
                  The role switcher selects fixed local personas. Anyone with
                  local API access can select either persona. This is not
                  production authentication.
                </p>
                <p className="small">
                  Resource services enforce assigned ownership. Uploads are
                  served through access-checked endpoints and are excluded from
                  Git. Run both servers on loopback only.
                </p>
              </section>
            </div>
          </>
        )
      )}
    </>
  );
}
