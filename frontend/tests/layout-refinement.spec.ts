import { test, expect } from "@playwright/test";

for (const width of [375, 1280]) {
  test(`homepage advances all five steps with native scrolling at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: "no-preference" });
    await page.goto("/");
    const track = page.locator(".workflow-scroll-track");
    await expect(track).toHaveAttribute("data-scroll", "true");
    for (const index of [0, 1, 2, 3, 4, 2, 0]) {
      await track.evaluate((element, step) => {
        const sticky = element.querySelector<HTMLElement>(".workflow-sticky")!;
        const top = Number.parseFloat(getComputedStyle(sticky).top);
        const start = element.getBoundingClientRect().top + scrollY - top;
        const distance =
          (element as HTMLElement).offsetHeight - sticky.offsetHeight;
        window.scrollTo({
          top: start + (distance * step) / 4,
          behavior: "instant",
        });
      }, index);
      await expect(track).toHaveAttribute(
        "data-active-step",
        String(index + 1),
      );
      await expect(page.locator(`#rights-tab-${index}`)).toHaveAttribute(
        "aria-selected",
        "true",
      );
      await expect(page.getByRole("tabpanel")).toBeInViewport();
    }
    await page.getByRole("tab", { name: /05.*Invoice/ }).click();
    await expect(track).toHaveAttribute("data-active-step", "5");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
    ).toBe(false);
  });
}

test("reduced-motion and short viewports retain compact keyboard exploration", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator(".workflow-scroll-track")).toHaveAttribute(
    "data-scroll",
    "false",
  );
  await page.getByRole("tab", { name: /01.*License/ }).focus();
  await page.keyboard.press("End");
  await expect(page.getByRole("tabpanel")).toContainText(
    "PayPal Sandbox invoices",
  );
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.setViewportSize({ width: 1280, height: 600 });
  await expect(page.locator(".workflow-scroll-track")).toHaveAttribute(
    "data-scroll",
    "false",
  );
});

test("form and footer content share centered edges at desktop and mobile widths", async ({
  page,
}) => {
  for (const width of [375, 768, 1280, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/dashboard/licenses/new");
    const form = page.locator("form.form-panel");
    const brand = page.locator(".site-footer-brand");
    await expect(form).toBeVisible();
    const formBox = await form.boundingBox();
    const footerBox = await brand.boundingBox();
    expect(Math.abs(formBox!.x - footerBox!.x)).toBeLessThanOrEqual(1);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
    ).toBe(false);
  }
});

test("generation uses full width when empty and a bounded history column when populated", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.request.post("/api/persona", { data: { persona: "studio_demo" } });
  let populated = false;
  await page.route("**/api/backend/generations", (route) =>
    route.fulfill({
      json: populated
        ? [
            {
              id: "layout-fixture-only",
              status: "FAILED",
              provider: "fish",
              created_at: "2026-11-12T00:00:00Z",
              receipt: { mode: "browser fixture" },
              error: "Explicit UI fixture. No provider request.",
            },
          ]
        : [],
    }),
  );
  await page.goto("/dashboard/generate");
  const layout = page.locator(".generation-layout");
  await expect(layout).toHaveAttribute("data-has-history", "false");
  const form = await layout.locator("form").boundingBox();
  const emptyHistory = await page
    .getByRole("region", { name: "Generation history", exact: true })
    .boundingBox();
  expect(Math.abs(form!.width - emptyHistory!.width)).toBeLessThanOrEqual(1);
  populated = true;
  await page.reload();
  await expect(layout).toHaveAttribute("data-has-history", "true");
  const populatedForm = await layout.locator("form").boundingBox();
  const history = page.getByRole("region", {
    name: "Generation history",
    exact: true,
  });
  expect((await history.boundingBox())!.x).toBeGreaterThan(
    populatedForm!.x + populatedForm!.width,
  );
  await expect(history).toHaveCSS("overflow-y", "auto");
  await expect(history).toHaveAttribute("tabindex", "0");
});
