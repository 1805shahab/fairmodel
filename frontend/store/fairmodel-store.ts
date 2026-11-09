import { create } from "zustand";
import { analyzeGeneration, createInvoice, sendPayout } from "@/lib/mock/api";

export type Screen = "hero" | "contract" | "control" | "audit" | "ledger";
export type GenerationStatus = "analyzing" | "approved" | "overage" | "breach";
export type InvoiceStatus = "REVIEW_REQUIRED" | "APPROVED" | "SENT" | "PAID_SIMULATED";
export type Role = "talent" | "studio";

export interface Generation {
  id: string;
  studio: string;
  assetType: string;
  durationSeconds: number;
  region: string;
  category: string;
  medium: string;
  transcript: string[];
  status: GenerationStatus;
  amountCents: number;
  createdAt: string;
  artistApproved: boolean;
}

export interface Invoice {
  id: string;
  generationId: string;
  amountCents: number;
  status: InvoiceStatus;
  createdAt: string;
  paypalDemo: true;
  transactionId?: string;
}

interface FairModelState {
  screen: Screen;
  role: Role;
  generations: Generation[];
  invoices: Invoice[];
  selectedGenerationId: string;
  contractVerified: boolean;
  breachActive: boolean;
  audioLevel: number;
  eventPulse: number;
  soundEnabled: boolean;
  demoRunning: boolean;
  demoElapsed: number;
  notify: string;
  setScreen: (screen: Screen) => void;
  setRole: (role: Role) => void;
  selectGeneration: (id: string) => void;
  setAudioLevel: (level: number) => void;
  recoverBreach: () => void;
  setSoundEnabled: (enabled: boolean) => void;
  setNotify: (message: string) => void;
  ingestContract: () => void;
  completeContract: () => void;
  createGeneration: (kind?: "normal" | "overage" | "breach") => Promise<string>;
  approveGeneration: (id: string) => void;
  approveInvoice: (id: string) => void;
  releasePayout: (id: string) => Promise<void>;
  releaseBatch: (ids: string[]) => Promise<void>;
  runDemo: () => void;
  stopDemo: () => void;
}

const initialGenerations: Generation[] = [
  {
    id: "GEN-1042",
    studio: "Northstar Studio",
    assetType: "Social reel",
    durationSeconds: 18,
    region: "United States",
    category: "Lifestyle",
    medium: "Social reel",
    transcript: ["The sound of a slower morning.", "Made for your everyday."],
    status: "approved",
    amountCents: 90,
    createdAt: new Date(Date.now() - 3_600_000).toISOString(),
    artistApproved: false,
  },
  {
    id: "GEN-1041",
    studio: "Goodwell Audio",
    assetType: "Digital spot",
    durationSeconds: 24,
    region: "United Kingdom",
    category: "Wellness",
    medium: "Digital video",
    transcript: ["A little more room to breathe."],
    status: "approved",
    amountCents: 120,
    createdAt: new Date(Date.now() - 7_200_000).toISOString(),
    artistApproved: true,
  },
  {
    id: "GEN-1040",
    studio: "Northstar Studio",
    assetType: "Podcast intro",
    durationSeconds: 34,
    region: "Canada",
    category: "Lifestyle",
    medium: "Podcast",
    transcript: ["Find your own kind of balance."],
    status: "overage",
    amountCents: 255,
    createdAt: new Date(Date.now() - 15_000_000).toISOString(),
    artistApproved: true,
  },
];

const regions = ["United States", "Canada", "United Kingdom", "United States"];
const studios = ["Northstar Studio", "Goodwell Audio", "Morrow Creative", "Little Current"];
const categories = ["Lifestyle", "Wellness", "Travel", "Home"];
const transcriptOptions = [
  ["A better rhythm for every day.", "Find your own kind of balance."],
  ["Make space for what matters.", "The little things sound different."],
  ["A new way to feel at home.", "Take a moment for yourself."],
  ["Made for wherever life takes you.", "Hear what feels like you."],
];

let engineTimer: ReturnType<typeof setTimeout> | undefined;
let breachTimer: ReturnType<typeof setTimeout> | undefined;
let demoTimers: ReturnType<typeof setTimeout>[] = [];
let generationSequence = 1043;

export const useFairModel = create<FairModelState>((set, get) => ({
  screen: "hero",
  role: "talent",
  generations: initialGenerations,
  invoices: [],
  selectedGenerationId: initialGenerations[0].id,
  contractVerified: false,
  breachActive: false,
  audioLevel: 0,
  eventPulse: 0,
  soundEnabled: false,
  demoRunning: false,
  demoElapsed: 0,
  notify: "",
  setScreen: (screen) => set({ screen }),
  setRole: (role) => set({ role }),
  selectGeneration: (id) => set({ selectedGenerationId: id, screen: "audit" }),
  setAudioLevel: (audioLevel) => set({ audioLevel }),
  recoverBreach: () => set({ breachActive: false, notify: "Scope returned to calm. The breach remains in the audit trail." }),
  setSoundEnabled: (soundEnabled) => set({ soundEnabled }),
  setNotify: (notify) => set({ notify }),
  ingestContract: () => {
    set({ contractVerified: true, screen: "contract", notify: "Sample license scope verified." });
  },
  completeContract: () => set({ screen: "control", notify: "Contract shell locked. Live scope monitoring is on." }),
  createGeneration: async (kind = "normal") => {
    const seed = Math.floor(Math.random() * transcriptOptions.length);
    const id = `GEN-${generationSequence++}`;
    const now = new Date();
    const generation: Generation = {
      id,
      studio: kind === "breach" ? "Morrow Creative" : studios[seed],
      assetType: ["Social reel", "Digital spot", "Podcast intro"][seed % 3],
      durationSeconds: kind === "overage" ? 37 : kind === "breach" ? 22 : 14 + (seed * 7) % 14,
      region: kind === "breach" ? "Brazil" : regions[seed],
      category: kind === "breach" ? "Gambling" : categories[seed],
      medium: ["Social reel", "Digital video", "Podcast"][seed % 3],
      transcript: kind === "breach"
        ? ["Try your luck tonight.", "A regional variation for Brazil."]
        : transcriptOptions[seed],
      status: "analyzing",
      amountCents: 0,
      createdAt: now.toISOString(),
      artistApproved: false,
    };
    set((state) => ({
      generations: [generation, ...state.generations].slice(0, 40),
      selectedGenerationId: id,
      breachActive: kind === "breach",
      eventPulse: state.eventPulse + 1,
    }));

    const status = kind === "breach" ? "breach" : await analyzeGeneration(generation);
    const amountCents = status === "breach"
      ? generation.durationSeconds * 5
      : status === "overage"
        ? (generation.durationSeconds - 30) * 5 + 150
        : Math.max(50, Math.round(generation.durationSeconds * 5));
    const analyzed = { ...generation, status, amountCents };
    set((state) => ({
      generations: state.generations.map((item) => item.id === id ? analyzed : item),
      breachActive: status === "breach",
      eventPulse: state.eventPulse + 1,
      notify: status === "breach"
        ? "Scope breach detected. No charge is created without talent review."
        : status === "overage"
          ? "Overage tier reached. Review the proposed royalty."
          : "Usage is within scope. Review the estimated royalty.",
    }));
    if (status === "breach") {
      const invoice = await createInvoice(analyzed);
      set((state) => ({ invoices: [invoice, ...state.invoices] }));
    }
    return id;
  },
  approveGeneration: (id) => set((state) => ({
    generations: state.generations.map((item) => item.id === id ? { ...item, artistApproved: true } : item),
    invoices: state.invoices.map((item) => item.generationId === id && item.status === "REVIEW_REQUIRED"
      ? { ...item, status: "APPROVED" }
      : item),
    notify: "Talent review recorded. This demo moves no funds.",
  })),
  approveInvoice: (id) => set((state) => ({
    invoices: state.invoices.map((invoice) => invoice.id === id ? { ...invoice, status: "APPROVED" } : invoice),
    notify: "Invoice approved in the local demo.",
  })),
  releasePayout: async (id) => {
    const invoice = get().invoices.find((item) => item.id === id);
    if (!invoice || invoice.status !== "APPROVED") return;
    const transactionId = await sendPayout(invoice);
    set((state) => ({
      invoices: state.invoices.map((item) => item.id === id
        ? { ...item, status: "PAID_SIMULATED", transactionId }
        : item),
      generations: state.generations.map((item) => item.id === invoice.generationId
        ? { ...item, artistApproved: true }
        : item),
      notify: `Simulated payout ${transactionId} recorded. No funds transferred.`,
    }));
  },
  releaseBatch: async (ids) => {
    const selected = get().generations.filter((item) => ids.includes(item.id) && item.artistApproved);
    if (!selected.length) return;
    const settled: Invoice[] = [];
    for (const generation of selected) {
      const invoice = await createInvoice(generation);
      const transactionId = await sendPayout(invoice);
      settled.push({ ...invoice, status: "PAID_SIMULATED", transactionId });
    }
    set((state) => ({
      invoices: [...settled, ...state.invoices],
      generations: state.generations.map((item) => ids.includes(item.id)
        ? { ...item, artistApproved: true }
        : item),
      notify: `Recorded ${settled.length} simulated payout${settled.length === 1 ? "" : "s"}. No funds transferred.`,
    }));
  },
  runDemo: () => {
    get().stopDemo();
    set({ demoRunning: true, demoElapsed: 0, screen: "contract", notify: "60-second story started." });
    get().ingestContract();
    demoTimers.push(setTimeout(() => get().completeContract(), 1_800));
    demoTimers = [
      setTimeout(() => void get().createGeneration("normal"), 3_000),
      setTimeout(() => void get().createGeneration("normal"), 10_000),
      setTimeout(() => void get().createGeneration("overage"), 18_000),
      setTimeout(() => void get().createGeneration("normal"), 27_000),
      setTimeout(() => void get().createGeneration("breach"), 38_000),
      setTimeout(() => {
        const breach = get().generations.find((item) => item.status === "breach" && !item.artistApproved);
        if (breach) get().approveGeneration(breach.id);
        set({ screen: "ledger" });
      }, 48_000),
      setTimeout(() => {
        const invoice = get().invoices.find((item) => item.status === "APPROVED");
        if (invoice) void get().releasePayout(invoice.id);
      }, 53_000),
      setTimeout(() => set({ demoRunning: false, demoElapsed: 60, screen: "ledger", notify: "Demo story complete. Explore the ledger or replay." }), 60_000),
    ];
    for (let second = 1; second <= 60; second += 1) {
      demoTimers.push(setTimeout(() => set({ demoElapsed: second }), second * 1000));
    }
  },
  stopDemo: () => {
    demoTimers.forEach(clearTimeout);
    demoTimers = [];
    set({ demoRunning: false });
  },
}));

export function startSimulationEngine() {
  if (engineTimer) return;
  const scheduleGeneration = () => {
    engineTimer = setTimeout(() => {
      const { demoRunning } = useFairModel.getState();
      if (!demoRunning) void useFairModel.getState().createGeneration(Math.random() < 0.18 ? "overage" : "normal");
      scheduleGeneration();
    }, 3_000 + Math.random() * 3_000);
  };
  const scheduleBreach = () => {
    breachTimer = setTimeout(() => {
      if (!useFairModel.getState().demoRunning) void useFairModel.getState().createGeneration("breach");
      scheduleBreach();
    }, 40_000);
  };
  scheduleGeneration();
  scheduleBreach();
}

export function stopSimulationEngine() {
  if (engineTimer) clearTimeout(engineTimer);
  if (breachTimer) clearTimeout(breachTimer);
  engineTimer = undefined;
  breachTimer = undefined;
}
