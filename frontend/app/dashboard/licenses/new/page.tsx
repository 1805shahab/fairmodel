"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, FileText, Upload } from "lucide-react";
import {
  BusyButton,
  ErrorPanel,
  Field,
  PageHeading,
  useAction,
} from "@/components/ui";
import { api, endpoint, post } from "@/components/api";
import { useWorkspace } from "@/components/workspace";
import type { License } from "@/components/types";

export default function NewLicense() {
  const router = useRouter();
  const { role } = useWorkspace();
  const [title, setTitle] = useState(""),
    [file, setFile] = useState<File | null>(null),
    [createdId, setCreatedId] = useState<string | null>(null);
  const { busy, error, run } = useAction();
  return (
    <>
      <PageHeading
        eyebrow="START A FAIR COLLABORATION"
        title="New voice license"
        description="Upload your agreement. Extract the terms. Review every rule before it goes live."
      />
      {role !== "artist" ? (
        <ErrorPanel message="Switch to Artist view to create an agreement." />
      ) : (
        <form
          className="panel form-panel"
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              if (!file) throw new Error("Choose a PDF contract.");
              const license = createdId
                ? { id: createdId }
                : await post<License>("/licenses", {
                    title,
                    studio_id: "studio_demo",
                  });
              setCreatedId(license.id);
              const body = new FormData();
              body.set("file", file);
              await api(`/licenses/${license.id}/contract`, {
                method: "POST",
                body,
              });
              router.push(`/dashboard/licenses/${license.id}`);
            }, "Contract uploaded. Review extraction options.");
          }}
        >
          <div className="form-section-title">
            <span className="file-icon">
              <FileText size={22} />
            </span>
            <div>
              <h2>Agreement details</h2>
              <p>Private to the assigned demo personas.</p>
            </div>
          </div>
          <Field label="Agreement name">
            <input
              required
              minLength={3}
              maxLength={160}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Northstar · Online voice campaign"
              disabled={!!createdId}
            />
          </Field>
          <Field label="Assigned production studio">
            <select disabled>
              <option>Northstar Studio · studio@example.test</option>
            </select>
          </Field>
          <Field
            label="Licensing agreement PDF"
            hint="Text PDF · up to 30 pages · 24 MiB max. Scanned PDFs require OCR."
          >
            <span className="upload-zone">
              <Upload size={26} />
              <strong>{file?.name || "Choose a licensing agreement"}</strong>
              <span>Source pages are preserved for your review.</span>
              <input
                aria-label="Licensing agreement PDF"
                type="file"
                accept=".pdf,application/pdf"
                required
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </span>
          </Field>
          <div className="alert info">
            Trying the local workflow?{" "}
            <a href={endpoint("/demo/fixtures/contract")} download>
              Download our sample PDF
            </a>
            . Demo extraction only works with this exact file.
          </div>
          {createdId && (
            <p className="muted">
              Draft saved. You can retry this upload without creating another
              license.
            </p>
          )}
          {error && <ErrorPanel message={error} />}
          <div className="form-footer">
            <span className="small">Nothing activates until you approve.</span>
            <BusyButton busy={busy}>
              Upload & continue <ArrowRight size={16} />
            </BusyButton>
          </div>
        </form>
      )}
    </>
  );
}
