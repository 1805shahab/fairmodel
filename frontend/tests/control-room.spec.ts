import { test, expect } from "@playwright/test";

for (const route of ["/", "/control-room"]) {
  test(`${route} opens the single working application without automatic payment writes`, async ({
    page,
  }) => {
    const writes: string[] = [];
    page.on("request", (request) => {
      if (
        request.method() !== "GET" &&
        /\/api\/backend\/.*(?:invoice|payment|paypal)/.test(request.url())
      )
        writes.push(request.url());
    });
    await page.goto(route);
    if (route === "/") {
      await expect(
        page.getByRole("heading", {
          name: "Your voice. Your rights. Your royalties.",
        }),
      ).toBeVisible();
      await page
        .getByRole("link", { name: "Open workspace", exact: true })
        .first()
        .click();
    }
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(
      page.getByRole("heading", { name: "Your voice. Your call." }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: /Open control room/i }),
    ).toHaveCount(0);
    await expect(page.getByText(/FICTIONAL PREVIEW/)).toHaveCount(0);
    await expect(
      page.getByRole("combobox", { name: "Workspace role" }),
    ).toBeVisible();
    await page
      .getByRole("link", { name: "Settings & integrations", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Sponsor integrations" }),
    ).toBeVisible();
    const response = await page.request.get("/api/tools/postman");
    expect(response.ok()).toBe(true);
    expect(response.headers()["content-disposition"]).toContain("attachment");
    const collection = await response.json();
    expect(collection.info.schema).toContain("v2.1.0");
    expect(
      collection.variable.find(
        (v: { key: string }) => v.key === "allow_explicit_writes",
      ).value,
    ).toBe("false");
    expect(writes).toEqual([]);
  });
}
