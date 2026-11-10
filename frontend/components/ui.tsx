"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, FileAudio, LoaderCircle, RefreshCw } from "lucide-react";
import { api, statusLabel } from "./api";
import { useWorkspace } from "./workspace";

export function useData<T>(path: string) {
  const { revision } = useWorkspace();
  const [data, setData] = useState<T | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      try {
        const result = await api<T>(path);
        if (active) {
          setData(result);
          setError("");
        }
      } catch (e) {
        if (active)
          setError(e instanceof Error ? e.message : "Request failed.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [path, revision, attempt]);
  const retry = useCallback(() => setAttempt((x) => x + 1), []);
  return { data, error, loading, retry };
}
export function Badge({ status }: { status: string }) {
  const color = [
    "ACTIVE",
    "APPROVED",
    "COMPLIANT",
    "NO_CHARGE",
    "PAID_SIMULATED",
    "artist_confirmed",
    "ROYALTY_APPROVED",
    "PAID",
  ].includes(status)
    ? "green"
    : [
          "NEEDS_REVIEW",
          "PENDING",
          "REVIEW",
          "ADDITIONAL_ROYALTY_DUE",
          "SENT",
          "PAYMENT_PENDING",
          "PARTIALLY_PAID",
          "unresolved",
          "stale",
        ].includes(status)
      ? "amber"
      : ["RESTRICTED_USAGE", "FAILED", "REJECTED"].includes(status)
        ? "red"
        : ["ANALYZED", "PROCESSING", "UPLOADED", "DRAFT"].includes(status)
          ? "blue"
          : "slate";
  return (
    <span className={`pill ${color}`}>
      <span className="status-dot" />
      {statusLabel(status)}
    </span>
  );
}
export function PageHeading({
  eyebrow,
  title,
  description,
  action,
  className,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`page-heading ${className || ""}`.trim()}>
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}
export function ErrorPanel({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div className="alert error" role="alert">
      <strong>We couldn’t finish that request.</strong>
      <p>{message}</p>
      {retry && (
        <button className="button secondary small-button" onClick={retry}>
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  );
}
export function Loading() {
  return (
    <div className="loading loading-skeleton" role="status" aria-live="polite">
      <LoaderCircle className="spin" size={22} />
      Loading your workspace…
    </div>
  );
}
export function Empty({
  title,
  description,
  href,
  label,
}: {
  title: string;
  description: string;
  href?: string;
  label?: string;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <FileAudio size={27} />
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
      {href && (
        <Link className="button secondary" href={href}>
          {label || "Get started"}
          <ArrowRight size={15} />
        </Link>
      )}
    </div>
  );
}
export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <div className="field">
      <label>
        <span>{label}</span>
        {children}
      </label>
      {hint && <small>{hint}</small>}
    </div>
  );
}
export function BusyButton({
  busy,
  children,
  ...props
}: {
  busy: boolean;
  children: React.ReactNode;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      aria-busy={busy}
      disabled={busy || props.disabled}
      className={props.className || "button"}
    >
      {busy && <LoaderCircle size={15} className="spin" />}
      {children}
    </button>
  );
}
export function useAction() {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const { refresh, notify } = useWorkspace();
  async function run(action: () => Promise<void>, message?: string) {
    setBusy(true);
    setError("");
    try {
      await action();
      refresh();
      if (message) notify(message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed.");
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, run };
}
