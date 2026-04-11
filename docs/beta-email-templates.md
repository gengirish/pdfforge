# PDFforge Beta Email Templates

## 1. Alpha Invite

**Subject:** You're in — PDFforge alpha access

```
Hi {{name}},

You signed up for PDFforge early access, and we picked you for our closed alpha.

What you get:
- All 6 PDF tools (merge, split, rotate, extract text, encrypt, decrypt)
- Direct line to the founding team for support
- Your feedback shapes the roadmap

Get started:
1. Open https://hire-with-giri.vercel.app
2. Download our test PDF to try every tool: https://pdfforge-api.fly.dev/api/v1/test-pdf
3. After testing, scroll to "Beta Feedback" and share your experience

We read every submission. If something breaks, tell us — we'll fix it within hours.

— The PDFforge Team
```

---

## 2. Beta Expansion Invite

**Subject:** PDFforge beta is live — you're invited

```
Hi {{name}},

PDFforge is now in expanded beta, and your waitlist spot is confirmed.

What's new since alpha:
- Improved stability across all tools
- Usage analytics so you can track your team's PDF workflows
- Paid plans available (Pro $9/mo, Team $29/mo) for hosted access

Try it now: https://hire-with-giri.vercel.app

Your use case ("{{use_case_snippet}}") is exactly what we're optimizing for.
We'd love your feedback — there's a form right on the page.

Questions? Reply to this email directly.

— The PDFforge Team
```

---

## 3. Open Beta Announcement

**Subject:** PDFforge is open — free PDF tools for every team

```
Hi {{name}},

PDFforge is now open to everyone. No invite needed.

What you can do today:
- Merge, split, rotate, extract, encrypt, decrypt — all locally
- No file uploads to third-party clouds
- API access for automation at /api/v1/*

Pricing:
- Free: All tools, localhost, no account needed
- Pro ($9/mo): Hosted instance, 100MB uploads, API key
- Team ($29/mo): Multi-user, audit logs, admin controls

Start here: https://hire-with-giri.vercel.app

Share with your team — every signup helps us build better tools.

— The PDFforge Team
```

---

## 4. Feedback Follow-up

**Subject:** Thanks for your PDFforge feedback

```
Hi {{name}},

We saw your feedback (rating: {{rating}}/5):
"{{message_snippet}}"

{{#if rating >= 4}}
Glad it's working for you! If you have teammates who deal with PDFs,
we'd appreciate you sharing PDFforge with them.
{{else}}
We take this seriously. Here's what we're doing about it:
- {{action_item}}

We'll follow up when it's fixed. Thanks for helping us improve.
{{/if}}

— The PDFforge Team
```

---

## 5. Churn Prevention (Cancelled Subscription)

**Subject:** We'll miss you — quick question?

```
Hi {{name}},

We noticed you cancelled your PDFforge subscription. No hard feelings.

Would you mind telling us why? (One-line reply is fine.)

Common reasons we hear:
- Not using it enough → We can help you automate workflows
- Missing a feature → Tell us and we'll prioritize it
- Too expensive → Let's talk about a custom plan

Either way, your free tools access continues. We hope to win you back.

— The PDFforge Team
```
