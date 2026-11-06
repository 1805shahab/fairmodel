"use client";
import { useState } from "react";
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
import { api, date } from "@/components/api";
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
        description="Store a consented reference for future experimental speaker comparison."
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
        Experimental speaker verification is optional. Uploading a reference
        does not run a model or produce a similarity score.
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
            <h2>Your approved recording</h2>
            <p>Only upload a voice you own or have permission to use.</p>
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
            <div className="reference-row" key={x.id}>
              <Mic2 size={18} />
              <span>{date(x.created_at)}</span>
              <strong>{x.metadata_json.duration_seconds}s</strong>
              <span className="pill green">Consent recorded</span>
            </div>
          ))
        ) : (
          <p className="muted">No recordings uploaded yet.</p>
        )}
      </section>
    </>
  );
}
