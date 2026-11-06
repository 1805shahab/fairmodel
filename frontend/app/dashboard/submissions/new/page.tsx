"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Upload } from "lucide-react";
import {
  BusyButton,
  ErrorPanel,
  Field,
  PageHeading,
  useAction,
  useData,
} from "@/components/ui";
import { useWorkspace } from "@/components/workspace";
import { api, endpoint } from "@/components/api";
import CampaignForm, { emptyCampaign } from "@/components/campaign-form";
import type { Asset, License } from "@/components/types";
export default function NewSubmission() {
  const { role } = useWorkspace(),
    router = useRouter();
  const licenses = useData<License[]>("/licenses");
  const [licenseId, setLicenseId] = useState(""),
    [campaign, setCampaign] = useState(emptyCampaign),
    [file, setFile] = useState<File | null>(null);
  const { busy, error, run } = useAction();
  return (
    <>
      <PageHeading
        eyebrow="CREATE WITH PERMISSION"
        title="Submit audio"
        description="Connect your campaign to an approved license. We’ll measure speech and review the usage."
      />
      {role !== "studio" ? (
        <ErrorPanel message="Switch to Studio view to upload a campaign asset." />
      ) : (
        <form
          className="panel form-panel"
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              if (!file) throw new Error("Choose a WAV, MP3 or M4A file.");
              if (file.size > 24 * 1024 * 1024)
                throw new Error("File exceeds 24 MiB.");
              const body = new FormData();
              body.set("license_id", licenseId);
              body.set("campaign", JSON.stringify(campaign));
              body.set("file", file);
              const asset = await api<Asset & { duplicate?: boolean }>(
                "/assets",
                { method: "POST", body },
              );
              router.push(`/dashboard/submissions/${asset.id}`);
            }, "Audio ready for analysis. Exact duplicate uploads return the existing asset.");
          }}
        >
          <Field label="Approved voice license">
            <select
              required
              value={licenseId}
              onChange={(e) => setLicenseId(e.target.value)}
            >
              <option value="">Select an active agreement</option>
              {licenses.data
                ?.filter((x) => x.status === "ACTIVE")
                .map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.title}
                  </option>
                ))}
            </select>
          </Field>
          {licenses.error && (
            <ErrorPanel message={licenses.error} retry={licenses.retry} />
          )}
          <CampaignForm value={campaign} onChange={setCampaign} />
          <Field
            label="Campaign audio"
            hint="WAV, MP3, M4A · 24 MiB max · 10 minutes max · single speaker and audio track."
          >
            <span className="upload-zone">
              <Upload size={25} />
              <strong>{file?.name || "Choose campaign audio"}</strong>
              <span>File content is validated with ffprobe.</span>
              <input
                aria-label="Campaign audio"
                type="file"
                accept=".wav,.mp3,.m4a"
                required
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </span>
          </Field>
          <div className="alert info">
            <span>
              For the local demo,{" "}
              <a href={endpoint("/demo/fixtures/audio")} download>
                download our synthetic narration
              </a>
              . Use US, online advertising, English and consumer products with
              the sample license. Audio cannot verify distribution geography.
            </span>
          </div>
          {error && <ErrorPanel message={error} />}
          <div className="form-footer">
            <span className="small">Analysis runs after upload.</span>
            <BusyButton busy={busy}>
              Upload audio <ArrowRight size={16} />
            </BusyButton>
          </div>
        </form>
      )}
    </>
  );
}
