import { test, expect } from "@playwright/test";
import path from "node:path";
import { readFileSync } from "node:fs";

test("public walkthrough is keyboard operated, reduced-motion safe and connected to the app", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator("h1")).toHaveCSS("animation-name", "none");
  await page.getByRole("tab", { name: /01.*License/ }).focus();
  await page.keyboard.press("End");
  await expect(page.getByRole("tab", { name: /05.*Invoice/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByRole("tabpanel")).toContainText(
    "PayPal Sandbox invoices",
  );
  await page.getByRole("link", { name: "Explore invoices & payments" }).click();
  await expect(page).toHaveURL(/\/dashboard\/invoices$/);
  await expect(
    page.getByRole("combobox", { name: "Workspace role" }),
  ).toBeVisible();
});

test("file chooser rejects bad formats and drag-drop retains native validation", async ({
  page,
}) => {
  await page.goto("/dashboard/licenses/new");
  await expect(page.getByLabel("Agreement name", { exact: true })).toHaveCSS(
    "background-color",
    "rgb(16, 23, 34)",
  );
  await expect(page.getByLabel("Agreement name", { exact: true })).toHaveCSS(
    "color",
    "rgb(237, 242, 248)",
  );
  const chooser = page.getByLabel("Licensing agreement PDF", { exact: true });
  await chooser.setInputFiles({
    name: "wrong.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Not a PDF"),
  });
  await expect(page.locator(".file-dropzone").getByRole("alert")).toContainText(
    "Choose .pdf files only.",
  );
  const bytes = Array.from(
    readFileSync(
      path.resolve(__dirname, "../../backend/fixtures/sample-license.pdf"),
    ),
  );
  const transfer = await page.evaluateHandle((data) => {
    const dt = new DataTransfer();
    dt.items.add(
      new File([new Uint8Array(data)], "sample-license.pdf", {
        type: "application/pdf",
      }),
    );
    return dt;
  }, bytes);
  await page
    .locator(".file-dropzone")
    .dispatchEvent("drop", { dataTransfer: transfer });
  await expect(page.locator(".file-dropzone").getByRole("alert")).toHaveCount(
    0,
  );
  await expect(page.locator(".file-dropzone strong")).toHaveText(
    "sample-license.pdf",
  );
  expect(
    await chooser.evaluate((input: HTMLInputElement) => input.files?.[0].name),
  ).toBe("sample-license.pdf");
  await chooser.setInputFiles([]);
  expect(
    await chooser.evaluate(
      (input: HTMLInputElement) => input.validity.valueMissing,
    ),
  ).toBe(true);
  await expect(page.locator(".file-dropzone strong")).toHaveText(
    "Drop a file here, or browse",
  );
});

test("analytics keeps four KPIs aligned and links state/currency/search filters to the grid", async ({
  page,
}) => {
  const rows = [
    {
      id: "ui-a",
      currency: "USD",
      status: "PROPOSED",
      campaign_name: "Proposed US example",
    },
    {
      id: "ui-b",
      currency: "USD",
      status: "APPROVED",
      campaign_name: "Approved US example",
    },
    {
      id: "ui-c",
      currency: "EUR",
      status: "APPROVED",
      campaign_name: "Approved EU example",
    },
  ].map((row) => ({
    ...row,
    amount: "30.00",
    artist_name: "UI fixture artist",
    studio_name: "UI fixture studio",
    license_title: "UI fixture license",
    created_at: "2026-11-10T00:00:00Z",
    calculation: {
      spoken_seconds: "45",
      additional_seconds: "15",
      billing_basis: "per_asset",
    },
  }));
  await page.route("**/api/backend/analytics", (route) =>
    route.fulfill({
      json: {
        rows,
        totals_by_currency: {
          USD: {
            proposed: "30",
            approved: "30",
            paid_simulated: "0",
            paid_sandbox: "0",
          },
          EUR: {
            proposed: "0",
            approved: "30",
            paid_simulated: "0",
            paid_sandbox: "0",
          },
        },
      },
    }),
  );
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/dashboard/analytics");
  const tops = await page
    .getByRole("region", { name: "USD ledger totals" })
    .locator(".stat-card")
    .evaluateAll((items) =>
      items.map((item) => item.getBoundingClientRect().top),
    );
  expect(tops).toHaveLength(4);
  expect(new Set(tops).size).toBe(1);
  await page
    .getByRole("combobox", { name: "Ledger currency" })
    .selectOption("USD");
  await page.getByRole("button", { name: "approved 1", exact: true }).click();
  await expect(
    page.getByText("1 approved entry in USD.", { exact: true }),
  ).toBeVisible();
  await page.getByRole("grid").scrollIntoViewIfNeeded();
  await expect(
    page.getByRole("gridcell", { name: "Approved US example", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("gridcell", { name: "Proposed US example", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Clear ledger filters" }).click();
  await page
    .getByRole("searchbox", { name: "Find in ledger" })
    .fill("Approved EU");
  await expect(
    page.getByRole("gridcell", { name: "Approved EU example", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("gridcell", { name: "Approved US example", exact: true }),
  ).toHaveCount(0);
});
