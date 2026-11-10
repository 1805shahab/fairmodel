import type {
  Generation,
  Invoice,
  GenerationStatus,
} from "@/store/fairmodel-store";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Fictional preview terms only; the backend Decimal engine owns actual royalties.
// 5 cents/second for the first 30s, then 7.5 cents/second; round half up once.
export function sampleRoyaltyCents(seconds: number): number {
  if (!Number.isSafeInteger(seconds) || seconds < 0) {
    throw new Error(
      "Fictional sample duration must be a nonnegative whole number.",
    );
  }
  const halfCents = Math.min(seconds, 30) * 10 + Math.max(0, seconds - 30) * 15;
  return Math.floor((halfCents + 1) / 2);
}

export async function analyzeGeneration(
  generation: Generation,
): Promise<GenerationStatus> {
  await wait(650 + Math.random() * 650);
  if (
    generation.region === "Brazil" ||
    generation.category.toLowerCase() === "gambling"
  )
    return "breach";
  if (generation.durationSeconds > 30) return "overage";
  return "approved";
}

export async function createInvoice(generation: Generation): Promise<Invoice> {
  if (
    !generation.artistApproved ||
    !["approved", "overage"].includes(generation.status) ||
    generation.amountCents <= 0
  ) {
    throw new Error(
      "Only artist-approved permitted sample usage can receive a simulated invoice.",
    );
  }
  await wait(450);
  return {
    id: `SIMULATED-${generation.id}`,
    generationId: generation.id,
    amountCents: generation.amountCents,
    status: "REVIEW_REQUIRED",
    createdAt: new Date().toISOString(),
    simulated: true,
  };
}

export async function sendPayout(invoice: Invoice): Promise<string> {
  if (
    !["APPROVED", "SENT"].includes(invoice.status) ||
    invoice.amountCents <= 0
  ) {
    throw new Error("An approved positive simulated invoice is required.");
  }
  await wait(900);
  return `SIMULATED-PAYMENT-${invoice.generationId}`;
}
