"use client";

import dynamic from "next/dynamic";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  ArrowDownToLine,
  ArrowLeft,
  ArrowRight,
  AudioLines,
  BadgeCheck,
  Check,
  ChevronRight,
  CircleAlert,
  Clock3,
  FileAudio2,
  Globe2,
  LockKeyhole,
  Mic,
  Pause,
  Play,
  Radio,
  ReceiptText,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Upload,
  Volume2,
  Wallet,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useFairModel, type Generation, type GenerationStatus } from "@/store/fairmodel-store";

const OrbScene = dynamic(() => import("./OrbScene"), {
  ssr: false,
  loading: () => <div className="scene-fallback"><span className="fallback-orb" /></div>,
});
const TerrainScene = dynamic(() => import("./TerrainScene"), {
  ssr: false,
  loading: () => <div className="terrain-fallback" />,
});

const screenMotion = {
  initial: { opacity: 0, y: 12, scale: 0.99 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -8, scale: 0.995 },
  transition: { type: "spring" as const, stiffness: 190, damping: 24 },
};

function MotionNumber({ value, prefix = "$", decimals = 2 }: { value: number; prefix?: string; decimals?: number }) {
  const [shown, setShown] = useState(value);
  const shownRef = useRef(value);
  useEffect(() => {
    const start = shownRef.current;
    const duration = 550;
    const began = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const progress = Math.min(1, (now - began) / duration);
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = start + (value - start) * ease;
      shownRef.current = current;
      setShown(current);
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);
  return <>{prefix}{shown.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}</>;
}

function StatusTag({ status }: { status: GenerationStatus }) {
  const labels = {
    analyzing: "Analyzing",
    approved: "In scope",
    overage: "Overage",
    breach: "Breach",
  };
  return <span className={`fm-status status-${status}`}><i />{labels[status]}</span>;
}

function LiveOrb({ compact = false }: { compact?: boolean }) {
  return <div className={`live-orb-wrap ${compact ? "live-orb-compact" : ""}`}>
    <OrbScene compact={compact} />
    <span className="orb-callout callout-match">VOICEPRINT <strong>99.2%</strong></span>
    <span className="orb-callout callout-license"><span className="mint-dot" /> LICENSE SCOPE <strong>ACTIVE</strong></span>
  </div>;
}

function MicButton() {
  const [active, setActive] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const frameRef = useRef(0);
  const setAudioLevel = useFairModel((state) => state.setAudioLevel);

  useEffect(() => () => {
    cancelAnimationFrame(frameRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    void contextRef.current?.close();
    setAudioLevel(0);
  }, [setAudioLevel]);

  async function toggleMic() {
    if (active) {
      cancelAnimationFrame(frameRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
      await contextRef.current?.close();
      streamRef.current = null;
      contextRef.current = null;
      setAudioLevel(0);
      setActive(false);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      useFairModel.getState().setNotify("This browser does not support microphone input.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const context = new AudioContext();
      const analyser = context.createAnalyser();
      analyser.fftSize = 256;
      context.createMediaStreamSource(stream).connect(analyser);
      const samples = new Uint8Array(analyser.frequencyBinCount);
      streamRef.current = stream;
      contextRef.current = context;
      setActive(true);
      const measure = () => {
        analyser.getByteFrequencyData(samples);
        const average = samples.reduce((sum, item) => sum + item, 0) / samples.length / 255;
        setAudioLevel(average);
        frameRef.current = requestAnimationFrame(measure);
      };
      measure();
    } catch {
      useFairModel.getState().setNotify("Microphone access was not granted. The demo remains interactive.");
    }
  }

  return <button className={`fm-button ${active ? "button-alert" : "button-glass"}`} onClick={() => void toggleMic()}>
    {active ? <Pause size={15} /> : <Mic size={15} />}{active ? "Stop listening" : "Speak to orb"}
  </button>;
}

function SceneBadges() {
  const breach = useFairModel((state) => state.breachActive);
  const verified = useFairModel((state) => state.contractVerified);
  return <div className="scene-badges">
    <span className={breach ? "badge-breach" : "badge-calm"}><span className="scene-status-dot" />{breach ? "SCOPE BREACH" : verified ? "LICENSE ACTIVE" : "VOICE SIGNATURE · LIVE"}</span>
    <span className="scene-readout">20K VOICE PARTICLES</span>
  </div>;
}

export function HeroScreen() {
  const setScreen = useFairModel((state) => state.setScreen);
  const createGeneration = useFairModel((state) => state.createGeneration);
  const prefersReduced = useReducedMotion();
  return <motion.section className="hero-screen" {...(prefersReduced ? { initial: false } : screenMotion)}>
    <div className="hero-copy">
      <span className="fm-eyebrow"><span className="pulse-dot" /> THE IDENTITY CONTROL ROOM</span>
      <h1>Your voice.<br />Your <em>terms.</em><br />Metered by the second.</h1>
      <p>A live, explainable view of licensed voice use. The artist sets the scope; every generation is measured against it.</p>
      <div className="hero-actions">
        <button className="fm-button button-primary" onClick={() => setScreen("control")}>Open control room <ArrowRight size={16} /></button>
        <button className="fm-button button-glass" onClick={() => void createGeneration("breach")}><ShieldAlert size={16} /> Watch a breach</button>
      </div>
      <MicButton />
      <div className="hero-facts">
        <span><ShieldCheck size={15} /> Artist review stays in control</span>
        <span><Activity size={15} /> Meter updates as usage arrives</span>
      </div>
    </div>
    <div className="hero-scene">
      <div className="scene-aura" />
      <LiveOrb />
      <SceneBadges />
      <span className="scene-coordinate coordinate-one">VOICE / AMARA REED</span>
      <span className="scene-coordinate coordinate-two">SIGNAL · 48.2 KHZ</span>
    </div>
    <div className="hero-bottom">
      <span>FICTIONAL DEMO IDENTITY · AMARA REED</span>
      <span>PAYMENTS ARE SIMULATED · NO REAL FUNDS</span>
    </div>
  </motion.section>;
}

const clauses = [
  { n: "01", label: "Runtime", value: "30 sec / asset · 90 day term", icon: Clock3 },
  { n: "02", label: "Territory", value: "US · Canada · United Kingdom", icon: Globe2 },
  { n: "03", label: "Media", value: "Digital · Podcast · Social reel", icon: Radio },
  { n: "04", label: "Rate", value: "$0.05 / second · tiered overage", icon: Wallet },
];

export function ContractScreen() {
  const ingest = useFairModel((state) => state.ingestContract);
  const complete = useFairModel((state) => state.completeContract);
  const verified = useFairModel((state) => state.contractVerified);
  const [fileName, setFileName] = useState("");
  const [dragging, setDragging] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [locked, setLocked] = useState(verified);
  const prefersReduced = useReducedMotion();

  function startSample(name = "Amara_Reed_voice_license.pdf") {
    setFileName(name);
    setScanning(true);
    setLocked(false);
    window.setTimeout(() => {
      ingest();
      setLocked(true);
      setScanning(false);
    }, prefersReduced ? 80 : 1300);
  }

  function acceptFile(file?: File) {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      useFairModel.getState().setNotify("Choose a PDF. This client demo does not upload documents.");
      return;
    }
    startSample(file.name);
  }

  return <motion.section className="screen-stack" {...(prefersReduced ? { initial: false } : screenMotion)}>
    <ScreenHeading eyebrow="01 / CONTRACT INGESTION" title="Put the terms in the light." description="Drop a license or load the sample. This client-only demo visualizes a fixed, fictional scope—no document is uploaded." />
    <div className="contract-layout">
      <div className={`contract-portal glass-panel ${dragging ? "portal-dragging" : ""} ${scanning ? "portal-scanning" : ""}`}
        onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => { event.preventDefault(); setDragging(false); acceptFile(event.dataTransfer.files[0]); }}>
        <input aria-label="Choose sample license PDF" type="file" accept=".pdf,application/pdf" onChange={(event) => acceptFile(event.target.files?.[0])} />
        <div className="portal-icon"><Upload size={23} /></div>
        <span className="fm-eyebrow">{scanning ? "SCANNING CONTRACT SCOPE" : fileName || "CONTRACT PORTAL"}</span>
        <h2>{scanning ? "Reading the boundaries…" : "Drop a license to begin."}</h2>
        <p>PDF intake is local-only in this demo. Loading a file animates the sample scope; file contents are not sent or parsed.</p>
        {scanning && <span className="laser-scan" />}
        <div className="portal-actions">
          <button className="fm-button button-primary" onClick={() => startSample()}><Sparkles size={15} /> Use sample contract</button>
          <label className="fm-button button-glass"><Upload size={15} /> Choose PDF<input type="file" accept=".pdf,application/pdf" onChange={(event) => acceptFile(event.target.files?.[0])} /></label>
        </div>
      </div>
      <div className="contract-preview glass-panel">
        <div className="panel-title-row"><div><span className="fm-eyebrow">LICENSE SHELL</span><h2>Amara Reed · Voice license</h2></div><span className={`scope-stamp ${locked ? "stamp-verified" : ""}`}>{locked ? <><BadgeCheck size={14} /> VERIFIED</> : <><LockKeyhole size={13} /> DRAFT</>}</span></div>
        <div className="clause-list">
          {clauses.map(({ n, label, value, icon: Icon }, index) => <motion.div key={n} className={`clause-chip ${locked ? "clause-locked" : ""}`} initial={false} animate={{ opacity: locked ? 1 : 0.62, x: locked ? 0 : -6 }} transition={{ delay: locked ? index * 0.12 : 0, type: "spring", stiffness: 230, damping: 22 }}>
            <span className="clause-icon"><Icon size={16} /></span><span className="clause-copy"><small>{n} / {label}</small><strong>{value}</strong></span><Check size={15} className="clause-check" />
          </motion.div>)}
        </div>
        <div className="geo-scope"><div className="geo-copy"><span className="fm-eyebrow">ALLOWED GEOGRAPHY</span><strong>US · CA · UK</strong><small>All other regions remain outside scope.</small></div><div className="dotted-globe" aria-label="Licensed regions US, Canada, and United Kingdom"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><b>US</b><b>CA</b><b>UK</b></div></div>
        <div className="forbidden-strip"><span><ShieldAlert size={14} /> FORBIDDEN ZONE</span><strong>Politics</strong><strong>Gambling</strong><strong>Tobacco</strong></div>
        <div className="rate-steps"><span className="fm-eyebrow">ROYALTY TIERS</span><div><i style={{ height: "18px" }} /><i style={{ height: "28px" }} /><i style={{ height: "42px" }} /></div><small>BASE $0.05/sec <span>·</span> OVERAGE ×1.5 <span>·</span> TIER 2 ×2</small></div>
        {locked && <motion.div className="verified-seal" initial={{ scale: 0.7, rotate: -12, opacity: 0 }} animate={{ scale: 1, rotate: 0, opacity: 1 }}><BadgeCheck size={19} /> CONTRACT VERIFIED · DEMO SCOPE</motion.div>}
        <button className="fm-button button-primary contract-continue" onClick={() => { if (!locked) startSample(); else complete(); }}>{locked ? "Enter live control room" : "Verify sample scope"} <ArrowRight size={15} /></button>
      </div>
    </div>
  </motion.section>;
}

export function ScreenHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="screen-heading"><div><span className="fm-eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}

function FeedCard({ item, selected }: { item: Generation; selected: boolean }) {
  const selectGeneration = useFairModel((state) => state.selectGeneration);
  return <button className={`feed-card ${selected ? "feed-selected" : ""} feed-${item.status}`} onClick={() => selectGeneration(item.id)}>
    <span className="feed-card-top"><strong>{item.studio}</strong><StatusTag status={item.status} /></span>
    <span className="feed-meta"><span><FileAudio2 size={12} />{item.assetType}</span><span><Clock3 size={12} />{item.durationSeconds}s</span></span>
    <span className="feed-meta"><span><Globe2 size={12} />{item.region}</span><span>{item.category}</span></span>
    <MiniWave status={item.status} />
  </button>;
}

function MiniWave({ status }: { status: GenerationStatus }) {
  const bars = useMemo(() => Array.from({ length: 28 }, (_, i) => 8 + Math.abs(Math.sin(i * 7.3)) * (i % 5 === 0 ? 27 : 15)), []);
  return <span className={`mini-wave wave-${status}`} aria-hidden="true">{bars.map((height, index) => <i key={index} style={{ height: `${height}px` }} />)}</span>;
}

export function ControlRoomScreen() {
  const generations = useFairModel((state) => state.generations);
  const invoices = useFairModel((state) => state.invoices);
  const selected = useFairModel((state) => state.selectedGenerationId);
  const breach = useFairModel((state) => state.breachActive);
  const role = useFairModel((state) => state.role);
  const setRole = useFairModel((state) => state.setRole);
  const createGeneration = useFairModel((state) => state.createGeneration);
  const approve = useFairModel((state) => state.approveGeneration);
  const recover = useFairModel((state) => state.recoverBreach);
  const setScreen = useFairModel((state) => state.setScreen);
  const approved = generations.filter((item) => item.status === "approved" || item.status === "overage");
  const estimatedCents = approved.reduce((sum, item) => sum + item.amountCents, 0);
  const used = generations.filter((item) => item.status !== "breach" && item.status !== "analyzing").reduce((sum, item) => sum + item.durationSeconds, 0);
  const scopeHealth = Math.max(12, Math.round(100 - (used % 85)));
  const breachGeneration = generations.find((item) => item.status === "breach" && !item.artistApproved);
  return <motion.section className="screen-stack control-room" {...screenMotion}>
    <ScreenHeading eyebrow="02 / LIVE CONTROL ROOM" title="Your identity, in real time." description="Every incoming generation is checked against the artist-approved shell." action={<div className="view-switch"><button className={role === "talent" ? "switch-active" : ""} onClick={() => setRole("talent")}>Talent</button><button className={role === "studio" ? "switch-active" : ""} onClick={() => setRole("studio")}>Studio</button></div>} />
    <div className="control-topline"><span><i className="pulse-dot" /> LIVE SIMULATION</span><span className="paypal-unlinked"><span /> PayPal · Not connected</span><span className="control-scope"><ShieldCheck size={14} /> LICENSE SCOPE HEALTH <strong>{scopeHealth}%</strong></span><span className="health-track"><i style={{ width: `${scopeHealth}%` }} /></span></div>
    <div className="control-grid">
      <section className="feed-column glass-panel"><div className="column-heading"><div><span className="fm-eyebrow">LIVE SIGNAL</span><h2>Incoming generations</h2></div><span className="live-count">{generations.length} <i /></span></div><div className="feed-list">{generations.slice(0, 6).map((item) => <FeedCard key={item.id} item={item} selected={selected === item.id} />)}</div><button className="feed-trigger" onClick={() => void createGeneration("normal")}><span className="trigger-plus">+</span>Simulate generation <ArrowRight size={13} /></button></section>
      <section className={`orb-center glass-panel ${breach ? "orb-center-breach" : ""}`}><div className="center-topline"><span className="fm-eyebrow">VOICEPRINT / 01</span><span className="frequency">LIVE FREQUENCY <i /></span></div><div className="center-orb"><LiveOrb compact /><div className="scope-ring ring-a" /><div className="scope-ring ring-b" /></div><SceneBadges /><div className="center-footer"><span>AMARA REED <small>· TALENT PROFILE</small></span><button aria-label="Open audit view" onClick={() => setScreen("audit")}><Activity size={14} /> INSPECT SIGNAL <ChevronRight size={13} /></button></div>{breach && <div className="breach-flash" aria-hidden="true" />}</section>
      <section className="meter-column glass-panel"><div className="column-heading"><div><span className="fm-eyebrow">ESTIMATED ROYALTIES</span><h2>Royalty meter</h2></div><span className="meter-icon"><Wallet size={16} /></span></div><div className="meter-display"><span className="currency-sign">$</span><MotionNumber value={estimatedCents / 100} prefix="" /><span className="meter-currency">USD</span></div><span className="meter-caption">EARNED · LOCAL DEMO ESTIMATE</span><div className="meter-spark"><Sparkline generations={generations} /></div><div className="tier-row"><span>BASE TIER <strong>00–30 sec</strong></span><span>OVERAGE <strong>×1.5</strong></span></div><div className="tier-track"><i /></div><div className="meter-meta"><span><span className="mint-dot" /> CONTRACT VERIFIED</span><span>Artist review required</span></div><div className="meter-foot"><span>SIMULATED ONLY</span><strong>{approved.length} scoped assets</strong></div></section>
    </div>
    <Timeline generations={generations} />
    <div className={`breach-panel ${breach ? "breach-panel-open" : ""}`} aria-live="polite">
      {breachGeneration ? <div className="breach-panel-inner"><div className="breach-heading"><span className="breach-icon"><ShieldAlert size={18} /></span><div><span className="fm-eyebrow">SCOPE EVENT · ARTIST REVIEW REQUIRED</span><h2>Generation outside the license.</h2></div><button aria-label="Dismiss breach panel" onClick={recover}><X size={16} /></button></div><div className="breach-reasons"><span><X size={13} /> Geography violation: Brazil is not licensed.</span><span><X size={13} /> Prohibited category: gambling.</span></div><div className="breach-transcript">“<mark>Try your luck tonight.</mark> A regional variation for Brazil.”</div><div className="breach-invoice"><div><ReceiptText size={16} /><span>Proposed review amount <small>Only payable after artist approval · simulated invoice</small></span></div><strong><MotionNumber value={breachGeneration.amountCents / 100} /></strong></div><div className="breach-actions">{role === "talent" ? <button className="fm-button button-alert" onClick={() => approve(breachGeneration.id)}><Check size={14} /> Review & approve demo amount</button> : <span className="review-required"><LockKeyhole size={14} /> Awaiting talent review</span>}<button className="fm-button button-glass" onClick={() => setScreen("audit")}>Open audit <ArrowRight size={14} /></button></div><p className="payment-disclaimer">DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED</p></div> : <div className="breach-idle"><ShieldCheck size={16} /><span>Scope intact. The shell is monitoring live usage.</span><button onClick={() => void createGeneration("breach")}><ShieldAlert size={14} /> Simulate breach</button></div>}
    </div>
    <div className="control-footnote"><span><Activity size={13} /> New mock events arrive every 3–6 seconds.</span><span>{invoices.length} review invoice{invoices.length === 1 ? "" : "s"} · simulated, client-only</span></div>
  </motion.section>;
}

function Sparkline({ generations }: { generations: Generation[] }) {
  const values = generations.slice(0, 10).reverse().map((item) => Math.max(3, item.amountCents));
  const points = values.map((value, index) => `${index * 100 / Math.max(1, values.length - 1)},${38 - Math.min(30, value / 14)}`).join(" ");
  return <svg viewBox="0 0 100 42" preserveAspectRatio="none" role="img" aria-label="Estimated royalty sparkline"><defs><linearGradient id="spark-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#ffb938" stopOpacity=".25" /><stop offset="1" stopColor="#ffb938" stopOpacity="0" /></linearGradient></defs><polygon points={`0,42 ${points} 100,42`} fill="url(#spark-fill)" /><polyline points={points} fill="none" stroke="#ffb938" strokeWidth="1.5" vectorEffect="non-scaling-stroke" /></svg>;
}

function Timeline({ generations }: { generations: Generation[] }) {
  return <section className="timeline-panel glass-panel"><div className="timeline-heading"><span className="fm-eyebrow">LAST 24 HOURS</span><span>{generations.length} monitored assets <span className="timeline-legend"><i className="legend-approved" /> In scope <i className="legend-overage" /> Overage <i className="legend-breach" /> Breach</span></span></div><div className="timeline-bars">{generations.slice(0, 24).reverse().map((item, index) => <button key={item.id} title={`${item.studio} · ${item.region} · ${item.durationSeconds}s · ${item.status}`} aria-label={`${item.status}: ${item.studio}, ${item.region}, ${item.durationSeconds} seconds`} className={`timeline-bar bar-${item.status}`} style={{ height: `${20 + Math.min(item.durationSeconds, 40) * 1.45}px`, animationDelay: `${index * 30}ms` }} onClick={() => useFairModel.getState().selectGeneration(item.id)} />)}</div><div className="timeline-axis"><span>24h ago</span><span>12h</span><span>Now</span></div></section>;
}

export function AuditScreen() {
  const selectedId = useFairModel((state) => state.selectedGenerationId);
  const generations = useFairModel((state) => state.generations);
  const approve = useFairModel((state) => state.approveGeneration);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const generation = generations.find((item) => item.id === selectedId) || generations[0];
  const breach = generation.status === "breach";
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => setProgress((value) => {
      if (value >= 100) { setPlaying(false); return 0; }
      return value + 3;
    }), 110);
    return () => clearInterval(timer);
  }, [playing]);
  const wordCount = generation.transcript.join(" ").split(/\s+/).length;
  const metric = (title: string, value: string) => <div className="audit-metric" key={title}><span>{title}</span><strong>{value}</strong></div>;
  return <motion.section className="screen-stack" {...screenMotion}>
    <ScreenHeading eyebrow="03 / GENERATION AUDIT" title="Every signal has a story." description={`Inspect ${generation.id} · ${generation.studio}. Evidence is advisory; the talent makes the call.`} action={<span className="audit-demo-pill"><Activity size={13} /> MOCK AUDIT RECORD</span>} />
    <div className="audit-metrics">{metric("WORDS", String(wordCount))}{metric("DURATION", `${generation.durationSeconds}s`)}{metric("CAMPAIGN", generation.category)}{metric("REGION", generation.region)}{metric("MEDIUM", generation.medium)}</div>
    <div className="audit-layout">
      <section className="glass-panel audit-media"><div className="panel-title-row"><div><span className="fm-eyebrow">FREQUENCY × TIME × AMPLITUDE</span><h2>Signal terrain</h2></div><span className="terrain-hint">DRAG TO ORBIT</span></div><TerrainScene /><div className="terrain-labels"><span>LOW · 20 HZ</span><span>PLAYHEAD {progress}%</span><span>HIGH · 20 KHZ</span></div><button className="fm-button button-glass play-button" onClick={() => { setPlaying(!playing); if (!playing && progress === 0) setProgress(1); }}>{playing ? <Pause size={14} /> : <Play size={14} />}{playing ? "Pause audio preview" : "Play local preview"}<span>This is a visual mock preview.</span></button></section>
      <section className="glass-panel voice-match"><span className="fm-eyebrow">VOICEPRINT ANALYSIS</span><h2>Voice match</h2><div className="match-dial" style={{ "--match-angle": "99.2%" } as React.CSSProperties}><div><strong>99.2<span>%</span></strong><small>SIMULATED MATCH</small></div></div><div className="threshold-line"><span>Threshold · 82%</span><i /><strong>+17.2</strong></div><span className="match-disclaimer"><ShieldCheck size={13} /> Not identity proof. Human review required.</span></section>
      <section className="glass-panel transcript-panel"><div className="panel-title-row"><div><span className="fm-eyebrow">TRANSCRIPT · LOCAL DEMO</span><h2>Words in context</h2></div><Volume2 size={15} className="muted-icon" /></div><div className="transcript-lines">{generation.transcript.map((line, index) => <p key={index} className={breach ? "transcript-flagged" : ""}>{line.split(" ").map((word, wordIndex) => <span key={wordIndex} className={breach && /luck|gambling|politics/i.test(word) ? "flagged-word" : progress > (wordIndex + 1) * 7 ? "spoken-word" : ""}>{word} </span>)}</p>)}</div><div className="category-tags"><span className={breach ? "tag-breach" : ""}><ShieldAlert size={12} /> {generation.category}</span><span><Globe2 size={12} /> {generation.region}</span><span><AudioLines size={12} /> {generation.medium}</span></div></section>
      <section className="glass-panel scope-checks"><span className="fm-eyebrow">CONTRACT SCOPE</span><h2>Permission check</h2>{[
        ["Territory is licensed", !breach],
        ["Category is permitted", !breach],
        ["Runtime within 30 seconds", generation.durationSeconds <= 30],
        ["Artist reviewed amount", generation.artistApproved],
      ].map(([label, passed]) => <div className={`scope-check ${passed ? "check-passed" : "check-failed"}`} key={String(label)}>{passed ? <Check size={14} /> : <X size={14} />}<span>{label}</span><strong>{passed ? "PASS" : "REVIEW"}</strong></div>)}{generation.status !== "analyzing" && !generation.artistApproved && <button className="fm-button button-primary approve-audit" onClick={() => approve(generation.id)}><Check size={14} /> Record talent review</button>}</section>
    </div>
  </motion.section>;
}

export function LedgerScreen() {
  const generations = useFairModel((state) => state.generations);
  const invoices = useFairModel((state) => state.invoices);
  const role = useFairModel((state) => state.role);
  const approve = useFairModel((state) => state.approveGeneration);
  const approveInvoice = useFairModel((state) => state.approveInvoice);
  const releasePayout = useFairModel((state) => state.releasePayout);
  const releaseBatch = useFairModel((state) => state.releaseBatch);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [payoutAnimation, setPayoutAnimation] = useState(false);
  const [drawer, setDrawer] = useState<string | null>(null);
  const total = generations.filter((item) => item.status !== "breach").reduce((sum, item) => sum + item.amountCents, 0);
  const invoiceRows = invoices.map((invoice) => ({ invoice, generation: generations.find((item) => item.id === invoice.generationId) })).filter((item) => item.generation);
  const selectedTotal = generations.filter((item) => selected.includes(item.id)).reduce((sum, item) => sum + item.amountCents, 0);
  async function runBatch() {
    if (!selected.length) return;
    setBusy(true);
    setPayoutAnimation(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1250));
      await releaseBatch(selected);
      setSelected([]);
    } finally {
      setBusy(false);
      window.setTimeout(() => setPayoutAnimation(false), 1200);
    }
  }
  function toggleSelected(id: string) {
    setSelected((value) => value.includes(id) ? value.filter((item) => item !== id) : [...value, id]);
  }
  return <motion.section className="screen-stack" {...screenMotion}>
    <ScreenHeading eyebrow="04 / ROYALTY LEDGER" title="The numbers, in the open." description="Review every measured second, approve proposed amounts, and follow simulated invoice events." action={<div className="paypal-disconnected"><span className="paypal-logo">P</span><span><strong>PayPal</strong><small>Not connected · demo only</small></span><span className="disconnected-dot" /></div>} />
    <div className="ledger-notice"><CircleAlert size={15} /><strong>DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED</strong><span>Client-side ledger · fictional transactions only</span></div>
    <div className="ledger-summary"><div className="glass-panel ledger-total"><span className="fm-eyebrow">ESTIMATED TOTAL · USD</span><strong><MotionNumber value={total / 100} /></strong><small>Mock royalty estimates. Nothing is charged.</small></div><div className="glass-panel ledger-total"><span className="fm-eyebrow">AWAITING ARTIST REVIEW</span><strong>{generations.filter((item) => !item.artistApproved && item.status !== "breach" && item.status !== "analyzing").length}</strong><small>Charges require explicit talent approval.</small></div><div className="glass-panel ledger-total"><span className="fm-eyebrow">SIMULATED PAYOUTS</span><strong>{invoices.filter((invoice) => invoice.status === "PAID_SIMULATED").length}</strong><small>PayPal API is not connected.</small></div></div>
    <div className="ledger-grid">
      <section className="glass-panel ledger-table-panel"><div className="ledger-panel-heading"><div><span className="fm-eyebrow">ROYALTY EVENTS</span><h2>Generation ledger</h2></div><span className="ledger-total-chip"><MotionNumber value={selectedTotal / 100} /></span></div><div className="ledger-scroll"><table className="fm-ledger"><thead><tr><th><span className="sr-only">Select</span></th><th>GENERATION</th><th>ASSET / SCOPE</th><th>SECONDS</th><th>ESTIMATE</th><th>STATUS</th><th>ARTIST REVIEW</th></tr></thead><tbody>{generations.map((item) => <tr key={item.id}><td><input aria-label={`Select ${item.id} for simulated batch payout`} type="checkbox" checked={selected.includes(item.id)} disabled={!item.artistApproved || item.status === "breach"} onChange={() => toggleSelected(item.id)} /></td><td><button className="ledger-id" onClick={() => setDrawer(item.id)}>{item.id}</button><small>{new Date(item.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</small></td><td><strong>{item.assetType}</strong><small>{item.region} · {item.category}</small></td><td className="mono-number">{item.durationSeconds}s</td><td className="money-number">${(item.amountCents / 100).toFixed(2)}</td><td><StatusTag status={item.status} /></td><td>{item.status === "breach" ? <span className="review-required">Scope review</span> : item.artistApproved ? <span className="approved-text"><Check size={13} /> Approved</span> : role === "talent" && item.status !== "analyzing" ? <button className="table-approve" onClick={() => approve(item.id)}>Review & approve</button> : <span className="review-required">Talent review</span>}</td></tr>)}</tbody></table></div><div className="ledger-batch"><span>{selected.length} selected · <strong><MotionNumber value={selectedTotal / 100} /></strong></span><button className="fm-button button-primary" disabled={!selected.length || busy} onClick={() => void runBatch}>{busy ? <Activity size={14} className="spin-icon" /> : <ArrowDownToLine size={14} />}{busy ? "Simulating payout…" : "Release simulated payout"}</button></div></section>
      <aside className="glass-panel invoice-list"><div className="ledger-panel-heading"><div><span className="fm-eyebrow">INVOICE DESK</span><h2>Review queue</h2></div><ReceiptText size={16} /></div>{invoiceRows.length ? invoiceRows.map(({ invoice, generation }) => generation && <article className="invoice-row" key={invoice.id}><div className="invoice-row-top"><span className="invoice-id">{invoice.id}</span><span className={`invoice-state invoice-${invoice.status.toLowerCase()}`}>{invoice.status.replaceAll("_", " ")}</span></div><strong>{generation.studio}</strong><span>{generation.region} · {generation.category} · {generation.durationSeconds}s</span><div className="invoice-row-total"><span>Proposed · DEMO ONLY</span><strong>${(invoice.amountCents / 100).toFixed(2)}</strong></div><div className="invoice-row-actions">{invoice.status === "REVIEW_REQUIRED" && role === "talent" ? <button className="table-approve" onClick={() => { approveInvoice(invoice.id); approve(generation.id); }}>Review & approve</button> : invoice.status === "APPROVED" ? <button className="fm-button button-paypal-demo" onClick={() => void releasePayout(invoice.id)}>Simulate PayPal payout</button> : invoice.status === "PAID_SIMULATED" ? <span className="approved-text"><Check size={13} /> Simulated · {invoice.transactionId}</span> : <span className="review-required"><LockKeyhole size={13} /> Awaiting artist review</span>}</div><div className="invoice-timeline"><i className="done" /><i className={invoice.status !== "REVIEW_REQUIRED" ? "done" : ""} /><i className={invoice.status === "PAID_SIMULATED" ? "done" : ""} /><span>Review</span><span>Approved</span><span>Demo</span></div></article>) : <div className="invoice-empty"><ReceiptText size={23} /><strong>No invoices yet</strong><span>A simulated breach creates a review-only invoice. Approval is always required.</span></div>}<div className="paypal-connect-card"><span className="paypal-logo">P</span><div><strong>PayPal Sandbox</strong><small>Not connected · no API requests</small></div><LockKeyhole size={14} /></div></aside>
    </div>
    <AnimatePresence>{drawer && <InvoiceDrawer id={drawer} generation={generations.find((item) => item.id === drawer)} close={() => setDrawer(null)} />}</AnimatePresence>
    <AnimatePresence>{payoutAnimation && <motion.div className="payout-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><motion.div className="payout-flight" initial={{ scale: 0.88, y: 18 }} animate={{ scale: 1, y: 0 }}><div className="payout-nodes"><span>TALENT</span><i>✦ · ✦ · ✦</i><span className="paypal-logo">P</span></div><div className="payout-success"><BadgeCheck size={30} /><strong>Demo payout complete</strong><span>No real funds transferred.</span></div></motion.div></motion.div>}</AnimatePresence>
  </motion.section>;
}

function InvoiceDrawer({ id, generation, close }: { id: string; generation?: Generation; close: () => void }) {
  return <motion.div className="drawer-scrim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={close}><motion.aside className="invoice-drawer glass-panel" role="dialog" aria-modal="true" aria-label={`Generation ${id} invoice detail`} initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }} transition={{ type: "spring", damping: 25, stiffness: 220 }} onClick={(event) => event.stopPropagation()}><button className="drawer-close" aria-label="Close invoice detail" onClick={close}><X size={17} /></button><span className="fm-eyebrow">LOCAL DEMO INVOICE</span><h2>{id}</h2><p>Fictional royalty estimate · No payment is requested.</p><div className="invoice-paper"><div className="invoice-brand"><AudioLines size={18} /> FAIRMODEL</div><span>INVOICE · SIMULATED</span><hr /><div><span>Asset</span><strong>{generation?.assetType || "Voice generation"}</strong></div><div><span>Campaign location</span><strong>{generation?.region || "United Kingdom"}</strong></div><div><span>Measured usage</span><strong>{generation?.durationSeconds || 0} seconds</strong></div><div><span>Tier</span><strong>{generation?.durationSeconds && generation.durationSeconds > 30 ? "Overage × 1.5" : "Base rate"}</strong></div><div><span>Rate</span><strong>$0.05 / sec</strong></div><hr /><div className="invoice-paper-total"><span>ESTIMATED TOTAL</span><strong>${((generation?.amountCents || 0) / 100).toFixed(2)}</strong></div><p>Subject to explicit artist review. This is not a real invoice or charge.</p></div><div className="invoice-disclaimer"><CircleAlert size={15} /> PayPal is disconnected. This experience makes no API calls and moves no funds.</div><button className="fm-button button-paypal-demo" onClick={close}>PayPal · demo only / not connected <ArrowRight size={14} /></button><button className="fm-button button-glass drawer-back" onClick={close}><ArrowLeft size={14} /> Back to ledger</button></motion.aside></motion.div>;
}
