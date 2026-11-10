import { test, expect } from "@playwright/test";
import { createInvoice, sampleRoyaltyCents } from "../lib/mock/api";
import type { Generation } from "../store/fairmodel-store";

test("fictional preview rates round in cents and restricted samples never receive invoices", async () => {
  expect([0, 18, 30, 34, 37].map(sampleRoyaltyCents)).toEqual([
    0, 90, 150, 180, 203,
  ]);
  expect(() => sampleRoyaltyCents(-1)).toThrow();
  expect(() => sampleRoyaltyCents(23.52)).toThrow();
  const sample: Generation = {
    id: "GEN-TEST",
    studio: "Fictional studio",
    assetType: "Fictional ad",
    durationSeconds: 37,
    region: "United States",
    category: "Lifestyle",
    medium: "Digital video",
    transcript: ["Fictional sample."],
    status: "overage",
    amountCents: 203,
    createdAt: "2026-11-09T00:00:00Z",
    artistApproved: true,
  };
  await expect(
    createInvoice({ ...sample, status: "breach" }),
  ).rejects.toThrow();
  await expect(
    createInvoice({ ...sample, artistApproved: false }),
  ).rejects.toThrow();
  await expect(createInvoice({ ...sample, amountCents: 0 })).rejects.toThrow();
  const first = await createInvoice(sample);
  const retry = await createInvoice(sample);
  expect(first.id).toBe("SIMULATED-GEN-TEST");
  expect(retry.id).toBe(first.id);
  expect(first.simulated).toBe(true);
});
