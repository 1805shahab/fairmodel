"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
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

const staticQuery = "(prefers-reduced-motion: reduce), (max-height: 640px)";
function subscribeStatic(notify: () => void) {
  const media = window.matchMedia(staticQuery);
  media.addEventListener("change", notify);
  return () => media.removeEventListener("change", notify);
}
const staticSnapshot = () => window.matchMedia(staticQuery).matches;

export default function ProductWalkthrough() {
  const [active, setActive] = useState(0);
  const track = useRef<HTMLDivElement>(null);
  const sticky = useRef<HTMLDivElement>(null);
  const navigation = useRef<HTMLDivElement>(null);
  const staticView = useSyncExternalStore(
    subscribeStatic,
    staticSnapshot,
    () => true,
  );
  useEffect(() => {
    if (staticView) return;
    let frame = 0;
    function update() {
      frame = 0;
      if (!track.current || !sticky.current) return;
      const box = track.current.getBoundingClientRect();
      const top = Number.parseFloat(getComputedStyle(sticky.current).top) || 0;
      const distance = track.current.offsetHeight - sticky.current.offsetHeight;
      if (distance <= 0) return;
      const progress = Math.max(0, Math.min(1, (top - box.top) / distance));
      setActive(Math.round(progress * (stages.length - 1)));
    }
    function schedule() {
      if (!frame) frame = requestAnimationFrame(update);
    }
    const observer = new ResizeObserver(schedule);
    if (track.current) observer.observe(track.current);
    if (sticky.current) observer.observe(sticky.current);
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    schedule();
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  }, [staticView]);
  useEffect(() => {
    const list = navigation.current;
    const button = list?.querySelector<HTMLElement>(`#rights-tab-${active}`);
    if (list && button && list.scrollWidth > list.clientWidth) {
      list.scrollLeft = Math.max(
        0,
        button.offsetLeft -
          list.offsetLeft -
          (list.clientWidth - button.offsetWidth) / 2,
      );
    }
  }, [active]);
  function select(index: number) {
    setActive(index);
    if (!staticView && track.current && sticky.current) {
      const top = Number.parseFloat(getComputedStyle(sticky.current).top) || 0;
      const start =
        track.current.getBoundingClientRect().top + window.scrollY - top;
      const distance = track.current.offsetHeight - sticky.current.offsetHeight;
      window.scrollTo({
        top: start + (distance * index) / (stages.length - 1),
        behavior: "instant",
      });
    }
  }
  const stage = stages[active];
  const Icon = stage.Icon;
  return (
    <div
      className="workflow-scroll-track"
      ref={track}
      data-scroll={!staticView}
      data-active-step={active + 1}
    >
      <div className="workflow-sticky" ref={sticky}>
        <div className="workflow-progress-heading">
          <span className="eyebrow">FROM PERMISSION TO PAYMENT</span>
          <span>
            {staticView
              ? "Choose a step to explore"
              : "Scroll to explore · or choose a step"}
          </span>
        </div>
        <div className="rights-walkthrough">
          <div
            ref={navigation}
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
                onClick={() => select(index)}
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
                    select(next);
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
        <div className="workflow-progress-track" aria-hidden="true">
          <span
            style={{ transform: `scaleX(${(active + 1) / stages.length})` }}
          />
        </div>
      </div>
    </div>
  );
}
