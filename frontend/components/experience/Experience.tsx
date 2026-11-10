"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  AudioLines,
  Activity,
  Command,
  FileCheck2,
  Gauge,
  Home,
  Keyboard,
  Play,
  Radio,
  ReceiptText,
  Search,
  ShieldAlert,
  Sparkles,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  useFairModel,
  startSimulationEngine,
  stopSimulationEngine,
  type Screen,
} from "@/store/fairmodel-store";
import {
  AuditScreen,
  ContractScreen,
  ControlRoomScreen,
  HeroScreen,
  LedgerScreen,
} from "./screens";

const navigation: {
  id: Screen;
  title: string;
  icon: typeof Home;
  label: string;
}[] = [
  { id: "hero", title: "Identity overview", icon: Home, label: "Home" },
  {
    id: "contract",
    title: "Contract ingestion",
    icon: FileCheck2,
    label: "Contract",
  },
  {
    id: "control",
    title: "Live control room",
    icon: Gauge,
    label: "Control room",
  },
  { id: "audit", title: "Generation audit", icon: Activity, label: "Audit" },
  { id: "ledger", title: "Royalty ledger", icon: ReceiptText, label: "Ledger" },
];

export default function Experience() {
  const screen = useFairModel((state) => state.screen);
  const setScreen = useFairModel((state) => state.setScreen);
  const setNotify = useFairModel((state) => state.setNotify);
  const notify = useFairModel((state) => state.notify);
  const breach = useFairModel((state) => state.breachActive);
  const demoRunning = useFairModel((state) => state.demoRunning);
  const demoElapsed = useFairModel((state) => state.demoElapsed);
  const demo = useFairModel((state) => state.runDemo);
  const stopDemo = useFairModel((state) => state.stopDemo);
  const createGeneration = useFairModel((state) => state.createGeneration);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [search, setSearch] = useState("");
  const paletteRef = useRef<HTMLInputElement>(null);
  const filtered = useMemo(
    () =>
      navigation.filter((item) =>
        `${item.title} ${item.label}`
          .toLowerCase()
          .includes(search.toLowerCase()),
      ),
    [search],
  );

  useEffect(() => {
    startSimulationEngine();
    return () => stopSimulationEngine();
  }, []);

  useEffect(() => {
    if (!notify) return;
    const timer = window.setTimeout(() => setNotify(""), 3800);
    return () => clearTimeout(timer);
  }, [notify, setNotify]);

  useEffect(() => {
    if (!paletteOpen) return;
    paletteRef.current?.focus();
  }, [paletteOpen]);

  const openPalette = useCallback(() => setPaletteOpen(true), []);
  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        openPalette();
      }
      if (event.key === "Escape") setPaletteOpen(false);
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [openPalette]);

  const screenComponents = {
    hero: <HeroScreen />,
    contract: <ContractScreen />,
    control: <ControlRoomScreen />,
    audit: <AuditScreen />,
    ledger: <LedgerScreen />,
  };

  function chooseScreen(id: Screen) {
    setScreen(id);
    setPaletteOpen(false);
    setSearch("");
  }

  return (
    <main
      className={`experience-shell ${breach ? "experience-breach" : ""}`}
      onPointerMove={(event) => {
        const bounds = event.currentTarget.getBoundingClientRect();
        event.currentTarget.style.setProperty(
          "--pointer-x",
          `${event.clientX - bounds.left}px`,
        );
        event.currentTarget.style.setProperty(
          "--pointer-y",
          `${event.clientY - bounds.top}px`,
        );
      }}
    >
      <div className="ambient-fog fog-one" />
      <div className="ambient-fog fog-two" />
      <div className="film-grain" />
      <div className="edge-vignette" />
      <header className="experience-topbar">
        <button className="fm-brand" onClick={() => chooseScreen("hero")}>
          <span>
            <AudioLines size={17} />
          </span>
          FAIRMODEL<i>®</i>
        </button>
        <nav className="experience-nav" aria-label="FairModel screens">
          {navigation.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={screen === id ? "nav-current" : ""}
              onClick={() => chooseScreen(id)}
            >
              <Icon size={14} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="topbar-actions">
          <span className="demo-live">
            <i /> DEMO LIVE
          </span>
          <button className="palette-trigger" onClick={openPalette}>
            <Command size={13} />
            <span>Search</span>
            <kbd>⌘ K</kbd>
          </button>
          <button
            className="run-demo-button"
            onClick={demoRunning ? stopDemo : demo}
          >
            {demoRunning ? <X size={14} /> : <Play size={14} />}
            {demoRunning ? "Stop story" : "Demo mode"}
          </button>
        </div>
      </header>
      <aside
        className="experience-notice"
        aria-label="Control Room simulation status"
      >
        <span>FICTIONAL PREVIEW · NO LIVE AI OR VOICE VERIFICATION</span>
        <strong>DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED</strong>
        <Link href="/dashboard">Open working artist / studio workspace →</Link>
      </aside>
      <div className="experience-scroll">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            className="screen-transition"
            key={screen}
            initial={{ opacity: 0, y: 12, scale: 0.99 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.995 }}
            transition={{ type: "spring", stiffness: 190, damping: 24 }}
          >
            {screenComponents[screen]}
          </motion.div>
        </AnimatePresence>
      </div>
      <footer className="experience-footer">
        <span>
          <span className="mint-dot" /> FICTIONAL ARTIST · AMARA REED
        </span>
        <span>CLIENT-SIDE SIMULATION · NO REAL PROVIDER CONNECTIONS</span>
        <button onClick={openPalette}>
          <Keyboard size={13} /> SHORTCUTS <kbd>⌘ K</kbd>
        </button>
      </footer>
      {demoRunning && (
        <div className="demo-progress" role="status">
          <span>60 SECOND STORY</span>
          <div>
            <i
              style={{ width: `${Math.min(100, (demoElapsed / 60) * 100)}%` }}
            />
          </div>
          <strong>{Math.max(0, 60 - demoElapsed)}s</strong>
        </div>
      )}
      <AnimatePresence>
        {paletteOpen && (
          <motion.div
            className="palette-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) setPaletteOpen(false);
            }}
          >
            <motion.div
              className="command-palette"
              role="dialog"
              aria-modal="true"
              aria-label="Command palette"
              initial={{ opacity: 0, y: -14, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8 }}
            >
              <div className="palette-search">
                <Search size={17} />
                <input
                  ref={paletteRef}
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Jump to a screen or action…"
                  aria-label="Search commands"
                />
                <kbd>ESC</kbd>
                <button
                  aria-label="Close command palette"
                  onClick={() => setPaletteOpen(false)}
                >
                  <X size={16} />
                </button>
              </div>
              <div className="palette-section">
                <span>NAVIGATION</span>
                {filtered.map(({ id, title, icon: Icon }) => (
                  <button key={id} onClick={() => chooseScreen(id)}>
                    <Icon size={15} />
                    {title}
                    <span>↵</span>
                  </button>
                ))}
              </div>
              <div className="palette-section">
                <span>DEMO EVENTS</span>
                <button
                  onClick={() => {
                    void createGeneration("normal");
                    setPaletteOpen(false);
                  }}
                >
                  <Radio size={15} />
                  Simulate an in-scope generation<span>↵</span>
                </button>
                <button
                  onClick={() => {
                    void createGeneration("breach");
                    setPaletteOpen(false);
                  }}
                >
                  <ShieldAlert size={15} />
                  Trigger a scope breach<span>↵</span>
                </button>
                <button
                  onClick={() => {
                    demo();
                    setPaletteOpen(false);
                  }}
                >
                  <Sparkles size={15} />
                  Run the 60-second demo story<span>↵</span>
                </button>
              </div>
              <div className="palette-footer">
                <span>
                  <Command size={12} /> K to open
                </span>
                <span>ESC to close</span>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {notify && (
          <motion.div
            className="experience-toast"
            role="status"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
          >
            <Sparkles size={14} />
            {notify}
            <button
              aria-label="Dismiss notification"
              onClick={() => setNotify("")}
            >
              <X size={14} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
