import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";

let licenseTitle = "";
let grantId = "",
  referenceId = "",
  licenseId = "";
function wav(seconds: number) {
  const bytes = seconds * 24000 * 2;
  const buffer = Buffer.alloc(44 + bytes);
  buffer.write("RIFF", 0);
  buffer.writeUInt32LE(36 + bytes, 4);
  buffer.write("WAVEfmt ", 8);
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(1, 20);
  buffer.writeUInt16LE(1, 22);
  buffer.writeUInt32LE(24000, 24);
  buffer.writeUInt32LE(48000, 28);
  buffer.writeUInt16LE(2, 32);
  buffer.writeUInt16LE(16, 34);
  buffer.write("data", 36);
  buffer.writeUInt32LE(bytes, 40);
  return buffer;
}

test("reference picker identifies oversized samples without requiring a 30-second consent", async ({
  page,
}) => {
  await page.request.post("/api/persona", { data: { persona: "artist_demo" } });
  await page.route("**/api/backend/references", (route) =>
    route.fulfill({
      json: [
        {
          id: "oversized",
          created_at: "2026-11-11T00:00:00Z",
          metadata_json: { duration_seconds: "45.401", format: "wav" },
          consent: true,
        },
        {
          id: "valid",
          created_at: "2026-11-11T00:00:00Z",
          metadata_json: { duration_seconds: "15.000", format: "wav" },
          consent: true,
        },
      ],
    }),
  );
  await page.goto("/dashboard/references");
  const picker = page.getByRole("combobox", {
    name: "Artist reference sample",
    exact: true,
  });
  await expect(picker.locator('option[value="oversized"]')).toBeDisabled();
  await expect(picker.locator('option[value="valid"]')).toBeEnabled();
  await expect(picker.locator('option[value="oversized"]')).toContainText(
    "45.401s",
  );
  await expect(
    page.getByText("you do not need to fill 30 seconds", { exact: false }),
  ).toBeVisible();
});
test.beforeAll(async ({ request }) => {
  const integrations = await (
    await request.get("/api/backend/integrations")
  ).json();
  expect(integrations.payment_provider).toBe("mock");
  expect(integrations.voice_generation.enabled).toBe(false);
  await request.post("/api/persona", { data: { persona: "artist_demo" } });
  licenseTitle = `Generation browser fixture ${Date.now()}`;
  const created = await request.post("/api/backend/licenses", {
    data: {
      title: licenseTitle,
      studio_id: "studio_demo",
    },
  });
  expect(created.ok()).toBeTruthy();
  licenseId = (await created.json()).id;
  expect(
    (
      await request.post(`/api/backend/licenses/${licenseId}/contract`, {
        multipart: {
          file: {
            name: "sample-license.pdf",
            mimeType: "application/pdf",
            buffer: readFileSync(
              path.resolve(
                __dirname,
                "../../backend/fixtures/sample-license.pdf",
              ),
            ),
          },
        },
      })
    ).ok(),
  ).toBeTruthy();
  const extracted = await request.post(
    `/api/backend/licenses/${licenseId}/extract`,
    { data: { use_demo_fixture: true } },
  );
  expect(extracted.ok()).toBeTruthy();
  const license = await extracted.json();
  const approved = await request.post(
    `/api/backend/licenses/${licenseId}/approve`,
    {
      data: {
        terms: license.terms,
        expected_version: license.version,
        note: "Automated isolated fixture approval, no real identity or legal agreement.",
      },
    },
  );
  expect(approved.ok(), await approved.text()).toBeTruthy();
  const reference = await request.post("/api/backend/references", {
    multipart: {
      consent: "true",
      file: {
        name: "synthetic-reference-test.wav",
        mimeType: "audio/wav",
        buffer: wav(12),
      },
    },
  });
  expect(reference.ok()).toBeTruthy();
  referenceId = (await reference.json()).id;
  const grant = await request.post("/api/backend/voice-grants", {
    multipart: {
      reference_id: referenceId,
      license_id: licenseId,
      owner_confirmed: "true",
      provider_transfer_consent: "true",
      note: "Automated local test only: synthetic silence, never sent to Google; no real speaker consent claimed.",
      file: {
        name: "synthetic-consent-test.wav",
        mimeType: "audio/wav",
        buffer: wav(4),
      },
    },
  });
  expect(grant.ok(), await grant.text()).toBeTruthy();
  grantId = (await grant.json()).id;
});

test("artist can inspect private sample, consent requirements and saved license grant", async ({
  page,
}) => {
  await page.request.post("/api/persona", { data: { persona: "artist_demo" } });
  await page.goto("/dashboard/references");
  await expect(
    page.getByRole("heading", {
      name: "3. Authorize your licensed voice for generation",
    }),
  ).toBeVisible();
  await expect(
    page.getByText("I am the owner of this voice and I consent to Google", {
      exact: false,
    }),
  ).toBeVisible();
  const audio = page.locator(`audio[src$="/references/${referenceId}/audio"]`);
  await expect(audio).toHaveAttribute("controls", "");
  expect(
    (
      await page.request.get(`/api/backend/references/${referenceId}/audio`)
    ).ok(),
  ).toBeTruthy();
  await expect(
    page.getByRole("heading", { name: new RegExp(`${licenseTitle}.*v[0-9]+`) }),
  ).toBeVisible();
});

test("studio sees explicit generation setup and cannot access private artist samples", async ({
  page,
}) => {
  await page.request.post("/api/persona", { data: { persona: "studio_demo" } });
  expect(
    (
      await page.request.get(`/api/backend/references/${referenceId}/audio`)
    ).status(),
  ).toBe(403);
  await page.goto("/dashboard/generate");
  await expect(
    page.getByText("Generation is not enabled/configured.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByText("Voice replication: gemini-3.8-flash-tts.", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(
    page.getByText("Speech synthesis: gemini-3.8-flash-lite-tts.", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Generate with licensed artist voice" }),
  ).toBeDisabled();
  await expect(
    page.getByLabel("Artist-approved voice and license"),
  ).toContainText("Generation browser fixture");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});

test("studio generation UI forwards consented script and opens existing analysis workflow", async ({
  page,
}) => {
  await page.request.post("/api/persona", { data: { persona: "studio_demo" } });
  // Explicit browser-only provider seam. No Gemini model or voice API is called.
  await page.route("**/api/backend/integrations", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    await route.fulfill({
      json: {
        ...data,
        voice_generation: {
          ...data.voice_generation,
          enabled: true,
          configured: true,
        },
      },
    });
  });
  let submitted = 0;
  await page.route("**/api/backend/generations", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    submitted++;
    const body = route.request().postDataJSON();
    expect(body.grant_id).toBe(grantId);
    expect(body.confirm_provider_use).toBe(true);
    expect(body.script).toContain("original reusable bottle");
    expect(body.request_key).toBeTruthy();
    const asset = await page.request.post("/api/backend/assets", {
      multipart: {
        license_id: licenseId,
        campaign: JSON.stringify(body.campaign),
        file: {
          name: "browser-only-generated-mock.wav",
          mimeType: "audio/wav",
          buffer: wav(2),
        },
      },
    });
    expect(asset.ok()).toBeTruthy();
    const recording = await asset.json();
    await route.fulfill({
      json: {
        id: "browser-mocked-generation",
        status: "SUCCEEDED",
        asset_id: recording.id,
        receipt: { mode: "browser mock; not live Gemini" },
      },
    });
  });
  await page.goto("/dashboard/generate");
  await page
    .getByLabel("Artist-approved voice and license")
    .selectOption(grantId);
  await page
    .getByLabel("Advertisement script", { exact: true })
    .fill(
      "Discover our original reusable bottle, designed for everyday adventures.",
    );
  await page
    .getByLabel("Campaign name", { exact: true })
    .fill("Generation browser campaign");
  await page.getByLabel("Declared country / region").fill("US");
  await page.getByLabel("Platform / medium").fill("online advertising");
  await page.getByLabel("Declared language", { exact: true }).fill("English");
  await page
    .getByLabel("Campaign category", { exact: true })
    .fill("consumer products");
  await page
    .getByLabel("I request this Gemini voice replication", { exact: false })
    .check();
  await page
    .getByRole("button", { name: "Generate with licensed artist voice" })
    .click();
  await expect(page).toHaveURL(/\/dashboard\/submissions\/[a-z0-9]+$/);
  expect(submitted).toBe(1);
  await expect(
    page.getByRole("heading", { name: "Generation browser campaign" }),
  ).toBeVisible();
});

test("Fish requires its own artist consent and studio selection, with no automatic provider fallback", async ({
  page,
}) => {
  await page.request.post("/api/persona", { data: { persona: "artist_demo" } });
  await page.goto("/dashboard/references");
  await page
    .getByRole("combobox", { name: "Voice generation provider", exact: true })
    .selectOption("fish");
  await expect(
    page.getByLabel("Speaker consent recording", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText("no reusable Fish voice profile", { exact: false }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Artist reference sample", exact: true })
    .selectOption(referenceId);
  await page
    .getByRole("combobox", { name: "Approved agreement", exact: true })
    .selectOption(licenseId);
  await page
    .getByLabel("Exact reference transcript", { exact: true })
    .fill(
      "Synthetic browser-test recording, never transmitted to a voice provider.",
    );
  await page.getByLabel("I reviewed", { exact: false }).check();
  await page.getByLabel("I am the adult voice owner", { exact: false }).check();
  await page
    .getByLabel("I explicitly authorize sending my reference", { exact: false })
    .check();
  await page
    .getByLabel("Generation permission note", { exact: true })
    .fill(
      "Explicit local fixture attestation for browser QA only; no real voice consent claimed.",
    );
  const grantResponse = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/backend/voice-grants") &&
      r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Grant licensed studio generation" })
    .click();
  const saved = await grantResponse;
  expect(saved.ok(), await saved.text()).toBeTruthy();
  const fishGrant = await saved.json();
  expect(fishGrant.provider).toBe("fish");
  expect(fishGrant.id).not.toBe(grantId);
  await page.request.post("/api/persona", { data: { persona: "studio_demo" } });
  await page.route("**/api/backend/integrations", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    await route.fulfill({
      json: {
        ...data,
        voice_generation: {
          ...data.voice_generation,
          fish: {
            ...data.voice_generation.fish,
            enabled: true,
            configured: true,
          },
        },
      },
    });
  });
  const keys: string[] = [];
  await page.route("**/api/backend/generations", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    const body = route.request().postDataJSON();
    expect(body.provider).toBe("fish");
    expect(body.grant_id).toBe(fishGrant.id);
    keys.push(body.request_key);
    if (keys.length === 1)
      return route.fulfill({
        status: 502,
        json: {
          detail:
            "Fish Audio reported a fair-use/rate limit. No provider switch or automatic retry was attempted.",
        },
      });
    const asset = await page.request.post("/api/backend/assets", {
      multipart: {
        license_id: licenseId,
        campaign: JSON.stringify({
          ...body.campaign,
          generation_provider: "Fish Audio / browser mock only",
        }),
        file: {
          name: "fish-browser-only.wav",
          mimeType: "audio/wav",
          buffer: wav(3),
        },
      },
    });
    expect(asset.ok()).toBeTruthy();
    const recording = await asset.json();
    await route.fulfill({
      json: {
        id: "fish-browser-mock",
        provider: "fish",
        status: "SUCCEEDED",
        asset_id: recording.id,
        receipt: { mode: "browser mock only" },
      },
    });
  });
  await page.goto("/dashboard/generate");
  await page
    .getByRole("combobox", { name: "Voice generation provider", exact: true })
    .selectOption("fish");
  const picker = page.getByRole("combobox", {
    name: "Artist-approved voice and license",
    exact: true,
  });
  await expect(picker.locator(`option[value="${grantId}"]`)).toHaveCount(0);
  await picker.selectOption(fishGrant.id);
  await page
    .getByLabel("Advertisement script", { exact: true })
    .fill("Discover our original lunch box for everyday adventures.");
  await page
    .getByLabel("Campaign name", { exact: true })
    .fill("Fish browser campaign");
  await page.getByLabel("Declared country / region").fill("US");
  await page.getByLabel("Platform / medium").fill("online advertising");
  await page.getByLabel("Declared language", { exact: true }).fill("English");
  await page
    .getByLabel("Campaign category", { exact: true })
    .fill("consumer products");
  await page
    .getByLabel("I request this Fish Audio voice replication", { exact: false })
    .check();
  await page
    .getByRole("button", { name: "Generate with licensed artist voice" })
    .click();
  await expect(
    page.getByText("Fish Audio reported a fair-use/rate limit.", {
      exact: false,
    }),
  ).toBeVisible();
  expect(keys).toHaveLength(1);
  await page
    .getByRole("button", { name: "Start a new generation request" })
    .click();
  await page
    .getByRole("button", { name: "Generate with licensed artist voice" })
    .click();
  await expect(page).toHaveURL(/\/dashboard\/submissions\/[a-z0-9]+$/);
  expect(keys).toHaveLength(2);
  expect(keys[0]).not.toBe(keys[1]);
  await expect(
    page.getByRole("heading", { name: "Fish browser campaign" }),
  ).toBeVisible();
});
