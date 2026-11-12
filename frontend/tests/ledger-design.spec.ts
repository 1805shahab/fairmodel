import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { money } from "../components/display-money";

test("ledger displays backend decimal text without financial rounding", () => {
  expect(money("57.54", "USD")).toBe("$57.54");
  expect(money("30.009", "USD")).toBe("$30.009");
  expect(money("0.00", "USD")).toBe("$0.00");
  expect(money("12345678901234567890.01", "USD")).toBe(
    "$12345678901234567890.01",
  );
  expect(money("3.1400", "QAR")).toBe("QAR 3.1400");
});

test("theme choice persists and launcher restores keyboard focus", async ({
  page,
}) => {
  await page.goto("/dashboard");
  await page.getByRole("button", { name: "Use dark theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.keyboard.press("Control+k");
  await expect(
    page.getByRole("dialog", { name: "Workspace navigation" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Open navigation" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "Use light theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

for (const theme of ["light", "dark"]) {
  test(`${theme} ledger has no axe AA violations across its main surfaces`, async ({
    page,
  }) => {
    test.setTimeout(180000);
    await page.addInitScript(
      (mode) => localStorage.setItem("fairmodel-theme", mode),
      theme,
    );
    for (const route of [
      "/",
      "/dashboard",
      "/dashboard/licenses/new",
      "/dashboard/generate",
      "/dashboard/analytics",
      "/dashboard/invoices",
      "/design-system",
    ]) {
      await page.goto(route);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      // The reference route intentionally demonstrates a persistent loading state.
      await expect(page.locator(".loading-skeleton")).toHaveCount(route === "/design-system" ? 1 : 0);
      if (route === "/dashboard/analytics") {
        await expect(page.locator('.ag-header-cell[col-id="artist_name"]')).toBeVisible();
      }
      const result = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze();
      expect(result.violations, `${theme}: ${route}`).toEqual([]);
    }
  });
}

test("compact navigation and 200 percent layout reflow keep controls reachable", async ({
  page,
}) => {
  for (const width of [375, 768, 1280, 640]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/dashboard/licenses/new");
    await expect(
      page.getByLabel("Agreement name", { exact: true }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
      `overflow at ${width}`,
    ).toBe(false);
    await expect(
      page.getByRole("button", { name: "Open navigation" }),
    ).toBeVisible();
  }
});
