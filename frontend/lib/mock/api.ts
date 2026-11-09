import type { Generation, Invoice, GenerationStatus } from "@/store/fairmodel-store";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function analyzeGeneration(generation: Generation): Promise<GenerationStatus> {
  await wait(650 + Math.random() * 650);
  if (generation.region === "Brazil" || generation.category === "gambling") return "breach";
  if (generation.durationSeconds > 30) return "overage";
  return "approved";
}

export async function createInvoice(generation: Generation): Promise<Invoice> {
  await wait(450);
  return {
    id: `INV-${Math.random().toString(36).slice(2, 8).toUpperCase()}`,
    generationId: generation.id,
    amountCents: generation.amountCents,
    status: "REVIEW_REQUIRED",
    createdAt: new Date().toISOString(),
    paypalDemo: true,
  };
}

export async function sendPayout(invoice: Invoice): Promise<string> {
  await wait(900);
  return `DEMO-${invoice.id.replace("INV-", "")}-${Date.now().toString().slice(-4)}`;
}
