# PDFforge Beta Testing Runbook

## Phase 1 — Closed Alpha (Week 1-2)

### Goal
Validate core tool reliability with 5-10 hand-picked users from the waitlist.

### Selection Criteria
Use the `/api/v1/beta-candidates` endpoint (requires admin token) to surface highest-signal signups:
```bash
curl -H "X-Admin-Token: $TOKEN" https://pdfforge-api.fly.dev/api/v1/beta-candidates?limit=10
```

Scoring factors:
- **Team plan interest** → +3 points
- **Pro plan interest** → +2 points
- **"This week" urgency** → +3 points
- **"This month" urgency** → +2 points
- **High volume keywords** → +2 points
- **Detailed use case (>60 chars)** → +1 point

### Onboarding Steps
1. Send alpha invite email (see templates below)
2. Share the test PDF: `https://pdfforge-api.fly.dev/api/v1/test-pdf`
3. Point technical testers to interactive API docs: `https://pdfforge-api.fly.dev/api/v1/docs` (Swagger) or `/api/v1/redoc` (ReDoc), and the machine-readable manifest at `/api/v1/capabilities` (see repository `README.md` for the full surface: pipeline, batch, async jobs, webhooks).
4. Point them to the feedback form at `#feedback` on the main page
5. Set up a shared Slack/Discord channel for real-time support

### Success Metrics
- 80%+ of alpha users complete at least 3 tool operations
- NPS >= 7 (from feedback ratings)
- Zero data-loss bugs
- <2s median response time for all tools

---

## Phase 2 — Expanded Beta (Week 3-4)

### Goal
Expand to 25-50 users, validate payment flow, gather feature requests.

### Actions
1. Open invites to all "pro" plan waitlist signups
2. Enable Lemon Squeezy checkout (set env vars per `docs/payments-setup.md`)
3. Monitor tool usage via `/api/v1/usage` and `/api/v1/metrics`
4. Review feedback daily via `/api/v1/feedback` (admin-only)

### Key Monitors
```bash
# Daily usage check
curl https://pdfforge-api.fly.dev/api/v1/usage

# Feedback review
curl -H "X-Admin-Token: $TOKEN" https://pdfforge-api.fly.dev/api/v1/feedback

# Waitlist pipeline
curl -H "X-Admin-Token: $TOKEN" https://pdfforge-api.fly.dev/api/v1/waitlist
```

---

## Phase 3 — Open Beta (Week 5-8)

### Goal
Remove invite gate, drive organic signups, validate conversion funnel.

### Actions
1. Remove "beta access" gating — make all tools publicly available
2. Launch on Product Hunt, Hacker News, and relevant subreddits
3. Enable paid plans for all users
4. Set up weekly metrics review cadence

### KPIs
| Metric | Target |
|--------|--------|
| WAU (Weekly Active Users) | 100+ |
| Conversion (free → paid) | 5%+ |
| Feedback rating avg | 4.0+ |
| Tool ops per user per week | 3+ |
| Churn (monthly) | <10% |

---

## Bug Triage SLA

| Severity | Response | Resolution |
|----------|----------|------------|
| P0 — Data loss / security | 1 hour | 4 hours |
| P1 — Tool broken | 4 hours | 24 hours |
| P2 — UX issue | 24 hours | 1 week |
| P3 — Enhancement | 1 week | Backlog |

---

## Admin Endpoints Reference

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/v1/beta-candidates` | Admin token | Scored waitlist for beta selection |
| `GET /api/v1/feedback` | Admin token | All feedback submissions |
| `GET /api/v1/waitlist` | Admin token | Full waitlist export |
| `GET /api/v1/usage` | Public | Tool usage counters |
| `GET /api/v1/metrics` | Public | Aggregate metrics + usage |
| `GET /api/v1/test-pdf` | Public | Download sample test PDF |
| `GET /api/v1/subscription?email=X` | Public | Subscription status lookup |
