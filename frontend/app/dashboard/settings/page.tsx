"use client";
import {
  AudioLines,
  Download,
  KeyRound,
  PlugZap,
  ShieldCheck,
} from "lucide-react";
import { ErrorPanel, Loading, PageHeading, useData } from "@/components/ui";
import { endpoint, PAYMENT_NOTICE } from "@/components/api";
import type { Integrations } from "@/components/types";
export default function Settings() {
  const { data, error, loading, retry } =
    useData<Integrations>("/integrations");
  return (
    <>
      <PageHeading
        eyebrow="AN HONEST VIEW OF THE STACK"
        title="Demo & integrations"
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
                    ready: true,
                    status: "Simulated only",
                  },
                  {
                    name: "PayPal Sandbox",
                    text: data.paypal,
                    ready: false,
                    status: "Intentionally deferred",
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
            <div className="dashboard-columns lower-grid">
              <section className="panel compact-panel">
                <Download size={24} className="blue-text" />
                <h2>Try the local fixture workflow</h2>
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
              </section>
              <section className="panel compact-panel">
                <ShieldCheck size={24} className="blue-text" />
                <h2>Demo identity & privacy</h2>
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
