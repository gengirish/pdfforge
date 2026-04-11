---
name: deploy-vercel
description: Deploy Next.js applications to Vercel using the Vercel CLI. Use when the user asks to deploy, ship, push to production, or publish a frontend app to Vercel. Also covers rollback, environment variables, and domain management.
---

# Deploy to Vercel via CLI

## Prerequisites

- **Vercel CLI**: Install globally with `npm install -g vercel`
- **Authentication**: Run `vercel login` if not already authenticated
- Ensure the project has a valid `package.json` with `build` and `start` scripts

## Deploy Commands

### First-time deploy (links project)

```bash
vercel --yes --prod
```

The `--yes` flag auto-confirms project settings detection (framework, build command, output directory). On first run this creates a `.vercel/` directory with project linking metadata.

### Subsequent deploys

```bash
vercel --prod
```

### Preview deploy (non-production)

```bash
vercel
```

Returns a unique preview URL for testing before promoting to production.

### Promote a preview to production

```bash
vercel promote <deployment-url>
```

## Environment Variables

### Set secrets via CLI

```bash
vercel env add VARIABLE_NAME production
vercel env add VARIABLE_NAME preview
vercel env add VARIABLE_NAME development
```

### Pull env vars to local `.env.local`

```bash
vercel env pull .env.local
```

### List all env vars

```bash
vercel env ls
```

## Domain Management

### Add custom domain

```bash
vercel domains add yourdomain.com
```

### Add subdomain

Add a CNAME record at your DNS provider:

```
CNAME   subdomain   →   cname.vercel-dns.com
```

Then add the domain in Vercel:

```bash
vercel domains add subdomain.yourdomain.com
```

### List domains

```bash
vercel domains ls
```

## Rollback

```bash
vercel rollback
```

Or target a specific deployment:

```bash
vercel rollback <deployment-url>
```

## Inspect & Logs

```bash
vercel inspect <deployment-url> --logs
```

## Next.js Considerations

- Vercel auto-detects Next.js and applies optimal settings — no `output: "standalone"` needed
- Static pages are served from the edge CDN; server-rendered routes run as serverless functions
- The `images.unoptimized` config can be removed if using Vercel's built-in image optimization
- `.vercel/` directory should be in `.gitignore`
- For framework detection issues, add `{"framework": "nextjs"}` to `vercel.json`

## Post-Deploy Verification

After deploying, run E2E tests against the live URL:

```bash
BASE_URL=https://your-app.vercel.app npx playwright test
```

The Playwright config should conditionally skip the local dev server when `BASE_URL` is set:

```javascript
webServer: process.env.BASE_URL
  ? undefined
  : { command: "npm run dev", url: "http://localhost:3000", reuseExistingServer: true }
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `vercel: command not found` | `npm install -g vercel` |
| Auth errors | `vercel login` or `vercel logout && vercel login` |
| Build fails on Vercel but works locally | Check Node.js version parity; set `engines` in `package.json` |
| Functions timeout | Increase `maxDuration` in route config or optimize the handler |
| Missing env vars at runtime | Verify vars are set for the correct environment (`production` / `preview`) |
| `No Output Directory named "public" found` | Add `vercel.json` with `{"framework": "nextjs"}` |
| 403 on domain add | Domain is on another Vercel team; verify ownership or add from that account |
