---
name: beta-testing-infra
description: Build beta testing infrastructure for SaaS products. Use when the user asks to prepare for beta launch, add feedback collection, score waitlist candidates, track usage analytics, or create test resources for beta testers.
---

# Beta Testing Infrastructure

End-to-end system for running a structured beta program — from candidate selection to feedback collection to usage tracking.

## Components

### 1. Usage Tracking (In-Memory Counters)

Thread-safe counters for every tool/feature:

```python
import threading
from collections import Counter

_usage_lock = threading.Lock()
_usage_counts: Counter[str] = Counter()

def record_tool_usage(tool_id: str) -> None:
    with _usage_lock:
        _usage_counts[tool_id] += 1

def get_usage_counts() -> dict[str, int]:
    with _usage_lock:
        return dict(_usage_counts)
```

Call `record_tool_usage("merge")` at the top of each route handler. Expose via `/api/v1/usage` and include in `/api/v1/metrics`.

### 2. Feedback API

DB table:

```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY,
    email TEXT DEFAULT '',
    rating INTEGER DEFAULT 0,    -- 1-5
    message TEXT DEFAULT '',
    page TEXT DEFAULT '',
    source_ip TEXT DEFAULT '',
    created_at TEXT
);
```

Endpoints:
- `POST /api/v1/feedback` — public, accepts `{ email, rating, message, page }`
- `GET /api/v1/feedback` — admin-only, returns all feedback

### 3. Beta Candidate Scoring

Score waitlist signups by urgency signals:

```python
def beta_candidates(limit=50):
    signups = read_waitlist_signups(limit=1000)
    scored = []
    for s in signups:
        score = 0
        if plan == "team": score += 3
        elif plan == "pro": score += 2
        if "this-week" in use_case: score += 3
        if high_volume_keywords: score += 2
        if len(use_case) > 60: score += 1
        scored.append({**s, "beta_score": score})
    return sorted(scored, key=lambda x: x["beta_score"], reverse=True)[:limit]
```

Expose via `GET /api/v1/beta-candidates` (admin-only).

### 4. Test PDF Generator

Generate a sample multi-page PDF for testers using reportlab:

```python
@app.get("/api/v1/test-pdf")
def test_pdf():
    # Generate 5-page PDF with realistic content
    # Return as downloadable file
```

### 5. Frontend Feedback Widget

Add a feedback section with:
- Email (optional)
- Rating dropdown (1-5)
- Message textarea (required)
- Success/error states

### 6. Admin Endpoints Summary

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /api/v1/beta-candidates` | Admin | Scored waitlist for selection |
| `GET /api/v1/feedback` | Admin | All feedback submissions |
| `GET /api/v1/waitlist` | Admin | Full waitlist export |
| `GET /api/v1/usage` | Public | Tool usage counters |
| `GET /api/v1/metrics` | Public | Aggregate metrics |
| `GET /api/v1/test-pdf` | Public | Sample PDF for testers |

## Beta Phases

1. **Closed Alpha** (5-10 users): Hand-pick from `/api/v1/beta-candidates`, gather qualitative feedback
2. **Expanded Beta** (25-50 users): Open to all Pro waitlist signups, enable payments
3. **Open Beta**: Remove invite gate, launch publicly, measure conversion

## Bug Triage SLA

| Severity | Response | Resolution |
|----------|----------|------------|
| P0 — Data loss | 1 hour | 4 hours |
| P1 — Tool broken | 4 hours | 24 hours |
| P2 — UX issue | 24 hours | 1 week |
| P3 — Enhancement | 1 week | Backlog |
