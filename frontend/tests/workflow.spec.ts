import { test, expect } from "@playwright/test";
import path from "node:path";
const fixtures = path.resolve(__dirname, "../../backend/fixtures");

test("artist and studio complete the real-media local fixture workflow", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Every voice deserves/ }),
  ).toBeVisible();
  await page.getByRole("link", { name: /Enter demo workspace/ }).click();
  await expect(
    page.getByRole("heading", { name: "Good to see you, Amara." }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "New voice license", exact: true })
    .click();
  await page
    .getByLabel("Agreement name")
    .fill(`Browser campaign ${Date.now()}`);
  await page
    .getByLabel("Licensing agreement PDF", { exact: true })
    .setInputFiles(path.join(fixtures, "sample-license.pdf"));
  await page.getByRole("button", { name: /Upload & continue/ }).click();
  await expect(
    page.getByRole("button", { name: "Extract terms" }),
  ).toBeVisible();
  await page.getByLabel(/Use local demo fixture/).check();
  await page.getByRole("button", { name: "Extract terms" }).click();
  await expect(page.getByLabel("Voice artist", { exact: true })).toHaveValue(
    "Amara Reed",
  );
  // List editing preserves separator keystrokes.
  const media = page.getByLabel("Permitted media", { exact: true });
  await media.fill("online advertising, podcast");
  await expect(media).toHaveValue("online advertising, podcast");
  await media.fill("online advertising");
  await page
    .getByLabel("Review note")
    .fill("Reviewed source pages and confirmed all fixture license terms.");
  await page.getByRole("button", { name: "Approve & activate" }).click();
  await expect(
    page.getByText("Artist-approved agreement.", { exact: false }),
  ).toBeVisible();
  const licenseId = page.url().split("/").pop();
  await page
    .getByRole("combobox", { name: "Demo persona" })
    .selectOption("studio");
  await expect(
    page.getByRole("combobox", { name: "Demo persona" }),
  ).toHaveValue("studio");
  await page
    .getByRole("link", { name: "Audio submissions", exact: true })
    .click();
  await page
    .getByRole("link", { name: "Submit audio", exact: true })
    .first()
    .click();
  await page.getByLabel("Approved voice license").selectOption(licenseId!);
  await page
    .getByLabel("Campaign name", { exact: true })
    .fill("Browser verified launch");
  await page.getByLabel("Intended use date").fill("2026-11-06");
  await page.getByLabel("Declared country / region").fill("US");
  await page.getByLabel("Platform / medium").fill("online advertising");
  await page.getByLabel("Declared language").fill("English");
  await page.getByLabel("Campaign category").fill("consumer products");
  await page
    .getByLabel("Campaign audio", { exact: true })
    .setInputFiles(path.join(fixtures, "sample-narration.wav"));
  await page.getByRole("button", { name: "Upload audio", exact: true }).click();
  await page.getByLabel(/Explicit local fixture mode/).check();
  await page
    .getByRole("button", { name: "Analyze audio", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Transcript & timestamps" }),
  ).toBeVisible();
  await expect(page.locator("audio")).toBeVisible();
  await page.getByLabel(/Explicit local fixture mode/).check();
  await page
    .getByRole("button", { name: "Evaluate compliance", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Compliance report", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("additional royalty due", { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Demo persona" })
    .selectOption("artist");
  await expect(
    page.getByRole("combobox", { name: "Demo persona" }),
  ).toHaveValue("artist");
  await page.getByRole("link", { name: "Royalties", exact: true }).click();
  const pending = page
    .locator(".royalty-card")
    .filter({
      has: page.getByRole("button", { name: "Approve charge", exact: true }),
    })
    .first();
  await pending
    .getByLabel("Approval / rejection note")
    .fill("Approved measured speech and checked the source agreement.");
  await pending
    .getByRole("button", { name: "Approve charge", exact: true })
    .click();
  await page
    .getByRole("button", {
      name: "Create / open simulated invoice",
      exact: true,
    })
    .first()
    .click();
  await page
    .getByRole("link", { name: "Invoices & payments", exact: true })
    .click();
  const paymentSteps = page.getByRole("list", {
    name: "Simulated payment demonstration steps",
  });
  await expect(paymentSteps).toBeVisible();
  await expect(paymentSteps).toContainText(
    "Approves the royalty, then simulates sending the invoice.",
  );
  await expect(paymentSteps).toContainText(
    "Simulates payment completion; no funds move.",
  );
  await expect(
    page.getByRole("link", { name: "See PayPal Sandbox status" }),
  ).toBeVisible();
  const draft = page
    .locator(".invoice-card")
    .filter({
      has: page.getByRole("button", {
        name: "Simulate sending invoice",
        exact: true,
      }),
    })
    .first();
  await draft
    .getByRole("button", { name: "Simulate sending invoice", exact: true })
    .click();
  await page
    .getByRole("combobox", { name: "Demo persona" })
    .selectOption("studio");
  await expect(
    page.getByRole("combobox", { name: "Demo persona" }),
  ).toHaveValue("studio");
  await page
    .getByRole("button", { name: "Simulate payment completion", exact: true })
    .first()
    .click();
  await expect(
    page.getByText("paid simulated", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page
      .getByText("DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED", {
        exact: true,
      })
      .first(),
  ).toBeVisible();
  await page.getByRole("link", { name: "Analytics", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Royalty ledger" }),
  ).toBeVisible();
  await expect(page.locator(".ag-root")).toBeVisible();
  await page.screenshot({
    path: "test-results/analytics-desktop.png",
    fullPage: true,
  });
});

test("mobile navigation, persona persistence and provider errors", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/dashboard");
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await page
    .getByRole("link", { name: "Demo & integrations", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Demo & integrations", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Intentionally deferred", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Demo persona" })
    .selectOption("studio");
  await expect(
    page.getByRole("combobox", { name: "Demo persona" }),
  ).toHaveValue("studio");
  await page.reload();
  await expect(
    page.getByRole("combobox", { name: "Demo persona" }),
  ).toHaveValue("studio");
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Let’s create responsibly." }),
  ).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflow).toBe(false);
  await page.screenshot({
    path: "test-results/dashboard-mobile.png",
    fullPage: true,
  });
  await page.route("**/api/backend/analytics", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Test API unavailable" }),
    }),
  );
  await page.reload();
  await expect(
    page.getByRole("alert").filter({ hasText: "Test API unavailable" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Retry", exact: true }),
  ).toBeVisible();
  await page.unroute("**/api/backend/analytics");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Test API unavailable" }),
  ).toHaveCount(0);
});
