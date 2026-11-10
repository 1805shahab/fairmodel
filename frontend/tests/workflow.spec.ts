import { test, expect } from "@playwright/test";
import path from "node:path";
import { readFileSync } from "node:fs";
const fixtures = path.resolve(__dirname, "../../backend/fixtures");

test("artist and studio complete the real-media local fixture workflow", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("link", { name: "Open workspace", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(
    page.getByRole("heading", { name: "Your voice. Your call." }),
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
    .getByRole("combobox", { name: "Workspace role" })
    .selectOption("studio");
  await expect(
    page.getByRole("combobox", { name: "Workspace role" }),
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
  await expect(page.getByLabel("Transcription provider")).toHaveValue("live");
  const assetId = page.url().split("/").pop();
  await page.getByLabel("Transcription provider").selectOption("fixture");
  await page
    .getByRole("button", { name: "Analyze audio", exact: true })
    .click();
  await page.getByRole("tab", { name: "Transcript", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Transcript & timestamps" }),
  ).toBeVisible();
  await expect(page.locator("audio")).toBeVisible();
  await page.getByRole("tab", { name: "Overview", exact: true }).click();
  await expect(page.getByLabel("Compliance provider")).toHaveValue("live");
  await page.getByRole("tab", { name: "Overview", exact: true }).click();
  await page.getByLabel("Compliance provider").selectOption("fixture");
  await page
    .getByRole("button", { name: "Evaluate compliance", exact: true })
    .click();
  await page.getByRole("tab", { name: "Compliance", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Compliance report", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("needs review", { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Workspace role" })
    .selectOption("artist");
  await expect(
    page.getByRole("combobox", { name: "Workspace role" }),
  ).toHaveValue("artist");
  await page
    .getByRole("tab", { name: "Identity & authorization", exact: true })
    .click();
  await page
    .getByLabel("I confirm the licensed speaker identity for this asset")
    .check();
  await page
    .getByLabel("I authorize this asset and its declared campaign")
    .check();
  await page
    .getByLabel("Identity and authorization review note")
    .fill(
      "Offline test only: simulated artist review of the bundled synthetic fixture.",
    );
  await page.getByRole("tab", { name: "Transcript", exact: true }).click();
  await page
    .getByRole("tab", { name: "Identity & authorization", exact: true })
    .click();
  await expect(
    page.getByLabel("Identity and authorization review note"),
  ).toHaveValue(
    "Offline test only: simulated artist review of the bundled synthetic fixture.",
  );
  await page
    .getByRole("button", { name: "Save artist usage review", exact: true })
    .click();
  await expect(
    page.getByText("Artist confirmation recorded", { exact: false }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Overview", exact: true }).click();
  await page.getByLabel("Compliance provider").selectOption("fixture");
  await page
    .getByRole("button", { name: "Evaluate compliance", exact: true })
    .click();
  await page.getByRole("tab", { name: "Compliance", exact: true }).click();
  await expect(
    page.getByText("additional royalty due", { exact: true }).first(),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/audio-analysis-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(
      async () =>
        (
          await page
            .getByLabel("Submitted recording", { exact: true })
            .boundingBox()
        )?.height || 0,
    )
    .toBeGreaterThan(30);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    ),
  ).toBe(false);
  await page.setViewportSize({ width: 1280, height: 720 });
  // Reopening fixture evidence must still default to live Gemini. A failed live
  // request must show the actual safe error without relabeling old fixture data.
  await page.reload();
  await page.getByRole("tab", { name: "Overview", exact: true }).click();
  await expect(page.getByLabel("Compliance provider")).toHaveValue("live");
  await page.route("**/api/backend/assets/*/evaluate", async (route) => {
    expect(route.request().postDataJSON().use_demo_fixture).toBe(false);
    await route.fulfill({
      status: 502,
      contentType: "application/json",
      body: JSON.stringify({
        detail:
          "Gemini reported a rate limit (provider HTTP 429). No fixture fallback was used.",
      }),
    });
  });
  await page
    .getByRole("button", { name: "Evaluate compliance", exact: true })
    .click();
  await expect(
    page.getByRole("alert").filter({ hasText: "provider HTTP 429" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Compliance", exact: true }).click();
  await expect(
    page.getByText("Offline fixture compliance — not a live AI result", {
      exact: true,
    }),
  ).toBeVisible();
  await page.unroute("**/api/backend/assets/*/evaluate");
  await page.getByRole("link", { name: "Royalties", exact: true }).click();
  const royaltyCard = page.locator(".royalty-card").filter({
    has: page.locator(`a[href="/dashboard/submissions/${assetId}"]`),
  });
  await royaltyCard
    .getByLabel("Approval / rejection note")
    .fill("Approved measured speech and checked the source agreement.");
  await royaltyCard
    .getByRole("button", { name: "Approve charge", exact: true })
    .click();
  const invoiceCreated = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      /\/royalties\/[^/]+\/invoice$/.test(response.url()),
  );
  await royaltyCard
    .getByRole("button", {
      name: "Create / open simulated invoice",
      exact: true,
    })
    .click();
  const invoiceResponse = await invoiceCreated;
  expect(invoiceResponse.ok()).toBe(true);
  const invoice = await invoiceResponse.json();
  await page
    .getByRole("link", { name: "Invoices & payments", exact: true })
    .click();
  await page.getByText("How test invoices work", { exact: true }).click();
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
  const invoiceCard = page.locator(".invoice-card").filter({
    has: page.getByRole("heading", { name: invoice.provider_id, exact: true }),
  });
  await expect(
    invoiceCard.getByRole("link", {
      name: "Browser verified launch",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("searchbox", { name: "Find invoice", exact: true })
    .fill(invoice.provider_id);
  await expect(page.locator(".invoice-card")).toHaveCount(1);
  await invoiceCard
    .getByRole("button", { name: "Simulate sending invoice", exact: true })
    .click();
  await page
    .getByRole("combobox", { name: "Workspace role" })
    .selectOption("studio");
  await expect(
    page.getByRole("combobox", { name: "Workspace role" }),
  ).toHaveValue("studio");
  await invoiceCard
    .getByRole("button", { name: "Simulate payment completion", exact: true })
    .click();
  await expect(
    invoiceCard.getByText("paid simulated", { exact: true }),
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
    .getByRole("link", { name: "Settings & integrations", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Settings & integrations", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Not yet verified", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Workspace role" })
    .selectOption("studio");
  await expect(
    page.getByRole("combobox", { name: "Workspace role" }),
  ).toHaveValue("studio");
  await page.reload();
  await expect(
    page.getByRole("combobox", { name: "Workspace role" }),
  ).toHaveValue("studio");
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Create with permission." }),
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

test("report distinguishes workflow evidence and omits empty or unverified quotations", async ({
  page,
}) => {
  const asset = {
    id: "citation-regression",
    license_id: "source-license",
    license_version: 4,
    original_name: "Explicit UI fixture.wav",
    status: "NEEDS_REVIEW",
    error: null,
    campaign: {
      name: "Citation rendering regression",
      region: "US",
      medium: "online advertising",
      language: "English",
      category: "consumer products",
      intended_use_date: "2026-11-09",
    },
    analysis: {
      result: {
        duration_seconds: "38.477",
        spoken_seconds: "23.52",
        format: "wav",
        sample_rate: 16000,
        channels: 1,
        speech_segments: [{ start: 1.5, end: 3 }],
        transcript: "Explicit offline UI fixture.",
        timestamps: [
          { start: 1.5, end: 3, text: "Explicit offline UI fixture." },
        ],
        provider: "demo_fixture (not Groq)",
        vad: "fixture UI only",
        measurement_note: "Explicit UI fixture; no service call.",
        measurement_uncertain: false,
        demo_fixture: true,
        speaker: {
          status: "disabled",
          score: null,
          note: "Identity is not independently verified.",
        },
      },
    },
    report: {
      result: {
        status: "NEEDS_REVIEW",
        reasons: ["Artist identity review remains unresolved."],
        calculation: {
          spoken_seconds: "23.52",
          prior_seconds: "0",
          included_seconds: "30",
          allowance_remaining: "30",
          additional_seconds: "0",
          rate: "2",
          amount: "0.00",
          currency: "USD",
          billing_basis: "per_asset",
          rounding: "ROUND_HALF_UP",
          explanation: "23.52 spoken seconds are below 30 included seconds.",
        },
        findings: {
          findings: [
            {
              category: "Purpose review",
              passage: "",
              explanation:
                "Purpose cannot be established from this UI fixture.",
              possible_conflict: false,
              needs_review: true,
            },
          ],
          uncertainty: [],
        },
        provider: "demo_fixture (not Gemini)",
        assessment_fixture: true,
        policy_version: 3,
        eligible_for_charge: false,
        metadata_note: "Declared metadata.",
        legal_note: "Advisory only.",
        rule_checks: [
          {
            rule: "submission_before_publication",
            kind: "administrative",
            outcome: "satisfied",
            explanation:
              "Studio upload and review-request receipts are present.",
          },
        ],
        source_pages: [
          { field: "special_conditions", page: 1, quote: "  ", verified: true },
          {
            field: "special_conditions",
            page: 0,
            quote: "Invalid page must not render",
            verified: true,
          },
          {
            field: "special_conditions",
            page: 1,
            quote: "Unverified text must not render",
            verified: false,
          },
          {
            field: "included_seconds",
            page: 1,
            quote: "Each advertisement includes 30 seconds of spoken voice.",
            verified: true,
            origin: "extracted",
          },
        ],
        source_review: {
          missing_fields: ["special_conditions"],
          recovered_condition_citations: 0,
        },
      },
    },
    authorization: null,
    royalty: null,
  };
  await page.route("**/api/backend/assets/citation-regression", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(asset),
    }),
  );
  // Native media seeking uses byte ranges. Match the real private-media endpoint
  // instead of returning a fresh full-file response to every Range request.
  const audioBytes = readFileSync(path.join(fixtures, "sample-narration.wav"));
  await page.route(
    "**/api/backend/assets/citation-regression/audio",
    (route) => {
      const range = /bytes=(\d+)-(\d*)/.exec(
        route.request().headers().range || "",
      );
      const start = range ? Number(range[1]) : 0;
      const end = range?.[2]
        ? Math.min(Number(range[2]), audioBytes.length - 1)
        : audioBytes.length - 1;
      return route.fulfill({
        status: range ? 206 : 200,
        contentType: "audio/wav",
        headers: {
          "Accept-Ranges": "bytes",
          "Content-Length": String(end - start + 1),
          ...(range
            ? { "Content-Range": `bytes ${start}-${end}/${audioBytes.length}` }
            : {}),
        },
        body: audioBytes.subarray(start, end + 1),
      });
    },
  );
  await page.route(
    "**/api/backend/assets/citation-regression/overlap",
    (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          asset_id: "citation-regression",
          pairs: [],
          incoming: [],
          usage: null,
        }),
      }),
  );
  await page.goto("/dashboard/submissions/citation-regression");
  await expect(
    page.getByRole("heading", { name: "Citation rendering regression" }),
  ).toBeVisible();
  const overviewTab = page.getByRole("tab", { name: "Overview", exact: true });
  await overviewTab.focus();
  await page.keyboard.press("ArrowRight");
  await expect(
    page.getByRole("tab", { name: "Transcript", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await expect
    .poll(() =>
      page
        .getByLabel("Submitted recording", { exact: true })
        .evaluate((audio: HTMLAudioElement) => audio.readyState),
    )
    .toBeGreaterThan(0);
  await page
    .getByRole("button", { name: "Seek to 1.5 seconds", exact: true })
    .click();
  await expect
    .poll(() =>
      page
        .getByLabel("Submitted recording", { exact: true })
        .evaluate((audio: HTMLAudioElement) => audio.currentTime),
    )
    .toBeCloseTo(1.5, 1);
  await expect(page.locator(".transcript-active")).toHaveText(
    /Explicit offline UI fixture/,
  );
  await page.getByLabel("Playback speed", { exact: true }).selectOption("1.5");
  await expect
    .poll(() =>
      page
        .getByLabel("Submitted recording", { exact: true })
        .evaluate((audio: HTMLAudioElement) => audio.playbackRate),
    )
    .toBe(1.5);
  await expect(page.locator(".speech-interval")).toHaveCount(1);
  await page.getByRole("slider", { name: "Seek recording" }).focus();
  await page.keyboard.press("Home");
  await page.keyboard.press("ArrowRight");
  await expect
    .poll(() =>
      page
        .getByLabel("Submitted recording", { exact: true })
        .evaluate((audio: HTMLAudioElement) => audio.currentTime),
    )
    .toBeCloseTo(0.01, 2);
  await page.getByRole("tab", { name: "Compliance", exact: true }).click();
  await page
    .getByText("Administrative workflow conditions", { exact: true })
    .click();
  await expect(
    page.getByText("Studio upload and review-request receipts are present.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "Missing source provenance: special_conditions. Review is required.",
      { exact: true },
    ),
  ).toBeVisible();
  await page
    .getByText("Supporting approved contract clauses", { exact: true })
    .click();
  await expect(page.locator(".report-panel blockquote")).toHaveCount(1);
  await expect(page.locator(".report-panel blockquote")).toHaveText(
    "Each advertisement includes 30 seconds of spoken voice.",
  );
  await expect(
    page.getByText("Unverified text must not render", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Invalid page must not render", { exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("tab", { name: "Identity & authorization", exact: true })
    .click();
  await expect(
    page.getByText("Identity not automatically verified", { exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Overview", exact: true }).click();
  await expect(page.getByLabel("Compliance provider")).toHaveValue("live");
});

test("artist resolves an actual first-party excerpt with same, separate and uncertain decisions", async ({
  page,
}) => {
  await page.goto("/dashboard");
  const apiPath = "/api/backend";
  const licenseResponse = await page.request.post(`${apiPath}/licenses`, {
    data: {
      title: `Browser overlap resolution ${Date.now()}`,
      studio_id: "studio_demo",
    },
  });
  expect(licenseResponse.status()).toBe(201);
  const license = await licenseResponse.json();
  expect(
    (
      await page.request.post(`${apiPath}/licenses/${license.id}/contract`, {
        multipart: {
          file: {
            name: "sample-license.pdf",
            mimeType: "application/pdf",
            buffer: readFileSync(path.join(fixtures, "sample-license.pdf")),
          },
        },
      })
    ).ok(),
  ).toBe(true);
  const extracted = await (
    await page.request.post(`${apiPath}/licenses/${license.id}/extract`, {
      data: { use_demo_fixture: true },
    })
  ).json();
  expect(
    (
      await page.request.post(`${apiPath}/licenses/${license.id}/approve`, {
        data: {
          terms: extracted.terms,
          expected_version: extracted.version,
          note: "Fixture-only source review for browser overlap regression.",
        },
      })
    ).ok(),
  ).toBe(true);
  await page
    .getByRole("combobox", { name: "Workspace role" })
    .selectOption("studio");
  await expect(
    page.getByRole("heading", { name: "Create with permission." }),
  ).toBeVisible();
  const upload = async (file: string, name: string) => {
    const response = await page.request.post(`${apiPath}/assets`, {
      multipart: {
        license_id: license.id,
        campaign: JSON.stringify({
          name,
          region: "US",
          medium: "online advertising",
          language: "English",
          category: "consumer products",
          intended_use_date: "2026-11-09",
        }),
        file: {
          name: file,
          mimeType: "audio/wav",
          buffer: readFileSync(path.join(fixtures, file)),
        },
      },
    });
    expect(response.status()).toBe(201);
    const asset = await response.json();
    expect(
      (
        await page.request.post(`${apiPath}/assets/${asset.id}/analyze`, {
          data: { use_demo_fixture: true },
        })
      ).ok(),
    ).toBe(true);
    return asset;
  };
  const original = await upload(
    "sample-narration.wav",
    "Browser original usage",
  );
  const excerpt = await upload("scenario-excerpt.wav", "Browser edited usage");
  expect(
    (
      await page.request.post(`${apiPath}/assets/${excerpt.id}/evaluate`, {
        data: { use_demo_fixture: true },
      })
    ).ok(),
  ).toBe(true);
  expect(
    (
      await page.request.post(`${apiPath}/assets/${excerpt.id}/overlap`, {
        data: {
          related_asset_id: original.id,
          decision: "SAME_USAGE",
          note: "Studio cannot decide for the artist.",
        },
      })
    ).status(),
  ).toBe(403);
  await page.goto(`/dashboard/submissions/${excerpt.id}`);
  await page.getByRole("tab", { name: "Overlap review", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Related recordings & overlap review" }),
  ).toBeVisible();
  await expect(page.getByLabel("Overlap review decision")).toHaveCount(0);
  await page
    .getByRole("combobox", { name: "Workspace role" })
    .selectOption("artist");
  await page
    .getByRole("tab", { name: "Identity & authorization", exact: true })
    .click();
  await page
    .getByLabel("I confirm the licensed speaker identity for this asset")
    .check();
  await page
    .getByLabel("I authorize this asset and its declared campaign")
    .check();
  await page
    .getByLabel("Identity and authorization review note")
    .fill(
      "OFFLINE FIXTURE ONLY: simulated artist review of the stock synthetic excerpt.",
    );
  await page
    .getByRole("button", { name: "Save artist usage review", exact: true })
    .click();
  await expect(
    page.getByText("Artist confirmation recorded", { exact: false }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Overlap review", exact: true }).click();
  await page.getByLabel("Overlap review decision").selectOption("UNCERTAIN");
  await page
    .getByLabel("Overlap review note")
    .fill("Fixture artist requests additional comparison before deciding.");
  await page
    .getByRole("button", { name: "Save overlap decision", exact: true })
    .click();
  await expect(
    page.getByText("Recorded decision: uncertain", { exact: false }),
  ).toBeVisible();
  let state = await (
    await page.request.get(`${apiPath}/assets/${excerpt.id}`)
  ).json();
  expect(state.compliance_state).toBe("NEEDS_REVIEW");
  await page.getByLabel("Overlap review decision").selectOption("SAME_USAGE");
  await page
    .getByLabel("Overlap review note")
    .fill(
      "Fixture artist compared the original and its actual eighteen-second edited excerpt.",
    );
  await page
    .getByRole("button", { name: "Save overlap decision", exact: true })
    .click();
  await expect(
    page.getByText("Recorded decision: same usage", { exact: false }),
  ).toBeVisible();
  state = await (
    await page.request.get(`${apiPath}/assets/${excerpt.id}`)
  ).json();
  expect(state.compliance_state).toBe("COMPLIANT");
  expect(state.royalty).toBeNull();
  expect(state.report.result.billing_usage.canonical_asset_id).toBe(
    original.id,
  );
  await page.reload();
  await page.getByRole("tab", { name: "Overlap review", exact: true }).click();
  await expect(page.getByLabel("Overlap review decision")).toHaveValue(
    "SAME_USAGE",
  );
  await page.getByRole("tab", { name: "Compliance", exact: true }).click();
  await expect(
    page.getByText("Overlap review resolved", { exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Overlap review", exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await page.screenshot({
    path: "test-results/overlap-review-mobile.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 1280, height: 720 });
  await page
    .getByLabel("Overlap review decision")
    .selectOption("SEPARATE_USAGE");
  await page
    .getByLabel("Overlap review note")
    .fill(
      "Fixture artist explicitly treats this edited version as independently licensed usage.",
    );
  await page
    .getByRole("button", { name: "Save overlap decision", exact: true })
    .click();
  await expect(
    page.getByText("Recorded decision: separate usage", { exact: false }),
  ).toBeVisible();
  state = await (
    await page.request.get(`${apiPath}/assets/${excerpt.id}`)
  ).json();
  expect(state.compliance_state).toBe("COMPLIANT");
  expect(state.royalty.status).toBe("NO_CHARGE");
  expect(state.royalty.amount).toBe("0.00");
  expect(state.invoice).toBeNull();
});
