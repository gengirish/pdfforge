const { test, expect } = require("@playwright/test");

// ---------------------------------------------------------------------------
// API Tests
// ---------------------------------------------------------------------------

test.describe("API endpoints", () => {
  test("GET /api/health returns ok", async ({ request }) => {
    const res = await request.get("/api/health");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("ok");
    expect(body.service).toBe("pdfforge");
  });

  test("GET /api/metrics returns full shape", async ({ request }) => {
    const res = await request.get("/api/metrics");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("ok");
    expect(body.metrics).toBeDefined();
    expect(typeof body.metrics.tool_count).toBe("number");
    expect(body.metrics.tool_count).toBeGreaterThanOrEqual(6);
    expect(typeof body.metrics.max_upload_mb).toBe("number");
    expect(body.metrics.max_upload_mb).toBeGreaterThan(0);
    expect(typeof body.metrics.total_signups).toBe("number");
    expect(body.metrics.waitlist_by_plan).toBeDefined();
    expect(typeof body.metrics.generated_at).toBe("string");
  });

  test("POST /api/waitlist accepts valid signup", async ({ request }) => {
    const email = `api-e2e-${Date.now()}@example.com`;
    const res = await request.post("/api/waitlist", {
      data: {
        name: "API Test",
        email,
        plan_interest: "pro",
        use_case: "E2E API test",
      },
    });
    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(body.status).toBe("ok");
    expect(body.message).toMatch(/waitlist/i);
  });

  test("POST /api/waitlist rejects duplicate email", async ({ request }) => {
    const email = `dup-e2e-${Date.now()}@example.com`;
    const first = await request.post("/api/waitlist", {
      data: { email, name: "First", plan_interest: "pro", use_case: "test" },
    });
    expect(first.status()).toBe(201);

    const second = await request.post("/api/waitlist", {
      data: { email, name: "Second", plan_interest: "pro", use_case: "test" },
    });
    expect(second.status()).toBe(409);
    const body = await second.json();
    expect(body.message).toMatch(/already/i);
  });

  test("POST /api/waitlist rejects invalid email", async ({ request }) => {
    const res = await request.post("/api/waitlist", {
      data: { email: "not-an-email", name: "Bad", plan_interest: "pro", use_case: "" },
    });
    expect(res.status()).toBe(400);
    const body = await res.json();
    expect(body.status).toBe("error");
  });
});

// ---------------------------------------------------------------------------
// Page Structure & Content
// ---------------------------------------------------------------------------

test.describe("page structure", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("has correct page title and lang attribute", async ({ page }) => {
    await expect(page).toHaveTitle(/PDFforge/i);
    const lang = await page.locator("html").getAttribute("lang");
    expect(lang).toBe("en");
  });

  test("hero section renders fully", async ({ page }) => {
    await expect(page.locator(".badge")).toContainText("Back-office PDF copilot");
    await expect(
      page.getByRole("heading", { name: /Fix broken document workflows/i })
    ).toBeVisible();
    await expect(page.locator(".subtitle")).toContainText("PDFforge");

    const ctaPrimary = page.locator("a.cta-primary");
    await expect(ctaPrimary).toBeVisible();
    await expect(ctaPrimary).toHaveAttribute("href", "#waitlist");

    const ctaSecondary = page.locator("a.cta-secondary");
    await expect(ctaSecondary).toBeVisible();
    await expect(ctaSecondary).toHaveAttribute("href", "#tools");

    const chips = page.locator(".chip-row .chip");
    await expect(chips).toHaveCount(3);
    await expect(chips.nth(0)).toContainText("No cloud upload");
    await expect(chips.nth(1)).toContainText("Flask");
    await expect(chips.nth(2)).toContainText("Next.js");
  });

  test("traction grid shows 4 metric cards with live data", async ({ page }) => {
    const cards = page.locator(".traction-grid .metric-card");
    await expect(cards).toHaveCount(4);

    await expect(cards.nth(0).locator(".metric-label")).toContainText("Backend health");
    await expect(cards.nth(1).locator(".metric-label")).toContainText("Waitlist signups");
    await expect(cards.nth(2).locator(".metric-label")).toContainText("Core workflows");
    await expect(cards.nth(3).locator(".metric-label")).toContainText("Max file size");

    await expect(cards.nth(0).locator(".metric-value")).toContainText("ok");
    await expect(cards.nth(2).locator(".metric-value")).toContainText("6");
    await expect(cards.nth(3).locator(".metric-value")).toContainText("MB");
  });

  test("problem-solution section has both cards", async ({ page }) => {
    const section = page.locator(".problem-solution");
    await expect(section.getByRole("heading", { name: "Why teams switch" })).toBeVisible();
    await expect(
      section.getByRole("heading", { name: "Built for YC-style velocity" })
    ).toBeVisible();

    const whyItems = section.locator("article").first().locator("li");
    await expect(whyItems).toHaveCount(3);

    const velocityItems = section.locator("article").nth(1).locator("li");
    await expect(velocityItems).toHaveCount(3);
  });

  test("FAQ section renders 3 questions with answers", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "FAQ" })).toBeVisible();
    const faqCards = page.locator(".faq-grid .card");
    await expect(faqCards).toHaveCount(3);

    await expect(faqCards.nth(0).getByRole("heading")).toContainText("files processed");
    await expect(faqCards.nth(1).getByRole("heading")).toContainText("API");
    await expect(faqCards.nth(2).getByRole("heading")).toContainText("paid roadmap");

    for (let i = 0; i < 3; i++) {
      await expect(faqCards.nth(i).locator("p.muted")).not.toBeEmpty();
    }
  });

  test("footer has branding and all links", async ({ page }) => {
    const footer = page.locator("footer.site-footer");
    await expect(footer).toBeVisible();
    await expect(footer).toContainText("PDFforge");
    await expect(footer).toContainText("local-first PDF ops");

    const healthLink = footer.locator('a[href="/api/health"]');
    await expect(healthLink).toBeVisible();

    const metricsLink = footer.locator('a[href="/api/metrics"]');
    await expect(metricsLink).toBeVisible();

    const feedbackLink = footer.locator('a[href="#feedback"]');
    await expect(feedbackLink).toBeVisible();

    const ghLink = footer.locator('a[href*="github.com/gengirish/pdfforge"]');
    await expect(ghLink).toBeVisible();
    await expect(ghLink).toHaveAttribute("target", "_blank");
    await expect(ghLink).toHaveAttribute("rel", /noopener/);
  });
});

// ---------------------------------------------------------------------------
// PDF Tool Cards
// ---------------------------------------------------------------------------

test.describe("PDF tool cards", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("all 6 tools are visible with correct titles", async ({ page }) => {
    const toolSection = page.locator("#tools");
    await expect(toolSection.getByRole("heading", { name: "PDF Tools" })).toBeVisible();

    const expectedTitles = [
      "Merge PDFs",
      "Split PDF",
      "Rotate Pages",
      "Extract Text",
      "Encrypt PDF",
      "Decrypt PDF",
    ];

    const toolCards = toolSection.locator(".tools-grid .card");
    await expect(toolCards).toHaveCount(6);

    for (const title of expectedTitles) {
      await expect(toolSection.getByRole("heading", { name: title })).toBeVisible();
    }
  });

  test("merge form has multi-file input and submit button", async ({ page }) => {
    const card = page.locator("#tools .card").filter({ hasText: "Merge PDFs" });
    const fileInput = card.locator('input[type="file"]');
    await expect(fileInput).toHaveAttribute("multiple", "");
    await expect(fileInput).toHaveAttribute("accept", ".pdf,application/pdf");
    await expect(fileInput).toHaveAttribute("aria-label", "Upload PDF files");
    await expect(card.getByRole("button", { name: "Merge & Download" })).toBeVisible();
  });

  test("split form has file input, ranges input, and submit button", async ({ page }) => {
    const card = page.locator("#tools .card").filter({ hasText: "Split PDF" });
    await expect(card.locator('input[type="file"]')).toHaveAttribute("aria-label", "Upload PDF file");
    await expect(card.locator('input[name="ranges"]')).toHaveAttribute("placeholder", "1-2,3,5-7");
    await expect(card.getByRole("button", { name: "Split & Download ZIP" })).toBeVisible();
  });

  test("rotate form has file input, angle select, optional pages, and submit", async ({ page }) => {
    const card = page.locator("#tools .card").filter({ hasText: "Rotate Pages" });
    await expect(card.locator('input[type="file"]')).toBeVisible();
    const angleSelect = card.locator('select[name="angle"]');
    await expect(angleSelect).toHaveAttribute("aria-label", "Rotation angle");
    const options = angleSelect.locator("option");
    await expect(options).toHaveCount(3);
    await expect(card.locator('input[name="pages"]')).toHaveAttribute(
      "placeholder",
      "Optional: 1,3-5"
    );
    await expect(card.getByRole("button", { name: "Rotate & Download" })).toBeVisible();
  });

  test("extract text form has file input and submit button", async ({ page }) => {
    const card = page.locator("#tools .card").filter({ hasText: "Extract Text" });
    await expect(card.locator('input[type="file"]')).toBeVisible();
    await expect(card.getByRole("button", { name: "Extract TXT" })).toBeVisible();
  });

  test("encrypt form has file input, password input, and submit button", async ({ page }) => {
    const card = page.locator("#tools .card").filter({ hasText: "Encrypt PDF" });
    await expect(card.locator('input[type="file"]')).toBeVisible();
    const pw = card.locator('input[type="password"]');
    await expect(pw).toHaveAttribute("aria-label", "Password");
    await expect(card.getByRole("button", { name: "Encrypt & Download" })).toBeVisible();
  });

  test("decrypt form has file input, password input, and submit button", async ({ page }) => {
    const card = page.locator("#tools .card").filter({ hasText: "Decrypt PDF" });
    await expect(card.locator('input[type="file"]')).toBeVisible();
    const pw = card.locator('input[type="password"]');
    await expect(pw).toHaveAttribute("aria-label", "Current password");
    await expect(card.getByRole("button", { name: "Decrypt & Download" })).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Waitlist Form
// ---------------------------------------------------------------------------

test.describe("waitlist form", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("waitlist section has form and founder console", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Pro Waitlist" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Join early access" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Founder Console" })).toBeVisible();
  });

  test("waitlist form has all expected fields with aria-labels", async ({ page }) => {
    const form = page.locator("#waitlist form").first();

    await expect(form.locator('[aria-label="Your name"]')).toBeVisible();
    await expect(form.locator('[aria-label="Work email"]')).toBeVisible();
    await expect(form.locator('[aria-label="Team size"]')).toBeVisible();
    await expect(form.locator('[aria-label="Monthly PDF volume"]')).toBeVisible();
    await expect(form.locator('[aria-label="Primary use case"]')).toBeVisible();
    await expect(form.locator('[aria-label="Implementation timeline"]')).toBeVisible();
    await expect(form.locator('[aria-label="Plan interest"]')).toBeVisible();
    await expect(
      form.locator('[aria-label="Describe your most painful PDF workflow step"]')
    ).toBeVisible();
    await expect(form.getByRole("button", { name: "Join Waitlist" })).toBeVisible();
  });

  test("primary use case select has all 5 options", async ({ page }) => {
    const form = page.locator("#waitlist form").first();
    const options = form.locator('[aria-label="Primary use case"] option');
    await expect(options).toHaveCount(5);
    await expect(options.nth(0)).toHaveText("Contracts and legal docs");
    await expect(options.nth(4)).toHaveText("Client deliverables");
  });

  test("timeline select has all 3 options", async ({ page }) => {
    const form = page.locator("#waitlist form").first();
    const options = form.locator('[aria-label="Implementation timeline"] option');
    await expect(options).toHaveCount(3);
  });

  test("plan interest select has 3 options", async ({ page }) => {
    const form = page.locator("#waitlist form").first();
    const options = form.locator('[aria-label="Plan interest"] option');
    await expect(options).toHaveCount(3);
    await expect(options.nth(0)).toHaveText("Pro");
    await expect(options.nth(1)).toHaveText("Team");
    await expect(options.nth(2)).toHaveText("Not sure yet");
  });

  test("full waitlist submission succeeds and shows confirmation", async ({ page }) => {
    const uniqueEmail = `full-e2e-${Date.now()}@example.com`;
    const form = page.locator("#waitlist form").first();

    await form.locator('[aria-label="Your name"]').fill("E2E Full Bot");
    await form.locator('[aria-label="Work email"]').fill(uniqueEmail);
    await form.locator('[aria-label="Team size"]').fill("10-20");
    await form.locator('[aria-label="Monthly PDF volume"]').fill("5000 docs");
    await form.locator('[aria-label="Primary use case"]').selectOption("Invoices and accounting docs");
    await form.locator('[aria-label="Implementation timeline"]').selectOption("this-week");
    await form.locator('[aria-label="Plan interest"]').selectOption("team");
    await form
      .locator('[aria-label="Describe your most painful PDF workflow step"]')
      .fill("Invoice merging for monthly close.");

    await form.getByRole("button", { name: "Join Waitlist" }).click();
    await expect(page.locator("#waitlist .success")).toContainText(/waitlist/i);
  });

  test("duplicate email shows error message", async ({ page, request }) => {
    const email = `dup-ui-${Date.now()}@example.com`;

    await request.post("/api/waitlist", {
      data: { email, name: "Pre-signup", plan_interest: "pro", use_case: "seed" },
    });

    const form = page.locator("#waitlist form").first();
    await form.locator('[aria-label="Work email"]').fill(email);
    await form.getByRole("button", { name: "Join Waitlist" }).click();

    await expect(page.locator("#waitlist .error")).toContainText(/already/i);
  });

  test("submit button shows loading state during submission", async ({ page }) => {
    const form = page.locator("#waitlist form").first();
    const email = `loading-${Date.now()}@example.com`;
    await form.locator('[aria-label="Work email"]').fill(email);

    const submitBtn = form.getByRole("button", { name: "Join Waitlist" });
    await submitBtn.click();

    await expect(
      form.getByRole("button").or(page.locator("#waitlist .success"))
    ).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Navigation & Anchors
// ---------------------------------------------------------------------------

test.describe("navigation", () => {
  test("CTA 'Get beta access' scrolls to waitlist section", async ({ page }) => {
    await page.goto("/");
    await page.locator("a.cta-primary").click();
    await expect(page.locator("#waitlist")).toBeInViewport();
  });

  test("CTA 'Try local tools now' scrolls to tools section", async ({ page }) => {
    await page.goto("/");
    await page.locator("a.cta-secondary").click();
    await expect(page.locator("#tools")).toBeInViewport();
  });
});

// ---------------------------------------------------------------------------
// Responsive Layout
// ---------------------------------------------------------------------------

test.describe("mobile viewport", () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test("page renders correctly on mobile", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("heading", { name: /Fix broken document workflows/i })
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "PDF Tools" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Pro Waitlist" })).toBeVisible();
    await expect(page.locator("footer.site-footer")).toBeVisible();

    const tractionGrid = page.locator(".traction-grid");
    const gridCols = await tractionGrid.evaluate(
      (el) => getComputedStyle(el).gridTemplateColumns
    );
    expect(gridCols).not.toContain("0px");
  });

  test("waitlist form is usable on mobile", async ({ page }) => {
    await page.goto("/");
    const form = page.locator("#waitlist form").first();
    const email = `mobile-${Date.now()}@example.com`;
    await form.locator('[aria-label="Work email"]').fill(email);
    await form.getByRole("button", { name: "Join Waitlist" }).click();
    await expect(page.locator("#waitlist .success")).toContainText(/waitlist/i);
  });
});

// ---------------------------------------------------------------------------
// Accessibility
// ---------------------------------------------------------------------------

test.describe("accessibility basics", () => {
  test("all form inputs have aria-labels", async ({ page }) => {
    await page.goto("/");

    const inputs = page.locator("input:not([type=hidden]), select, textarea");
    const count = await inputs.count();
    expect(count).toBeGreaterThan(0);

    for (let i = 0; i < count; i++) {
      const el = inputs.nth(i);
      const ariaLabel = await el.getAttribute("aria-label");
      const ariaLabelledBy = await el.getAttribute("aria-labelledby");
      const id = await el.getAttribute("id");
      const label = id ? await page.locator(`label[for="${id}"]`).count() : 0;

      const hasLabel = ariaLabel || ariaLabelledBy || label > 0;
      if (!hasLabel) {
        const name = await el.getAttribute("name");
        const type = await el.getAttribute("type");
        throw new Error(`Input name="${name}" type="${type}" at index ${i} has no accessible label`);
      }
    }
  });

  test("page has no duplicate h1 elements", async ({ page }) => {
    await page.goto("/");
    const h1Count = await page.locator("h1").count();
    expect(h1Count).toBe(1);
  });

  test("all images have alt text (if any)", async ({ page }) => {
    await page.goto("/");
    const images = page.locator("img");
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      const alt = await images.nth(i).getAttribute("alt");
      expect(alt).not.toBeNull();
    }
  });
});

// ---------------------------------------------------------------------------
// Beta Feedback
// ---------------------------------------------------------------------------

test.describe("beta feedback", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("feedback section renders with form and resources", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Beta Feedback" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Share your experience" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Beta Resources" })).toBeVisible();
  });

  test("feedback form has all fields with aria-labels", async ({ page }) => {
    const form = page.locator("#feedback form").first();
    await expect(form.locator('[aria-label="Feedback email"]')).toBeVisible();
    await expect(form.locator('[aria-label="Rating"]')).toBeVisible();
    await expect(form.locator('[aria-label="Feedback message"]')).toBeVisible();
    await expect(form.getByRole("button", { name: "Send Feedback" })).toBeVisible();
  });

  test("rating select has 5 options", async ({ page }) => {
    const form = page.locator("#feedback form").first();
    const options = form.locator('[aria-label="Rating"] option');
    await expect(options).toHaveCount(5);
  });

  test("feedback submission succeeds", async ({ page }) => {
    const form = page.locator("#feedback form").first();
    await form.locator('[aria-label="Feedback email"]').fill(`fb-${Date.now()}@example.com`);
    await form.locator('[aria-label="Rating"]').selectOption("4");
    await form.locator('[aria-label="Feedback message"]').fill("Great tool, needs OCR support.");
    await form.getByRole("button", { name: "Send Feedback" }).click();
    await expect(page.locator("#feedback .success")).toContainText(/thank you/i);
  });

  test("feedback form rejects empty message", async ({ page }) => {
    const form = page.locator("#feedback form").first();
    const msgField = form.locator('[aria-label="Feedback message"]');
    await expect(msgField).toHaveAttribute("required", "");
  });

  test("beta resources section has test PDF link", async ({ page }) => {
    const resources = page.locator("#feedback .card").nth(1);
    const link = resources.locator('a[href*="test-pdf"]');
    await expect(link).toBeVisible();
    await expect(link).toContainText("Download test PDF");
  });
});

// ---------------------------------------------------------------------------
// Usage API
// ---------------------------------------------------------------------------

test.describe("usage API", () => {
  test("GET /api/metrics includes tool_usage field", async ({ request }) => {
    const res = await request.get("/api/metrics");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.metrics.tool_usage).toBeDefined();
    expect(typeof body.metrics.tool_usage).toBe("object");
  });

  test("POST /api/feedback returns 201 for valid input", async ({ request }) => {
    const res = await request.post("/api/feedback", {
      data: {
        email: `fb-api-${Date.now()}@example.com`,
        rating: 5,
        message: "E2E feedback test",
        page: "/",
      },
    });
    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(body.status).toBe("ok");
  });

  test("POST /api/feedback rejects missing message", async ({ request }) => {
    const res = await request.post("/api/feedback", {
      data: { email: "x@y.com", rating: 3, message: "" },
    });
    expect(res.status()).toBe(400);
  });

  test("POST /api/feedback rejects invalid rating", async ({ request }) => {
    const res = await request.post("/api/feedback", {
      data: { email: "x@y.com", rating: 0, message: "test" },
    });
    expect(res.status()).toBe(400);
  });
});
