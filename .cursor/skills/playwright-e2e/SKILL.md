---
name: playwright-e2e
description: Manages E2E testing with Playwright for the IntelliForge Learning platform. Use when writing, running, or debugging E2E tests, adding test coverage, testing new features, or asking about test structure, selectors, or CI integration.
---

# Playwright E2E Testing — IntelliForge Learning

## Quick Start

```bash
# Run all tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e/auth.spec.ts

# Run with UI mode (interactive)
npx playwright test --ui

# Run headed (see browser)
npx playwright test --headed

# Run a single test by name
npx playwright test -g "should show sign in"

# Generate HTML report
npx playwright show-report
```

## Project Structure

```
tests/
├── e2e/                          # Test specs grouped by feature
│   ├── ai-tutor.spec.ts          # AI Tutor chatbot API + UI
│   ├── api-coverage.spec.ts      # Broad API auth gates, validation, edge cases
│   ├── auth.spec.ts              # Auth guards for pages + API endpoints
│   ├── certificate-verify.spec.ts # Certificate verification page + API
│   ├── courses.spec.ts           # Browse, detail, learn page (real + mocked)
│   ├── dashboard.spec.ts         # Dashboard tabs, empty states, journey strip
│   ├── discussions.spec.ts       # Discussion API + UI (auth, sort, CRUD)
│   ├── feedback.spec.ts          # Feedback page + API
│   ├── gamification.spec.ts      # XP, streaks, badges, leaderboard
│   ├── learning-paths.spec.ts    # Learning paths pages + API
│   ├── navigation.spec.ts        # Navbar, cross-page linking, SEO, 404
│   ├── register.spec.ts          # Register form + sessions page
│   ├── responsive.spec.ts        # Mobile + tablet viewport rendering
│   ├── search.spec.ts           # Search API validation + edge cases
│   └── sessions-admin.spec.ts   # Admin sessions, Zoom status, meeting provider
├── fixtures/                     # Shared test fixtures
│   └── test-fixtures.ts          # Custom fixtures (authed page, etc.)
└── helpers/                      # Utility functions
    └── selectors.ts              # Reusable selectors & constants
playwright.config.ts              # Playwright configuration
```

## Configuration

File: `playwright.config.ts` at project root.

- **Base URL**: `http://localhost:3000` (dev) or the `E2E_BASE_URL` env var
- **Browsers**: Chromium (primary), Firefox, WebKit (optional)
- **Auth state**: Stored in `tests/.auth/` via `storageState`
- **Timeouts**: 30s test, 10s action, 60s navigation
- **Retries**: 1 on CI, 0 locally
- **Workers**: 1 (serial) — tests share DB state

## Auth Strategy

NextAuth Google OAuth cannot be automated directly. Use one of:

1. **Storage state** (recommended): Sign in once manually, save cookies:
   ```bash
   npx playwright codegen http://localhost:3000 --save-storage=tests/.auth/user.json
   ```
   Then use `storageState` in test config or fixture.

2. **Test API bypass**: If `NODE_ENV=test`, create a test-only session endpoint.

3. **Mock session**: For non-auth-dependent tests, mock the session via page context.

## Writing Tests

### Conventions

- File naming: `feature-name.spec.ts`
- Use `test.describe()` to group related tests
- Use `test.beforeEach()` for shared setup (e.g., navigate to page)
- Prefer `getByRole()`, `getByText()`, `getByPlaceholder()` over CSS selectors
- Use `data-testid` attributes for complex components (add to source if needed)
- Each test should be independent — no reliance on other test ordering

### Test Template

```typescript
import { test, expect } from "@playwright/test";

test.describe("Feature Name", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/target-page");
  });

  test("should do expected behavior", async ({ page }) => {
    // Arrange
    await page.getByRole("button", { name: "Action" }).click();

    // Act
    await page.getByPlaceholder("Enter value").fill("test");
    await page.getByRole("button", { name: "Submit" }).click();

    // Assert
    await expect(page.getByText("Success")).toBeVisible();
  });
});
```

### Common Patterns

**Wait for API response:**
```typescript
const [response] = await Promise.all([
  page.waitForResponse(resp => resp.url().includes("/api/endpoint") && resp.status() === 200),
  page.getByRole("button", { name: "Submit" }).click(),
]);
```

**Test toast/notification:**
```typescript
await expect(page.locator("[role='alert']")).toContainText("Success");
```

**Test navigation:**
```typescript
await page.getByRole("link", { name: "Dashboard" }).click();
await expect(page).toHaveURL(/\/dashboard/);
```

**Mock API for isolated tests:**
```typescript
await page.route("/api/gamification/profile", route =>
  route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ totalXP: 150, rank: 3 }),
  })
);
```

## Selectors Reference

| Element | Selector |
|---------|----------|
| Navbar links | `nav >> a[href="/path"]` or `getByRole("link", { name })` |
| Glass cards | `.glass-card` |
| Primary buttons | `.btn-primary` or `getByRole("button", { name })` |
| Input fields | `.input-field` or `getByPlaceholder()` |
| AI Tutor button | `button:has-text("+AI Tutor")` |
| Discussion tab | `button:has-text("Discussions")` |
| Achievements tab | `button:has-text("Achievements")` |
| Chat messages | `[data-testid="chat-message"]` |
| Leaderboard | `[data-testid="leaderboard"]` |

## Adding Tests for New Features

1. Create `tests/e2e/feature-name.spec.ts`
2. Add `data-testid` attributes to components if needed
3. Write tests covering: happy path, error states, edge cases, mobile responsive
4. Run `npx playwright test tests/e2e/feature-name.spec.ts --headed` to verify
5. Update this skill if new patterns emerge

## CI Integration

Add to GitHub Actions workflow:

```yaml
- name: Install Playwright
  run: npx playwright install --with-deps chromium
- name: Run E2E tests
  run: npx playwright test
  env:
    E2E_BASE_URL: http://localhost:3000
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: playwright-report
    path: playwright-report/
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Timeout on navigation | Increase `navigationTimeout` in config |
| Auth expired | Re-run `--save-storage` to refresh session cookies |
| Flaky test | Add `await page.waitForLoadState("networkidle")` or explicit waits |
| Element not found | Check if component is lazy-loaded, wait for it with `waitFor()` |
