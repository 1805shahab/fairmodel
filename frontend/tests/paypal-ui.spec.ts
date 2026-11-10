import { test, expect } from "@playwright/test";

const configuration = {
  demo_mode: true,
  payment_provider: "paypal_sandbox",
  payment_notice: "PAYPAL SANDBOX — TEST TRANSACTION — NO REAL MONEY",
  gemini: { configured: false, model: "test" },
  groq: { configured: false, model: "test" },
  audio_tools: { ffmpeg: true, ffprobe: true },
  speaker_verification: { enabled: false, status: "disabled" },
  paypal: "Test-intercepted Sandbox UI",
  fixtures_available: false,
  paypal_configuration: {
    credentials_configured: false,
    merchant_configured: true,
    buyer_configured: true,
    drafts_enabled: true,
    sending_enabled: true,
    webhook_configured: false,
  },
};

test("Sandbox invoice UI requires send approval and separates partial, pending and paid states", async ({
  page,
}) => {
  let sendCalls = 0,
    refreshes = 0;
  const invoice = {
    id: "ui-sandbox",
    royalty_id: "ui-royalty",
    provider_id: "INV2-MOCK-UI-TEST",
    provider: "paypal_sandbox",
    simulated: false,
    amount: "30.00",
    currency: "USD",
    recipient: "buyer@personal.example.com",
    status: "DRAFT",
    created_at: "2026-11-09T00:00:00Z",
    eligible_for_send: true,
    notice: configuration.payment_notice,
    events: [],
    sandbox: {
      issuer: "merchant@business.example.com",
      invoice_number: "FM-UI-TEST",
      provider_status: "DRAFT",
      payment_url: null as string | null,
      due_date: null,
      paid_amount: "0.00",
      due_amount: "30.00",
      refunded_amount: "0.00",
      last_synced_at: "2026-11-09T00:00:00Z",
      error: null,
      transactions: [],
    },
  };
  await page.route("**/api/backend/integrations", (route) =>
    route.fulfill({ json: configuration }),
  );
  await page.route("**/api/backend/invoices**", async (route) => {
    const request = route.request();
    if (request.url().endsWith("/send")) {
      expect(request.postDataJSON().confirm_sandbox).toBe(true);
      sendCalls++;
      invoice.status = invoice.sandbox.provider_status = "SENT";
      invoice.sandbox.payment_url =
        "https://www.sandbox.paypal.com/invoice/p/#MOCK-RETURNED-LINK";
    } else if (request.url().endsWith("/refresh")) {
      refreshes++;
      invoice.status = invoice.sandbox.provider_status =
        refreshes === 1
          ? "PAYMENT_PENDING"
          : refreshes === 2
            ? "PARTIALLY_PAID"
            : "PAID";
      invoice.sandbox.paid_amount =
        refreshes === 2 ? "10.00" : refreshes === 3 ? "30.00" : "0.00";
      invoice.sandbox.due_amount =
        refreshes === 2 ? "20.00" : refreshes === 3 ? "0.00" : "30.00";
    }
    expect(request.url()).not.toContain("simulate-payment");
    await route.fulfill({
      json: request.url().endsWith("/invoices") ? [invoice] : invoice,
    });
  });
  await page.goto("/dashboard/invoices");
  const card = page.locator(".invoice-card");
  await expect(card).toContainText(configuration.payment_notice);
  await expect(
    card.getByRole("button", {
      name: "Simulate payment completion",
      exact: true,
    }),
  ).toHaveCount(0);
  page.once("dialog", (dialog) => dialog.dismiss());
  await card
    .getByRole("button", { name: "Send Sandbox invoice", exact: true })
    .click();
  expect(sendCalls).toBe(0);
  page.once("dialog", (dialog) => dialog.accept());
  await card
    .getByRole("button", { name: "Send Sandbox invoice", exact: true })
    .click();
  await expect(
    card.getByRole("link", { name: "Open PayPal Sandbox invoice" }),
  ).toHaveAttribute(
    "href",
    "https://www.sandbox.paypal.com/invoice/p/#MOCK-RETURNED-LINK",
  );
  await expect(card.getByText("sent", { exact: true })).toBeVisible();
  await card.getByRole("button", { name: "Refresh PayPal status" }).click();
  await expect(
    card.getByText("payment pending", { exact: true }),
  ).toBeVisible();
  await card.getByRole("button", { name: "Refresh PayPal status" }).click();
  await expect(card.getByText("partially paid", { exact: true })).toBeVisible();
  await card.getByRole("button", { name: "Refresh PayPal status" }).click();
  await expect(card.getByText("paid (Sandbox)", { exact: true })).toBeVisible();
  expect(sendCalls).toBe(1);
});

test("Sandbox draft creation requires a reviewed case and can be cancelled without a write", async ({
  page,
}) => {
  let writes = 0;
  await page.route("**/api/backend/integrations", (route) =>
    route.fulfill({ json: configuration }),
  );
  await page.route("**/api/backend/royalties**", async (route) => {
    const url = route.request().url();
    if (url.endsWith("/invoice-preview"))
      return route.fulfill({
        json: {
          amount: "30.00",
          currency: "USD",
          sandbox_payload: {
            merchant_email: "merchant@business.example.com",
            buyer_email: "buyer@personal.example.com",
          },
        },
      });
    if (url.endsWith("/invoice")) {
      writes++;
      expect(route.request().postDataJSON()).toEqual({
        confirm_sandbox: true,
        expected_amount: "30.00",
        expected_currency: "USD",
        expected_recipient: "buyer@personal.example.com",
      });
      return route.fulfill({
        json: { provider: "paypal_sandbox", provider_id: "INV2-MOCK-UI-TEST" },
      });
    }
    return route.fulfill({
      json: [
        {
          id: "ui-charge",
          asset_id: "ui-asset",
          license_id: "ui-license",
          amount: "30.00",
          currency: "USD",
          status: "APPROVED",
          eligible_for_charge: true,
          approval_current: true,
          created_at: "2026-11-09T00:00:00Z",
          decision_note: "Reviewed mock UI case",
          calculation: {
            explanation: "(45 - 30) x 2 = 30",
            spoken_seconds: "45",
            allowance_remaining: "30",
            additional_seconds: "15",
            billing_basis: "per_asset",
            rounding: "HALF_UP",
          },
        },
      ],
    });
  });
  await page.goto("/dashboard/royalties");
  const button = page.getByRole("button", {
    name: "Create / open PayPal Sandbox draft",
    exact: true,
  });
  const dismissed = new Promise<void>((resolve) => {
    page.once("dialog", async (dialog) => {
      await dialog.dismiss();
      resolve();
    });
  });
  await button.click();
  await dismissed;
  await expect(button).toBeEnabled();
  expect(writes).toBe(0);
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("buyer@personal.example.com");
    expect(dialog.message()).toContain("30.00 USD");
    await dialog.accept();
  });
  await button.click();
  await expect(page.getByText(/Actual Sandbox draft/)).toBeVisible();
  expect(writes).toBe(1);
});
