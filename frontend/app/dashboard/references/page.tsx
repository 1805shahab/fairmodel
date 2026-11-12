"use client";
import { useState } from "react";
import Link from "next/link";
import { Mic2 } from "lucide-react";
import {
  BusyButton,
  ErrorPanel,
  Field,
  PageHeading,
  useAction,
  useData,
} from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, date, endpoint, post } from "@/components/api";
import type { License } from "@/components/types";
import type { VoiceGrant } from "@/components/voice-generation-types";
interface Reference {
  id: string;
  created_at: string;
  metadata_json: { duration_seconds: string; format: string };
  consent: boolean;
}
export default function References() {
  const { role } = useWorkspace();
  return (
    <>
      <PageHeading
        eyebrow="CONSENT COMES FIRST"
        title="Reference voice"
        description="Start with your own sample, approve a contract, then explicitly authorize studio voice generation."
      />
      {role === "artist" ? (
        <ArtistReferences />
      ) : (
        <div className="alert info">
          Reference voice management is available to the artist persona.
        </div>
      )}
    </>
  );
}
function ArtistReferences() {
  const [file, setFile] = useState<File | null>(null),
    [consent, setConsent] = useState(false);
  const { busy, error, run } = useAction();
  const refs = useData<Reference[]>("/references");
  return (
    <>
      <div className="alert warning">
        Uploading a sample records storage/comparison consent only. Voice
        replication needs a separate artist grant for the selected provider
        below. Optional speaker verification remains separate.
      </div>
      <form
        className="panel form-panel"
        onSubmit={(e) => {
          e.preventDefault();
          void run(async () => {
            if (!file) throw new Error("Choose a consented recording.");
            const body = new FormData();
            body.set("consent", String(consent));
            body.set("file", file);
            await api("/references", { method: "POST", body });
            setFile(null);
          }, "Consented reference stored privately.");
        }}
      >
        <div className="form-section-title">
          <Mic2 size={23} />
          <div>
            <h2>1. Upload your reference recording</h2>
            <p>
              For Gemini replication, use 10–30 seconds of clean, natural speech
              from the consenting adult speaker.
            </p>
          </div>
        </div>
        <Field label="Reference recording">
          <input
            aria-label="Reference recording"
            type="file"
            required
            accept=".wav,.mp3,.m4a"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </Field>
        <label className="checkbox">
          <input
            type="checkbox"
            required
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
          />
          I have permission to store and compare this recording for voice
          verification.
        </label>
        {error && <ErrorPanel message={error} />}
        <BusyButton busy={busy} disabled={!consent}>
          Upload consented reference
        </BusyButton>
      </form>
      {refs.error && <ErrorPanel message={refs.error} retry={refs.retry} />}
      <section className="panel compact-panel">
        <h2>Stored references</h2>
        {refs.data?.length ? (
          refs.data.map((x) => (
            <article key={x.id}>
              <div className="reference-row">
                <Mic2 size={18} />
                <span>{date(x.created_at)}</span>
                <strong>{x.metadata_json.duration_seconds}s</strong>
                <span className="pill green">Consent recorded</span>
              </div>
              <audio
                controls
                preload="none"
                aria-label={`Reference uploaded ${date(x.created_at)}`}
                src={endpoint(`/references/${x.id}/audio`)}
                style={{ width: "100%" }}
              />
            </article>
          ))
        ) : (
          <p className="muted">No recordings uploaded yet.</p>
        )}
      </section>
      <section className="panel compact-panel">
        <h2>2. Upload and approve your contract</h2>
        <p>
          Gemini extracts terms from the PDF. Review the actual clauses and
          approve the agreement before granting studio generation.
        </p>
        <Link className="button secondary" href="/dashboard/licenses/new">
          Upload licensing contract
        </Link>
      </section>
      <GenerationPermission references={refs.data || []} />
    </>
  );
}

const CONSENT =
  "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model.";
function eligibleReference(reference: Reference) {
  const seconds = Number(reference.metadata_json.duration_seconds);
  return Number.isFinite(seconds) && seconds >= 10 && seconds <= 30;
}
function GenerationPermission({ references }: { references: Reference[] }) {
  const licenses = useData<License[]>("/licenses");
  const grants = useData<VoiceGrant[]>("/voice-grants");
  const { busy, error, run } = useAction();
  const [referenceId, setReferenceId] = useState("");
  const [licenseId, setLicenseId] = useState("");
  const [consentFile, setConsentFile] = useState<File | null>(null);
  const [owner, setOwner] = useState(false);
  const [transfer, setTransfer] = useState(false);
  const [note, setNote] = useState("");
  const [provider, setProvider] = useState<"gemini" | "fish">("gemini");
  const [referenceText, setReferenceText] = useState("");
  const [policy, setPolicy] = useState(false);
  return (
    <>
      <form
        className="panel form-panel"
        aria-busy={busy}
        onSubmit={(event) => {
          event.preventDefault();
          void run(async () => {
            const selected = references.find((x) => x.id === referenceId);
            if (!selected || !eligibleReference(selected))
              throw new Error(
                "Choose a 10–30 second artist reference sample. This is separate from the shorter consent recording.",
              );
            if (provider === "gemini" && !consentFile)
              throw new Error(
                "Choose the speaker's separate consent recording.",
              );
            const body = new FormData();
            body.set("reference_id", referenceId);
            body.set("license_id", licenseId);
            body.set("owner_confirmed", String(owner));
            body.set("provider_transfer_consent", String(transfer));
            body.set("note", note);
            body.set("provider", provider);
            body.set("reference_text", referenceText);
            body.set("provider_policy_ack", String(policy));
            if (provider === "gemini" && consentFile)
              body.set("file", consentFile);
            await api("/voice-grants", { method: "POST", body });
          }, "Studio generation grant saved for this approved license version.");
        }}
      >
        <h2>3. Authorize your licensed voice for generation</h2>
        <p>
          This grants the assigned studio access to generation under one
          approved agreement. It does not approve a finished advertisement or
          royalty charge.
        </p>
        <Field label="Voice generation provider">
          <select
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value as "gemini" | "fish");
              setOwner(false);
              setTransfer(false);
              setPolicy(false);
            }}
          >
            <option value="gemini">Google Gemini</option>
            <option value="fish">
              Fish Audio · s2.1-pro-free · inline cloning
            </option>
          </select>
        </Field>
        <Field
          label="Artist reference sample"
          hint="Choose 10–30 seconds of natural speech, not necessarily the consent statement. Out-of-range samples remain stored but cannot be used for Gemini replication."
        >
          <select
            required
            value={referenceId}
            onChange={(e) => setReferenceId(e.target.value)}
          >
            <option value="">Choose your sample</option>
            {references.map((x) => (
              <option key={x.id} value={x.id} disabled={!eligibleReference(x)}>
                {date(x.created_at)} · {x.metadata_json.duration_seconds}s ·{" "}
                {x.id.slice(0, 8)}
                {!eligibleReference(x) ? " — needs a 10–30s reference" : ""}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Approved agreement">
          <select
            required
            value={licenseId}
            onChange={(e) => setLicenseId(e.target.value)}
          >
            <option value="">Choose an active license</option>
            {licenses.data
              ?.filter((x) => x.status === "ACTIVE")
              .map((x) => (
                <option key={x.id} value={x.id}>
                  {x.title} · version {x.version}
                </option>
              ))}
          </select>
        </Field>
        {provider === "gemini" ? (
          <>
            <div className="alert info">
              <span>
                The same adult speaker must record this exact statement in
                English: <strong>{CONSENT}</strong> Use a separate 2–30 second
                human recording, with no music. Google checks the reference and
                consent during replication; synthetic demo fixtures are not
                eligible.
              </span>
            </div>
            <Field
              label="Speaker consent recording"
              hint="Read only the consent statement naturally. FairModel accepts 2–30 seconds; you do not need to fill 30 seconds or add silence."
            >
              <input
                type="file"
                required
                accept=".wav,.mp3,.m4a"
                onChange={(e) => setConsentFile(e.target.files?.[0] || null)}
              />
            </Field>
          </>
        ) : (
          <>
            <div className="alert warning">
              Fish receives your reference recording, its transcript and studio
              scripts. FairModel requests inline cloning and creates no reusable
              Fish voice profile. The free model has no DPA guarantee or
              verified zero-retention promise. Provider retention and usage
              terms apply. This permission is a manual attestation, not
              independent identity verification.
            </div>
            <Field
              label="Exact reference transcript"
              hint="Write the words actually spoken in your selected sample. This is reference context, not the advertisement script or a verified transcription."
            >
              <textarea
                required
                maxLength={4000}
                rows={4}
                value={referenceText}
                onChange={(e) => setReferenceText(e.target.value)}
              />
            </Field>
            <label className="checkbox">
              <input
                type="checkbox"
                required
                checked={policy}
                onChange={(e) => setPolicy(e.target.checked)}
              />
              <span>
                I reviewed{" "}
                <a href="https://fish.audio/privacy/">Fish privacy</a> and{" "}
                <a href="https://fish.audio/terms/">usage terms</a>, acknowledge
                provider retention and no DPA guarantee, and confirm this
                transcript matches my sample.
              </span>
            </label>
          </>
        )}
        <label className="checkbox">
          <input
            type="checkbox"
            required
            checked={owner}
            onChange={(e) => setOwner(e.target.checked)}
          />
          I am the adult voice owner or have the adult speaker’s explicit
          permission for this licensed replication; the submitted recordings are
          authentic and from that speaker.
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            required
            checked={transfer}
            onChange={(e) => setTransfer(e.target.checked)}
          />
          {provider === "gemini" ? (
            <>
              I authorize sending these reference and consent recordings to
              Google Gemini and allowing the assigned studio to generate
              licensed advertisements. Google’s provider processing terms apply;
              FairModel requests stateless voice replication.
            </>
          ) : (
            <>
              I explicitly authorize sending my reference recording and its
              transcript to Fish Audio for third-party processing and permit the
              assigned studio to generate speech under this approved license.
              This does not authorize Google processing or approve a final
              advertisement.
            </>
          )}
        </label>
        <Field label="Generation permission note">
          <textarea
            required
            minLength={10}
            maxLength={2000}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Identify the consenting speaker and the permitted studio use."
          />
        </Field>
        {licenses.error && (
          <ErrorPanel message={licenses.error} retry={licenses.retry} />
        )}
        {error && <ErrorPanel message={error} />}
        <BusyButton busy={busy}>Grant licensed studio generation</BusyButton>
      </form>
      <section className="panel compact-panel">
        <h2>Recorded generation permissions</h2>
        {grants.error && (
          <ErrorPanel message={grants.error} retry={grants.retry} />
        )}
        {!grants.data?.length && (
          <p className="muted">
            No voice has been authorized for studio generation yet.
          </p>
        )}
        {grants.data?.map((grant) => (
          <article key={grant.id} className="form-section-title">
            <div>
              <h3>
                {grant.license_title} · v{grant.license_version}
              </h3>
              <p>
                {grant.provider === "fish" ? "Fish Audio" : "Google Gemini"} ·{" "}
                {grant.status} · {date(grant.created_at)}
              </p>
              <p>{grant.note}</p>
              {grant.status === "ACTIVE" && (
                <BusyButton
                  busy={busy}
                  className="button secondary"
                  type="button"
                  onClick={() =>
                    void run(async () => {
                      await post(`/voice-grants/${grant.id}/revoke`);
                    }, "Future voice generation revoked; existing history preserved.")
                  }
                >
                  Revoke future generation
                </BusyButton>
              )}
            </div>
          </article>
        ))}
      </section>
    </>
  );
}
