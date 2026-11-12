import { test, expect, type APIRequestContext } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import type { Passport } from "../components/passport-types";

const fixture = (name: string) =>
  readFileSync(path.resolve(__dirname, "../../backend/fixtures", name));
let assetId = "",
  licenseId = "",
  invoiceId = "";
async function checked(
  request: APIRequestContext,
  url: string,
  options: Parameters<APIRequestContext["post"]>[1],
) {
  const response = await request.post(url, options);
  expect(response.ok(), await response.text()).toBeTruthy();
  return response.json();
}
test.beforeAll(async ({ request }) => {
  const integrations = await (
    await request.get("/api/backend/integrations")
  ).json();
  expect(
    integrations.payment_provider,
    "These tests require the isolated QA mock backend",
  ).toBe("mock");
  await checked(request, "/api/persona", { data: { persona: "artist_demo" } });
  const license = await checked(request, "/api/backend/licenses", {
    data: {
      title: `Passport browser fixture ${Date.now()}`,
      studio_id: "studio_demo",
    },
  });
  licenseId = license.id;
  await checked(request, `/api/backend/licenses/${licenseId}/contract`, {
    multipart: {
      file: {
        name: "sample-license.pdf",
        mimeType: "application/pdf",
        buffer: fixture("sample-license.pdf"),
      },
    },
  });
  const extracted = await checked(
    request,
    `/api/backend/licenses/${licenseId}/extract`,
    { data: { use_demo_fixture: true } },
  );
  await checked(request, `/api/backend/licenses/${licenseId}/approve`, {
    data: {
      terms: extracted.terms,
      expected_version: extracted.version,
      note: "Explicit fixture-only automated review; not a real artist identity.",
    },
  });
  await checked(request, "/api/persona", { data: { persona: "studio_demo" } });
  const asset = await checked(request, "/api/backend/assets", {
    multipart: {
      license_id: licenseId,
      campaign: JSON.stringify({
        name: "Passport fixture launch",
        region: "US",
        medium: "online advertising",
        language: "English",
        category: "consumer products",
        intended_use_date: "2026-11-06",
      }),
      file: {
        name: "sample-narration.wav",
        mimeType: "audio/wav",
        buffer: fixture("sample-narration.wav"),
      },
    },
  });
  assetId = asset.id;
  await checked(request, `/api/backend/assets/${assetId}/analyze`, {
    data: { use_demo_fixture: true },
  });
  await checked(request, "/api/persona", { data: { persona: "artist_demo" } });
  await checked(request, `/api/backend/assets/${assetId}/authorization`, {
    data: {
      identity_confirmed: true,
      use_authorized: true,
      note: "Automated fictional fixture attestation, not biometric proof or a real artist decision.",
    },
  });
  await checked(request, `/api/backend/assets/${assetId}/evaluate`, {
    data: { use_demo_fixture: true },
  });
  const detail = await (
    await request.get(`/api/backend/assets/${assetId}`)
  ).json();
  expect(detail.royalty.amount).toBe("57.54");
  await checked(
    request,
    `/api/backend/royalties/${detail.royalty.id}/decision`,
    {
      data: {
        approve: true,
        note: "Automated test-only fixture charge approval; no real payment.",
      },
    },
  );
  const invoice = await checked(
    request,
    `/api/backend/royalties/${detail.royalty.id}/invoice`,
    { data: {} },
  );
  expect(invoice.simulated).toBe(true);
  invoiceId = invoice.id;
});

test("private passport uses saved evidence, genuine citations and print-safe snapshot", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`/dashboard/submissions/${assetId}/passport`);
  await expect(
    page.getByRole("heading", { name: "Voice Usage Passport", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("VP-" + assetId.toUpperCase(), { exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/not a legal certificate/)).toBeVisible();
  await expect(
    page.getByText("Simulated invoice ID", { exact: true }),
  ).toHaveCount(1);
  await expect(
    page.getByText("PayPal Sandbox invoice ID", { exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: /medium.*satisfied/ }).click();
  const selected = page.getByRole("article", { name: "Selected evidence" });
  await expect(
    selected.getByRole("link", { name: /Open source page/ }),
  ).toHaveAttribute("href", /#page=\d+/);
  await expect(selected.locator("blockquote").first()).not.toBeEmpty();
  for (const width of [1440, 1024, 768, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
  }
  await page.emulateMedia({ media: "print" });
  await expect(
    page.getByRole("heading", {
      name: "Complete compliance evidence snapshot",
    }),
  ).toBeVisible();
  await expect(page.locator(".stage-header")).toBeHidden();
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(255, 255, 255)",
  );
  await page.pdf({
    path: test.info().outputPath("private-passport.pdf"),
    format: "A4",
    printBackground: true,
  });
  expect(errors).toEqual([]);
});

test("artist concern, studio response and resolution preserve the invoice and hold stale approval", async ({
  page,
}) => {
  await page.goto(`/dashboard/reviews?asset=${assetId}`);
  await page.getByLabel("Artist decision").selectOption("INVESTIGATE");
  await page
    .getByLabel("Supporting evidence reference (optional)")
    .selectOption("contract:additional_rate");
  await page
    .getByLabel("Required review note")
    .fill(
      "Please confirm this rate allocation before sending this fictional test invoice.",
    );
  await page.getByRole("button", { name: "Record artist decision" }).click();
  const thread = page.locator(".case-thread").first();
  await expect(thread).toContainText("New financial approvals are held");
  const rows = await (
    await page.request.get("/api/backend/review-cases")
  ).json();
  const row = rows.find((r: { asset_id: string }) => r.asset_id === assetId);
  await page
    .getByRole("combobox", { name: "Workspace role" })
    .selectOption("studio");
  await expect(page.getByLabel("Artist decision")).toHaveCount(0);
  expect(
    (
      await page.request.post(`/api/backend/review-cases/${row.id}/events`, {
        data: {
          request_key: "studio-cannot-resolve-01",
          kind: "RESOLVE",
          note: "Studio must not resolve an artist concern.",
        },
      })
    ).status(),
  ).toBe(403);
  await thread
    .getByRole("textbox")
    .fill(
      "Studio confirms the declared usage and requests artist review of the supporting clause.",
    );
  await thread.getByRole("button", { name: "Record response" }).click();
  await expect(thread).toContainText("Studio confirms the declared usage");
  await page
    .getByRole("combobox", { name: "Workspace role" })
    .selectOption("artist");
  await expect(page.getByLabel("Artist decision")).toBeVisible();
  await thread
    .getByRole("textbox")
    .fill(
      "Artist reviewed this fictional response and resolved the test concern.",
    );
  await thread.getByRole("button", { name: "Resolve concern" }).click();
  await page.getByLabel("Case status").selectOption("RESOLVED");
  await expect(page.locator(".case-thread").first()).toContainText(
    "Artist reviewed this fictional response",
  );
  await page.reload();
  const invoice = await (
    await page.request.get(`/api/backend/invoices/${invoiceId}`)
  ).json();
  expect(invoice.amount).toBe("57.54");
  expect(invoice.status).toBe("DRAFT");
  expect(
    (
      await page.request.post(`/api/backend/invoices/${invoiceId}/send`, {
        data: { event_key: "held-after-dispute-test" },
      })
    ).status(),
  ).toBe(409);
});

test("studio simulator calculates immediately with no usage or invoice writes", async ({
  page,
}) => {
  await page.request.post("/api/persona", { data: { persona: "studio_demo" } });
  const before = await Promise.all(
    ["assets", "royalties", "invoices"].map(
      async (name) =>
        (await (await page.request.get(`/api/backend/${name}`)).json()).length,
    ),
  );
  const writes: string[] = [];
  page.on("request", (request) => {
    if (
      request.method() !== "GET" &&
      /\/api\/backend\/(assets|royalties|invoices|paypal)/.test(request.url())
    )
      writes.push(request.url());
  });
  await page.goto("/dashboard/simulator");
  await page.getByLabel("Approved agreement").selectOption(licenseId);
  await page
    .getByLabel("Intended campaign", { exact: true })
    .fill("Preview only launch");
  await page.getByLabel("Declared campaign category").fill("consumer products");
  for (const [seconds, amount] of [
    ["20", "$0.00"],
    ["30", "$0.00"],
    ["45", "$30.00"],
    ["58.77", "$57.54"],
  ]) {
    await page
      .getByLabel("Estimated spoken duration", { exact: true })
      .fill(seconds);
    await expect(page.locator(".estimate-result .passport-amount")).toHaveText(
      amount,
    );
  }
  await page.getByLabel("Estimated spoken duration", { exact: true }).fill("");
  await expect(page.locator(".estimate-result .passport-amount")).toHaveCount(
    0,
  );
  expect(writes).toEqual([]);
  const after = await Promise.all(
    ["assets", "royalties", "invoices"].map(
      async (name) =>
        (await (await page.request.get(`/api/backend/${name}`)).json()).length,
    ),
  );
  expect(after).toEqual(before);
});

test("evidence explorer seeks only a valid supplied containing transcript segment", async ({
  page,
}) => {
  // This test adds explicitly synthetic timestamps in an intercepted response only.
  // The actual fixture has no timestamps; persisted media/evidence is unchanged.
  const original: Passport = await (
    await page.request.get(`/api/backend/assets/${assetId}/passport`)
  ).json();
  const audio = original.asset.analysis!.result,
    report = original.asset.report!.result;
  const passage = audio.transcript.split(" ").slice(0, 8).join(" ");
  audio.timestamps = [{ start: 1, end: 5, text: passage }];
  report.findings.findings = [
    {
      category: "Synthetic timestamp test",
      passage,
      explanation: "Explicit browser-only fixture",
      possible_conflict: false,
      needs_review: false,
    },
    {
      category: "Missing timestamp test",
      passage: "This excerpt is not present in a timestamped segment.",
      explanation: "No timestamp can be inferred",
      possible_conflict: false,
      needs_review: true,
    },
  ];
  await page.route(`**/api/backend/assets/${assetId}/passport`, (route) =>
    route.fulfill({ json: original }),
  );
  await page.goto(`/dashboard/submissions/${assetId}/passport`);
  await page.getByRole("button", { name: /Synthetic timestamp test/ }).click();
  await page
    .getByRole("button", { name: "Seek containing segment at 1.00s" })
    .click();
  await expect
    .poll(() =>
      page
        .locator("audio")
        .evaluate((audio: HTMLAudioElement) => audio.currentTime),
    )
    .toBeCloseTo(1, 1);
  await page.getByRole("button", { name: /Missing timestamp test/ }).click();
  await expect(
    page.getByRole("button", { name: /Seek containing segment/ }),
  ).toHaveCount(0);
});
