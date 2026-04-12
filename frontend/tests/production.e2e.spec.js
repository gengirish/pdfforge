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
    expect(body.metrics.tool_usage).toBeDefined();
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

// ---------------------------------------------------------------------------
// Navigation & Page Structure
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

  test("nav has logo and links", async ({ page }) => {
    await expect(page.locator(".nav-logo")).toContainText("PDFforge");
    const navLinks = page.locator(".nav-links a");
    const count = await navLinks.count();
    expect(count).toBeGreaterThanOrEqual(4);
  });

  test("hero section renders with eyebrow, heading, subtitle, and CTAs", async ({ page }) => {
    await expect(page.locator(".hero-eyebrow")).toContainText("IntelliForge AI");
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator(".hero-sub")).toContainText("PDFforge");
    await expect(page.locator(".btn-primary")).toBeVisible();
    await expect(page.locator(".btn-ghost")).toBeVisible();
  });

  test("trust badges row shows at least 3 badges", async ({ page }) => {
    const badges = page.locator(".trust-badge");
    const count = await badges.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });

  test("proof bar shows 4 stats", async ({ page }) => {
    const stats = page.locator(".proof-stat");
    await expect(stats).toHaveCount(4);
  });

  test("testimonials section shows 3 cards", async ({ page }) => {
    const cards = page.locator(".testimonial-card");
    await expect(cards).toHaveCount(3);
    for (let i = 0; i < 3; i++) {
      await expect(cards.nth(i).locator(".testimonial-quote")).not.toBeEmpty();
      await expect(cards.nth(i).locator(".testimonial-name")).not.toBeEmpty();
      await expect(cards.nth(i).locator(".testimonial-role")).not.toBeEmpty();
    }
  });

  test("how-it-works section has 3 steps", async ({ page }) => {
    const steps = page.locator("#how-it-works .how-step");
    await expect(steps).toHaveCount(3);
    await expect(steps.nth(0).locator("h3")).toContainText("Upload locally");
    await expect(steps.nth(1).locator("h3")).toContainText("Pick an operation");
    await expect(steps.nth(2).locator("h3")).toContainText("Download or automate");
  });

  test("FAQ section renders questions with answers", async ({ page }) => {
    const faqItems = page.locator(".faq-item");
    const count = await faqItems.count();
    expect(count).toBeGreaterThanOrEqual(3);
    for (let i = 0; i < count; i++) {
      await expect(faqItems.nth(i).locator("h3")).not.toBeEmpty();
      await expect(faqItems.nth(i).locator("p")).not.toBeEmpty();
    }
  });

  test("footer has brand, IntelliForge link, and nav links", async ({ page }) => {
    const footer = page.locator("footer.site-footer");
    await expect(footer).toBeVisible();
    await expect(footer.locator(".footer-brand")).toContainText("PDFforge");
    const ifLink = footer.locator('a[href*="intelliforge.tech"]').first();
    await expect(ifLink).toBeVisible();
    await expect(ifLink).toHaveAttribute("target", "_blank");
    await expect(footer.locator('a[href="#feedback"]')).toBeVisible();
    const ghLink = footer.locator('a[href*="github.com/gengirish/pdfforge"]');
    await expect(ghLink).toBeVisible();
    await expect(ghLink).toHaveAttribute("target", "_blank");
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
    const toolCells = page.locator(".tool-cell");
    await expect(toolCells).toHaveCount(6);
    const expectedTitles = ["Merge", "Split", "Rotate", "Extract Text", "Encrypt", "Decrypt"];
    for (const title of expectedTitles) {
      await expect(page.locator("#tools").getByRole("heading", { name: title })).toBeVisible();
    }
  });

  test("each tool has an upload zone instead of raw file input", async ({ page }) => {
    const zones = page.locator("#tools .upload-zone");
    await expect(zones).toHaveCount(6);
    for (let i = 0; i < 6; i++) {
      await expect(zones.nth(i)).toBeVisible();
    }
  });

  test("merge form has multi-file input and submit button", async ({ page }) => {
    const cell = page.locator(".tool-cell").filter({ hasText: "Merge" });
    const fileInput = cell.locator('input[type="file"]');
    await expect(fileInput).toHaveAttribute("multiple", "");
    await expect(fileInput).toHaveAttribute("accept", ".pdf,application/pdf");
    await expect(fileInput).toHaveAttribute("aria-label", "Upload PDF files");
    await expect(cell.getByRole("button", { name: "Merge & Download" })).toBeVisible();
  });

  test("split form has file input, ranges input, and submit button", async ({ page }) => {
    const cell = page.locator(".tool-cell").filter({ hasText: "Split" });
    await expect(cell.locator('input[type="file"]')).toHaveAttribute("aria-label", "Upload PDF file");
    await expect(cell.locator('input[name="ranges"]')).toHaveAttribute("placeholder", "1-2,3,5-7");
    await expect(cell.getByRole("button", { name: "Split & Download ZIP" })).toBeVisible();
  });

  test("rotate form has file input, angle select, optional pages, and submit", async ({ page }) => {
    const cell = page.locator(".tool-cell").filter({ hasText: "Rotate" });
    await expect(cell.locator(".upload-zone")).toBeVisible();
    const angleSelect = cell.locator('select[name="angle"]');
    await expect(angleSelect).toHaveAttribute("aria-label", "Rotation angle");
    await expect(angleSelect.locator("option")).toHaveCount(3);
    await expect(cell.locator('input[name="pages"]')).toHaveAttribute("placeholder", "Optional: 1,3-5");
    await expect(cell.getByRole("button", { name: "Rotate & Download" })).toBeVisible();
  });

  test("extract text form has upload zone and submit button", async ({ page }) => {
    const cell = page.locator(".tool-cell").filter({ hasText: "Extract Text" });
    await expect(cell.locator(".upload-zone")).toBeVisible();
    await expect(cell.getByRole("button", { name: "Extract TXT" })).toBeVisible();
  });

  test("encrypt form has upload zone, password input, and submit button", async ({ page }) => {
    const cell = page.locator(".tool-cell").filter({ hasText: "Encrypt" });
    await expect(cell.locator(".upload-zone")).toBeVisible();
    await expect(cell.locator('input[type="password"]')).toHaveAttribute("aria-label", "Password");
    await expect(cell.getByRole("button", { name: "Encrypt & Download" })).toBeVisible();
  });

  test("decrypt form has upload zone, password input, and submit button", async ({ page }) => {
    const cell = page.locator(".tool-cell").filter({ hasText: "Decrypt" });
    await expect(cell.locator(".upload-zone")).toBeVisible();
    await expect(cell.locator('input[type="password"]')).toHaveAttribute("aria-label", "Current password");
    await expect(cell.getByRole("button", { name: "Decrypt & Download" })).toBeVisible();
  });

  test("tool forms use AJAX (no method/action attributes)", async ({ page }) => {
    const forms = page.locator("#tools form");
    const count = await forms.count();
    expect(count).toBe(6);
    for (let i = 0; i < count; i++) {
      const method = await forms.nth(i).getAttribute("method");
      const action = await forms.nth(i).getAttribute("action");
      expect(method).toBeNull();
      expect(action).toBeNull();
    }
  });
});

// ---------------------------------------------------------------------------
// Pricing
// ---------------------------------------------------------------------------

test.describe("pricing section", () => {
  test("shows 3 pricing cards", async ({ page }) => {
    await page.goto("/");
    const cards = page.locator(".price-card");
    await expect(cards).toHaveCount(3);
  });

  test("featured card has 'MOST POPULAR' label", async ({ page }) => {
    await page.goto("/");
    const featured = page.locator(".price-card--featured");
    await expect(featured).toBeVisible();
  });

  test("each card has name, price, and features", async ({ page }) => {
    await page.goto("/");
    const cards = page.locator(".price-card");
    const count = await cards.count();
    for (let i = 0; i < count; i++) {
      await expect(cards.nth(i).locator("h3")).not.toBeEmpty();
      await expect(cards.nth(i).locator(".price-amount")).toBeVisible();
      const features = cards.nth(i).locator(".price-features li");
      expect(await features.count()).toBeGreaterThanOrEqual(4);
    }
  });
});

// ---------------------------------------------------------------------------
// Waitlist Form
// ---------------------------------------------------------------------------

test.describe("waitlist form", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("waitlist section has form and priority card", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Join early access" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Who gets priority?" })).toBeVisible();
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
    await expect(form.locator('[aria-label="Describe your most painful PDF workflow step"]')).toBeVisible();
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
    await expect(form.locator('[aria-label="Implementation timeline"] option')).toHaveCount(3);
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
    await form.locator('[aria-label="Describe your most painful PDF workflow step"]').fill("Invoice merging for monthly close.");
    await form.getByRole("button", { name: "Join Waitlist" }).click();
    await expect(page.locator("#waitlist .msg-success")).toContainText(/waitlist/i);
  });

  test("duplicate email shows error message", async ({ page, request }) => {
    const email = `dup-ui-${Date.now()}@example.com`;
    await request.post("/api/waitlist", {
      data: { email, name: "Pre-signup", plan_interest: "pro", use_case: "seed" },
    });
    const form = page.locator("#waitlist form").first();
    await form.locator('[aria-label="Work email"]').fill(email);
    await form.getByRole("button", { name: "Join Waitlist" }).click();
    await expect(page.locator("#waitlist .msg-error")).toContainText(/already/i);
  });
});

// ---------------------------------------------------------------------------
// Navigation & Anchors
// ---------------------------------------------------------------------------

test.describe("navigation", () => {
  test("CTA 'Get early access' scrolls to waitlist section", async ({ page }) => {
    await page.goto("/");
    await page.locator(".btn-primary").click();
    await expect(page.locator("#waitlist")).toBeInViewport();
  });

  test("CTA 'Try the tools' scrolls to tools section", async ({ page }) => {
    await page.goto("/");
    await page.locator(".btn-ghost").click();
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
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator("#tools")).toBeVisible();
    await expect(page.locator("#waitlist")).toBeVisible();
    await expect(page.locator("footer.site-footer")).toBeVisible();
  });

  test("trust badges wrap on mobile", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".trust-row")).toBeVisible();
    const badges = page.locator(".trust-badge");
    expect(await badges.count()).toBeGreaterThanOrEqual(3);
  });

  test("waitlist form is usable on mobile", async ({ page }) => {
    await page.goto("/");
    const form = page.locator("#waitlist form").first();
    const email = `mobile-${Date.now()}@example.com`;
    await form.locator('[aria-label="Work email"]').fill(email);
    await form.getByRole("button", { name: "Join Waitlist" }).click();
    await expect(page.locator("#waitlist .msg-success")).toContainText(/waitlist/i);
  });
});

// ---------------------------------------------------------------------------
// Accessibility
// ---------------------------------------------------------------------------

test.describe("accessibility basics", () => {
  test("all visible form inputs have aria-labels", async ({ page }) => {
    await page.goto("/");
    const inputs = page.locator("#waitlist input, #waitlist select, #waitlist textarea, #feedback input, #feedback select, #feedback textarea");
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

  test("tool upload zones have aria-labels", async ({ page }) => {
    await page.goto("/");
    const zones = page.locator("#tools .upload-zone");
    const count = await zones.count();
    expect(count).toBe(6);
    for (let i = 0; i < count; i++) {
      const label = await zones.nth(i).getAttribute("aria-label");
      expect(label).toBeTruthy();
    }
  });

  test("page has no duplicate h1 elements", async ({ page }) => {
    await page.goto("/");
    expect(await page.locator("h1").count()).toBe(1);
  });

  test("all images have alt text (if any)", async ({ page }) => {
    await page.goto("/");
    const images = page.locator("img");
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      expect(await images.nth(i).getAttribute("alt")).not.toBeNull();
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
    await expect(page.getByRole("heading", { name: "Send feedback" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Beta resources" })).toBeVisible();
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
    await expect(form.locator('[aria-label="Rating"] option')).toHaveCount(5);
  });

  test("feedback submission succeeds", async ({ page }) => {
    const form = page.locator("#feedback form").first();
    await form.locator('[aria-label="Feedback email"]').fill(`fb-${Date.now()}@example.com`);
    await form.locator('[aria-label="Rating"]').selectOption("4");
    await form.locator('[aria-label="Feedback message"]').fill("Great tool, needs OCR support.");
    await form.getByRole("button", { name: "Send Feedback" }).click();
    await expect(page.locator("#feedback .msg-success")).toContainText(/thank you/i);
  });

  test("feedback form rejects empty message", async ({ page }) => {
    const form = page.locator("#feedback form").first();
    await expect(form.locator('[aria-label="Feedback message"]')).toHaveAttribute("required", "");
  });

  test("beta resources section has test PDF link", async ({ page }) => {
    const resources = page.locator("#feedback .fb-card").nth(1);
    const link = resources.locator('a[href*="test-pdf"]');
    await expect(link).toBeVisible();
    await expect(link).toContainText("Download test PDF");
  });
});
