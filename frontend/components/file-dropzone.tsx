"use client";

import { useId, useRef, useState } from "react";
import { FileCheck2, Upload } from "lucide-react";

/** Client convenience validation only; the backend validates the actual file content. */
export default function FileDropzone({
  label,
  accept,
  extensions,
  file,
  onChange,
  disabled,
  note,
}: {
  label: string;
  accept: string;
  extensions: string[];
  file: File | null;
  onChange: (file: File | null) => void;
  disabled?: boolean;
  note: string;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const descriptionId = useId();
  function validate(files: FileList | null) {
    const selected = files?.[0];
    const invalid =
      files && files.length > 1
        ? "Choose one file at a time."
        : selected &&
            !extensions.some((extension) =>
              selected.name.toLowerCase().endsWith(extension),
            )
          ? `Choose ${extensions.join(", ")} files only.`
          : selected && selected.size > 24 * 1024 * 1024
            ? "File exceeds 24 MiB. Choose a smaller file."
            : "";
    setError(invalid);
    if (invalid) {
      onChange(null);
      if (input.current) input.current.value = "";
      return;
    }
    onChange(selected || null);
  }
  return (
    <span
      className={`file-dropzone ${dragging ? "is-dragging" : ""} ${file ? "has-file" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node))
          setDragging(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        if (disabled) return;
        validate(e.dataTransfer.files);
        // Preserve native required-file validation for drag and keyboard selection alike.
        if (
          input.current &&
          e.dataTransfer.files.length === 1 &&
          extensions.some((x) =>
            e.dataTransfer.files[0].name.toLowerCase().endsWith(x),
          ) &&
          e.dataTransfer.files[0].size <= 24 * 1024 * 1024
        )
          input.current.files = e.dataTransfer.files;
      }}
    >
      {file ? (
        <FileCheck2 size={28} aria-hidden="true" />
      ) : (
        <Upload size={28} aria-hidden="true" />
      )}
      <strong>{file?.name || "Drop a file here, or browse"}</strong>
      <span id={descriptionId}>
        {file
          ? `${(file.size / (1024 * 1024)).toFixed(2)} MiB · choose another file to replace`
          : note}
      </span>
      <input
        ref={input}
        aria-label={label}
        aria-describedby={descriptionId}
        aria-invalid={!!error}
        type="file"
        accept={accept}
        required
        disabled={disabled}
        onChange={(e) => validate(e.target.files)}
      />
      {error && (
        <span className="file-error" role="alert">
          {error}
        </span>
      )}
    </span>
  );
}
