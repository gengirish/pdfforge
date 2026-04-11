---
name: lemonsqueezy-payments
description: Integrate Lemon Squeezy as a payment provider and Merchant of Record. Use when the user asks to add payments, subscriptions, checkout, or monetization — especially from India where Stripe is difficult. Covers webhooks, checkout sessions, subscription management, and plan gating.
---

# Lemon Squeezy Payment Integration

Lemon Squeezy acts as Merchant of Record — handles tax compliance, invoicing, and global payouts. Ideal for indie hackers and startups in India.

## Architecture

```
User clicks Subscribe
  → Frontend POST /api/checkout { variant_id, email }
  → Backend creates checkout via Lemon Squeezy API
  → User redirected to hosted checkout page
  → User pays
  → Lemon Squeezy sends webhook to /api/v1/webhooks/lemonsqueezy
  → Backend upserts subscription in DB
  → Frontend checks /api/subscription?email=X
```

## Required Environment Variables

### Backend

| Variable | Description |
|----------|-------------|
| `LEMONSQUEEZY_API_KEY` | API key from Settings → API |
| `LEMONSQUEEZY_STORE_ID` | Store ID from Settings → Stores |
| `LEMONSQUEEZY_WEBHOOK_SECRET` | Signing secret from Settings → Webhooks |
| `LEMONSQUEEZY_PRO_VARIANT_ID` | Variant ID for Pro plan |
| `LEMONSQUEEZY_TEAM_VARIANT_ID` | Variant ID for Team plan |

### Frontend (Next.js)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_LS_PRO_VARIANT_ID` | Pro variant ID (inlined at build time) |
| `NEXT_PUBLIC_LS_TEAM_VARIANT_ID` | Team variant ID (inlined at build time) |

## Webhook Endpoint (Python/Flask)

```python
@app.post("/api/v1/webhooks/lemonsqueezy")
def webhook():
    raw = request.get_data(as_text=False)
    sig = request.headers.get("X-Signature", "")
    expected = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return jsonify({"error": "Invalid signature"}), 401

    payload = json.loads(raw)
    event = request.headers.get("X-Event-Name", "")
    # Handle: subscription_created, subscription_updated,
    #         subscription_cancelled, subscription_expired
```

## Checkout Session (Python/Flask)

```python
@app.post("/api/v1/checkout")
def checkout():
    body = request.get_json()
    checkout_payload = {
        "data": {
            "type": "checkouts",
            "attributes": {"checkout_data": {"email": body["email"]}},
            "relationships": {
                "store": {"data": {"type": "stores", "id": STORE_ID}},
                "variant": {"data": {"type": "variants", "id": body["variant_id"]}},
            },
        }
    }
    # POST to https://api.lemonsqueezy.com/v1/checkouts
    # Return checkout URL from response
```

## Frontend Proxy (Next.js API Route)

Create `/app/api/checkout/route.js` to proxy checkout requests to backend — avoids exposing backend URL to browser.

## Subscription DB Schema

```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    customer_id TEXT,
    subscription_id TEXT,
    variant_id TEXT,
    plan TEXT DEFAULT 'free',        -- free/pro/team
    status TEXT DEFAULT 'active',    -- active/cancelled/expired/past_due
    current_period_end TEXT,
    created_at TEXT,
    updated_at TEXT
);
```

## Pricing UI Pattern

```jsx
const plans = [
  { name: "Free", price: "0", period: "forever", variantId: null, cta: "Current plan" },
  { name: "Pro", price: "9", period: "/mo", variantId: process.env.NEXT_PUBLIC_LS_PRO_VARIANT_ID, cta: "Start free trial" },
  { name: "Team", price: "29", period: "/mo", variantId: process.env.NEXT_PUBLIC_LS_TEAM_VARIANT_ID, cta: "Contact us" },
];
```

**Important**: Next.js inlines `NEXT_PUBLIC_*` vars at build time. Dynamic access like `process.env[varName]` does NOT work in client components — always use direct references.

## Testing Without Credentials

Without Lemon Squeezy API keys, Subscribe buttons should gracefully fall back (e.g., scroll to waitlist). The webhook endpoint returns 401 if secret is unconfigured.

## Why Lemon Squeezy over Stripe

- **Merchant of Record**: Handles tax, compliance, invoicing globally
- **India-friendly**: No need for Indian business entity complications with Stripe
- **Simple API**: JSON:API format, hosted checkout, webhook-driven
- **Built-in affiliate system**: For growth
