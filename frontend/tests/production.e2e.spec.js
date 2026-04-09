const { test, expect } = require("@playwright/test");

test("landing page loads with core sections", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: /Fix broken document workflows/i })
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "PDF Tools" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Pro Waitlist" })).toBeVisible();
});

test("waitlist form submits successfully", async ({ page }) => {
  await page.goto("/");

  const uniqueEmail = `yc-e2e-${Date.now()}@example.com`;
  const waitlistForm = page.locator("#waitlist form").first();

  await waitlistForm.getByPlaceholder("Name").fill("YC E2E Bot");
  await waitlistForm.getByPlaceholder("Work email").fill(uniqueEmail);
  await waitlistForm.getByPlaceholder("Team size (e.g. 5-10)").fill("5-10");
  await waitlistForm
    .getByPlaceholder("Monthly PDF volume (e.g. 2,000 docs)")
    .fill("2200 docs");
  await waitlistForm.getByRole("combobox").nth(0).selectOption({ label: "Contracts and legal docs" });
  await waitlistForm.getByRole("combobox").nth(1).selectOption({ label: "Need a fix this month" });
  await waitlistForm.getByRole("combobox").nth(2).selectOption({ label: "Pro" });
  await waitlistForm
    .getByPlaceholder("What is the most painful PDF step right now?")
    .fill("Manual merge/split for contracts slows our team.");

  await waitlistForm.getByRole("button", { name: "Join Waitlist" }).click();
  await expect(page.getByText(/Thanks! You are on the waitlist/i)).toBeVisible();
});
