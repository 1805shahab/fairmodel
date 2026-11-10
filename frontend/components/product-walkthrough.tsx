"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  AudioLines,
  FileCheck2,
  ListChecks,
  ReceiptText,
  ShieldCheck,
} from "lucide-react";

const stages = [
  {
    title: "Set the terms.",
    name: "License",
    Icon: FileCheck2,
    text: "Upload a PDF agreement. Gemini extracts structured terms with source clauses. The artist reviews them before activation.",
    evidence: "Source text → reviewed contract version",
    href: "/dashboard/licenses",
    action: "Explore voice licenses",
  },
  {
    title: "Hear the whole story.",
    name: "Analyze",
    Icon: AudioLines,
    text: "Submit authorized audio. FFprobe measures the recording, VAD estimates speech activity, and Groq Whisper transcribes the words.",
    evidence: "Recording → measured speech + transcript",
    href: "/dashboard/submissions",
    action: "Explore audio submissions",
  },
  {
    title: "Know why it matters.",
    name: "Evaluate",
    Icon: ListChecks,
    text: "Gemini assesses content. Deterministic rules check approved scope. Missing evidence stays visible as a review requirement.",
    evidence: "AI observations + contract rules → explained result",
    href: "/dashboard/submissions",
    action: "Open compliance workflows",
  },
  {
    title: "Keep the artist in control.",
    name: "Authorize",
    Icon: ShieldCheck,
    text: "The artist attests to identity and campaign authorization, resolves possible reuse, and reviews eligible royalty charges.",
    evidence: "Human decision → version-bound audit record",
    href: "/dashboard/royalties",
    action: "Explore royalty review",
  },
  {
    title: "Give every charge a reason.",
    name: "Invoice",
    Icon: ReceiptText,
    text: "Approved charges can become PayPal Sandbox invoices. Draft, sent and paid are separate states. Local mock payments stay explicitly labeled.",
    evidence: "Approved royalty → traceable test invoice",
    href: "/dashboard/invoices",
    action: "Explore invoices & payments",
  },
];

export default function ProductWalkthrough() {
  const [active, setActive] = useState(0);
  const stage = stages[active];
  const Icon = stage.Icon;
  return (
    <div className="rights-walkthrough">
      <div
        className="rights-stage-list"
        role="tablist"
        aria-label="How FairModel works"
        aria-orientation="vertical"
      >
        {stages.map((item, index) => (
          <button
            key={item.name}
            id={`rights-tab-${index}`}
            role="tab"
            aria-selected={index === active}
            aria-controls="rights-stage-panel"
            tabIndex={index === active ? 0 : -1}
            onClick={() => setActive(index)}
            onKeyDown={(event) => {
              const next =
                event.key === "ArrowDown"
                  ? (index + 1) % stages.length
                  : event.key === "ArrowUp"
                    ? (index + stages.length - 1) % stages.length
                    : event.key === "Home"
                      ? 0
                      : event.key === "End"
                        ? stages.length - 1
                        : null;
              if (next !== null) {
                event.preventDefault();
                setActive(next);
                document.getElementById(`rights-tab-${next}`)?.focus();
              }
            }}
          >
            <span>0{index + 1}</span>
            {item.name}
            <ArrowUpRight size={18} aria-hidden="true" />
          </button>
        ))}
      </div>
      <div
        className="rights-stage-panel"
        id="rights-stage-panel"
        role="tabpanel"
        aria-labelledby={`rights-tab-${active}`}
        tabIndex={0}
      >
        <div className="rights-stage-art" aria-hidden="true">
          <span />
          <span />
          <span />
          <Icon size={70} strokeWidth={1} />
        </div>
        <div key={active} className="rights-stage-copy">
          <span className="eyebrow">STEP 0{active + 1}</span>
          <h3>{stage.title}</h3>
          <p>{stage.text}</p>
          <div className="rights-evidence-line">{stage.evidence}</div>
          <Link href={stage.href}>
            {stage.action}
            <ArrowUpRight size={17} />
          </Link>
        </div>
      </div>
    </div>
  );
}
