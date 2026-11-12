"use client";
import Link from "next/link";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import CampaignForm, { emptyCampaign } from "@/components/campaign-form";
import { api, date } from "@/components/api";
import {
  BusyButton,
  ErrorPanel,
  Field,
  PageHeading,
  useAction,
  useData,
} from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import type {
  SpeechGeneration,
  VoiceGrant,
} from "@/components/voice-generation-types";

export default function GenerateAdvertisement() {
  const { role } = useWorkspace();
  return (
    <>
      <PageHeading
        eyebrow="CREATE WITH LICENSED CONSENT"
        title="Generate advertisement"
        description="Select a provider and the artist’s permission, then generate your script. Audio analysis and artist review follow."
      />
      {role !== "studio" ? (
        <div className="alert info">
          <span>
            Artists first{" "}
            <Link href="/dashboard/references">
              upload their reference and consent recordings
            </Link>
            , approve a contract and grant studio generation. Switch to Studio
            to create an advertisement.
          </span>
        </div>
      ) : (
        <StudioGeneration />
      )}
    </>
  );
}

function StudioGeneration() {
  const router = useRouter();
  const grants = useData<VoiceGrant[]>("/voice-grants");
  const jobs = useData<SpeechGeneration[]>("/generations");
  const integration = useData<{
    voice_generation: {
      enabled: boolean;
      configured: boolean;
      model: string;
      replication_model: string;
      access_note: string;
      fish?: {
        enabled: boolean;
        configured: boolean;
        model: string;
        access_note: string;
      };
    };
  }>("/integrations");
  const [grantId, setGrantId] = useState("");
  const [script, setScript] = useState("");
  const [campaign, setCampaign] = useState(emptyCampaign);
  const [confirmed, setConfirmed] = useState(false);
  const [provider, setProvider] = useState<"gemini" | "fish">("gemini");
  const request = useRef<{ signature: string; key: string } | null>(null);
  const { busy, error, run } = useAction();
  const active =
    grants.data?.filter(
      (x) => x.status === "ACTIVE" && (x.provider || "gemini") === provider,
    ) || [];
  const available = integration.data?.voice_generation;
  const selectedProvider = provider === "fish" ? available?.fish : available;
  return (
    <>
      <div className="alert info">
        <span>
          The selected provider uses the artist’s consented reference voice, not
          a prebuilt replacement. Generated audio is uploaded for separate live
          Groq/VAD analysis, Gemini compliance and final artist authorization.
          No charge or invoice is created here.
        </span>
      </div>
      {available &&
        (!selectedProvider?.enabled || !selectedProvider.configured) && (
          <div className="alert warning">
            <span>
              {provider === "gemini" ? (
                <>
                  Generation is not enabled/configured. Set
                  ENABLE_VOICE_GENERATION=true in backend/.env, keep the
                  existing server-only Gemini key, and restart the backend.
                  Gemini replication requires paid-tier access; enabling the
                  flag does not prove account access.
                </>
              ) : (
                <>
                  Generation is not enabled/configured for Fish. Set
                  ENABLE_VOICE_GENERATION=true, ENABLE_FISH_GENERATION=true and
                  FISH_API_KEY in backend/.env, then restart. Only s2.1-pro-free
                  is allowed; configured status does not prove live access.
                </>
              )}
            </span>
          </div>
        )}
      {grants.error && (
        <ErrorPanel message={grants.error} retry={grants.retry} />
      )}
      {integration.error && (
        <ErrorPanel message={integration.error} retry={integration.retry} />
      )}
      {!grants.loading && !active.length && (
        <div className="alert warning">
          Your artist must upload authentic reference/consent recordings and
          grant generation for an approved license before you can generate.
        </div>
      )}
      <form
        className="panel form-panel"
        aria-busy={busy}
        onSubmit={(e) => {
          e.preventDefault();
          void run(async () => {
            const body = {
              provider,
              grant_id: grantId,
              script,
              campaign,
              confirm_provider_use: confirmed,
            };
            const signature = JSON.stringify(body);
            if (request.current?.signature !== signature)
              request.current = { signature, key: crypto.randomUUID() };
            try {
              const job = await api<SpeechGeneration>("/generations", {
                method: "POST",
                body: JSON.stringify({
                  ...body,
                  request_key: request.current.key,
                }),
              });
              if (job.status === "SUCCEEDED" && job.asset_id)
                router.push(`/dashboard/submissions/${job.asset_id}`);
              else
                throw new Error(
                  job.error ||
                    "Generation is still running or was interrupted. Inspect its saved history; this request will not automatically run again.",
                );
            } finally {
              jobs.retry();
            }
          }, "Generated audio saved. Run audio analysis and compliance on the recording page.");
        }}
      >
        <Field label="Voice generation provider">
          <select
            value={provider}
            disabled={busy}
            onChange={(e) => {
              setProvider(e.target.value as "gemini" | "fish");
              setGrantId("");
              setConfirmed(false);
              request.current = null;
            }}
          >
            <option value="gemini">Google Gemini</option>
            <option value="fish">
              Fish Audio · s2.1-pro-free · inline cloning
            </option>
          </select>
        </Field>
        <Field label="Artist-approved voice and license">
          <select
            required
            value={grantId}
            onChange={(e) => setGrantId(e.target.value)}
          >
            <option value="">Choose a current artist grant</option>
            {active.map((x) => (
              <option key={x.id} value={x.id}>
                {x.license_title} · v{x.license_version} · reference{" "}
                {x.reference_id.slice(0, 8)}
              </option>
            ))}
          </select>
        </Field>
        <Field
          label="Advertisement script"
          hint="10–4,000 characters. The script is sent as text to Gemini. Output duration is measured after generation; text length does not set billable seconds."
        >
          <textarea
            required
            minLength={10}
            maxLength={4000}
            rows={9}
            value={script}
            onChange={(e) => setScript(e.target.value)}
            placeholder="Write an original advertisement permitted by the agreement."
          />
        </Field>
        <CampaignForm value={campaign} onChange={setCampaign} />
        {provider === "gemini" && available && (
          <p className="small">
            Voice replication: {available.replication_model}. Speech synthesis:{" "}
            {available.model}. These configured models are not proof of provider
            access. No model is substituted automatically after a rejection.
          </p>
        )}
        {provider === "fish" && (
          <p className="small">
            Fish Audio · s2.1-pro-free only · inline reference cloning. No
            reusable profile is created. Fair-use limits and provider retention
            apply; no DPA or zero-retention guarantee. Identity is not
            independently verified. There is no automatic provider/model
            fallback.
          </p>
        )}
        <label className="checkbox">
          <input
            required
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I request this {provider === "fish" ? "Fish Audio" : "Gemini"} voice
          replication and speech-generation operation using the artist’s
          provider-specific grant.{" "}
          {provider === "fish"
            ? "Only the documented free model is requested, subject to fair-use limits and provider terms."
            : "It may consume paid API quota."}
          This does not authorize a royalty invoice.
        </label>
        {error && <ErrorPanel message={error} />}
        {busy && (
          <p role="status">
            The selected provider is processing the permitted inputs and
            generating the advertisement. Keep this page open; do not start
            another request.
          </p>
        )}
        <div className="form-footer">
          <BusyButton
            busy={busy}
            disabled={
              !selectedProvider?.enabled ||
              !selectedProvider.configured ||
              !active.length
            }
          >
            Generate with licensed artist voice
          </BusyButton>
          <button
            className="button secondary"
            type="button"
            disabled={busy}
            onClick={() => {
              request.current = null;
            }}
          >
            Start a new generation request
          </button>
        </div>
        <p className="small">
          Retries reuse the same request key. A failed/interrupted request is
          not automatically rerun; a new request is a separate provider
          operation.
        </p>
      </form>
      <section className="panel compact-panel">
        <h2>Generation history</h2>
        {jobs.error && <ErrorPanel message={jobs.error} retry={jobs.retry} />}
        {!jobs.data?.length && (
          <p className="muted">No generated advertisements yet.</p>
        )}
        {jobs.data?.map((job) => (
          <article key={job.id} className="form-section-title">
            <div>
              <h3>
                {job.status} · {date(job.created_at)}
              </h3>
              <p>
                {job.receipt.service ||
                  (job.provider === "fish"
                    ? "Fish Audio request"
                    : "Gemini TTS request")}
                {job.receipt.succeeded_at && job.receipt.mode === "live"
                  ? " · live response saved"
                  : " · no successful result recorded"}
              </p>
              {job.error && <p>{job.error}</p>}
              {job.receipt.requested_replication_model && (
                <p className="small">
                  Requested replication:{" "}
                  {job.receipt.requested_replication_model}. Requested
                  synthesis: {job.receipt.requested_model}.
                </p>
              )}
              {job.receipt.requested_model &&
                !job.receipt.requested_replication_model && (
                  <p className="small">
                    Requested model: {job.receipt.requested_model}.
                  </p>
                )}
              {job.asset_id && (
                <Link
                  className="button secondary"
                  href={`/dashboard/submissions/${job.asset_id}`}
                >
                  Open recording and analyze
                </Link>
              )}
            </div>
          </article>
        ))}
      </section>
    </>
  );
}
