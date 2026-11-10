import { test, expect } from "@playwright/test";

for (const width of [390, 1440]) {
  test(`landing sculpture hydrates without console errors at ${width}px`, async ({
    page,
    request,
  }) => {
    const errors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("pageerror", (error) => errors.push(error.message));
    await page.setViewportSize({ width, height: 1000 });
    await page.emulateMedia({ reducedMotion: "reduce" });

    // Geometry must exist before JS and remain the same asset after hydration.
    const response = await request.get("/");
    expect(response.ok()).toBe(true);
    expect(await response.text()).toContain('src="/voice-sculpture-still.svg"');
    await page.goto("/");
    const still = page.locator("img.voice-still");
    await expect(still).toHaveAttribute("src", "/voice-sculpture-still.svg");
    await expect
      .poll(() =>
        still.evaluate(
          (img: HTMLImageElement) => img.complete && img.naturalWidth === 500,
        ),
      )
      .toBe(true);
    if (width < 700) {
      // Clicking a handler proves hydration completed, not just SSR visibility.
      await page.getByRole("button", { name: "Explore in 3D" }).click();
    }
    await expect(
      page.locator(".voice-webgl canvas[data-rendered=true]"),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Play sculpture motion" }),
    ).toBeDisabled();
    expect(
      errors,
      "React warnings and runtime errors must not be hidden",
    ).toEqual([]);
  });
}

test("landing illustration remains visible without JavaScript", async ({
  browser,
  baseURL,
}) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    baseURL,
  });
  try {
    const page = await context.newPage();
    await page.goto("/");
    const still = page.locator("img.voice-still");
    await expect(still).toBeVisible();
    await expect
      .poll(() => still.evaluate((img: HTMLImageElement) => img.naturalWidth))
      .toBe(500);
    await expect(page.locator(".voice-webgl canvas")).toHaveCount(0);
  } finally {
    await context.close();
  }
});
