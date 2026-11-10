import { test, expect } from "@playwright/test";

test("working overview has no sidebar and page launcher performs real navigation", async ({
  page,
}) => {
  await page.goto("/dashboard");
  await expect(page.locator(".workspace-sidebar")).toHaveCount(0);
  await expect(
    page.getByRole("navigation", { name: "Main navigation", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Control+k");
  const launcher = page.getByRole("dialog", { name: "Workspace navigation" });
  await expect(launcher).toBeVisible();
  await launcher
    .getByRole("searchbox", { name: "Find a page" })
    .fill("invoice");
  await expect(launcher.getByRole("link")).toHaveCount(1);
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/dashboard\/invoices$/);
  await expect(launcher).toHaveCount(0);
});

test("real WebGL sculpture pauses and changes its rendered view on rotation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/dashboard");
  const canvas = page.locator(".voice-webgl canvas[data-rendered=true]");
  await expect(canvas).toBeVisible();
  await page.getByRole("button", { name: "Pause sculpture motion" }).click();
  await expect(page.locator(".voice-sculpture")).toHaveAttribute(
    "data-motion",
    "paused",
  );
  await canvas.evaluate(
    () =>
      new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      ),
  );
  const before = await canvas.screenshot();
  await page.getByRole("button", { name: "Rotate sculpture right" }).click();
  await expect
    .poll(async () => Buffer.compare(before, await canvas.screenshot()))
    .not.toBe(0);
  await page.getByRole("button", { name: "Reset sculpture view" }).click();
  await page.getByRole("button", { name: "Play sculpture motion" }).click();
  await expect(page.locator(".voice-sculpture")).toHaveAttribute(
    "data-motion",
    "playing",
  );
  await expect(
    page.getByText(
      "Artwork only. Not a voiceprint, identity check or audio measurement.",
    ),
  ).toBeVisible();
});

test("small screens defer WebGL and reduced motion disables automatic rotation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/dashboard");
  await expect(
    page.getByRole("button", { name: "Explore in 3D" }),
  ).toBeVisible();
  await expect(page.locator(".voice-webgl canvas")).toHaveCount(0);
  await page.getByRole("button", { name: "Explore in 3D" }).click();
  await expect(
    page.locator(".voice-webgl canvas[data-rendered=true]"),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Play sculpture motion" }),
  ).toBeDisabled();
});

test("WebGL failure shows illustration and leaves working workflow accessible", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      kind: string,
      ...args: unknown[]
    ) {
      if (kind.startsWith("webgl")) return null;
      return Reflect.apply(original, this, [kind, ...args]);
    } as typeof original;
  });
  await page.goto("/dashboard");
  await expect(
    page.getByText(
      "WebGL unavailable. The workspace remains fully functional.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "New voice license", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".voice-webgl canvas")).toHaveCount(0);
});
