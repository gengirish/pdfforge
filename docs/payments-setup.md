# PDFforge Payments — Lemon Squeezy Setup

PDFforge uses [Lemon Squeezy](https://lemonsqueezy.com) as the payment provider. Lemon Squeezy acts as Merchant of Record, handling tax compliance and payouts globally.

## Prerequisites

1. Create a Lemon Squeezy account at https://lemonsqueezy.com
2. Create a Store
3. Create two Products with recurring variants:
   - **Pro** — $9/month
   - **Team** — $29/month
4. Note down the **Variant IDs** from each product's variant page

## Required Environment Variables

### Backend (Fly.io / app.py)

| Variable | Description |
|----------|-------------|
| `LEMONSQUEEZY_API_KEY` | API key from Settings → API |
| `LEMONSQUEEZY_STORE_ID` | Store ID from Settings → Stores |
| `LEMONSQUEEZY_WEBHOOK_SECRET` | Signing secret from Settings → Webhooks |
| `LEMONSQUEEZY_PRO_VARIANT_ID` | Variant ID for the Pro plan |
| `LEMONSQUEEZY_TEAM_VARIANT_ID` | Variant ID for the Team plan |

### Frontend (Vercel)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_LS_PRO_VARIANT_ID` | Same Pro variant ID (exposed to browser for checkout) |
| `NEXT_PUBLIC_LS_TEAM_VARIANT_ID` | Same Team variant ID |

## Webhook Configuration

1. In Lemon Squeezy dashboard → Settings → Webhooks
2. Create a webhook pointing to: `https://pdfforge-api.fly.dev/api/v1/webhooks/lemonsqueezy`
3. Set a signing secret and save it as `LEMONSQUEEZY_WEBHOOK_SECRET`
4. Subscribe to these events:
   - `subscription_created`
   - `subscription_updated`
   - `subscription_cancelled`
   - `subscription_expired`

## How It Works

```
User clicks "Subscribe" on pricing card
  → Frontend POST /api/checkout with variant_id
  → Backend creates checkout session via Lemon Squeezy API
  → User redirected to Lemon Squeezy hosted checkout page
  → User pays
  → Lemon Squeezy sends webhook to /api/v1/webhooks/lemonsqueezy
  → Backend stores subscription in DB
  → Frontend can check /api/subscription?email=... to verify status
```

## Setting Env Vars

### Fly.io (backend)

```bash
flyctl secrets set \
  LEMONSQUEEZY_API_KEY="ls_..." \
  LEMONSQUEEZY_STORE_ID="12345" \
  LEMONSQUEEZY_WEBHOOK_SECRET="whsec_..." \
  LEMONSQUEEZY_PRO_VARIANT_ID="67890" \
  LEMONSQUEEZY_TEAM_VARIANT_ID="67891" \
  --app pdfforge-api
```

### Vercel (frontend)

```bash
cd frontend
echo "67890" | vercel env add NEXT_PUBLIC_LS_PRO_VARIANT_ID production
echo "67891" | vercel env add NEXT_PUBLIC_LS_TEAM_VARIANT_ID production
```

## Testing

Without Lemon Squeezy credentials, the Subscribe buttons gracefully fall back to the waitlist section. Once credentials are set, clicking Subscribe redirects to the Lemon Squeezy checkout.

## Database

The `subscriptions` table is auto-created on app startup alongside the existing `waitlist_signups` table. Schema:

- `email` (unique)
- `customer_id`, `subscription_id`, `variant_id`
- `plan` (free/pro/team)
- `status` (active/cancelled/expired/past_due/paused)
- `current_period_end`
- `created_at`, `updated_at`
