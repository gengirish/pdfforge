# PDFforge CI/CD Strategy

This strategy separates validation (`CI`) from release (`CD`) so production deploys are gated by fast feedback.

## Pipeline overview

1. **CI (`.github/workflows/ci.yml`)**
   - Runs on pull requests and non-`main` pushes.
   - Validates backend compile + health smoke check.
   - Builds frontend.
   - Runs Playwright local integration tests against:
     - local backend (`http://127.0.0.1:5050`)
     - local Next.js app started by Playwright config.

2. **CD (`.github/workflows/cd.yml`)**
   - Runs on `main` pushes and manual dispatch.
   - Deploys backend to Fly.io.
   - Deploys frontend to Vercel production with explicit backend URL injection.

## Required GitHub secrets

Add these repository secrets before enabling CD:

- `FLY_API_TOKEN`: Fly.io API token with deploy permissions.
- `FLY_APP_NAME`: Backend app name to deploy (for example, `pdfescape-lite-api` now, `pdfforge-api` after migration).
- `VERCEL_TOKEN`: Vercel token with project deploy access.
- `VERCEL_ORG_ID`: Vercel team/org ID.
- `VERCEL_PROJECT_ID`: Vercel project ID for the frontend project.
- `BACKEND_BASE_URL`: Public backend URL used by frontend at runtime (for example, `https://pdfescape-lite-api.fly.dev`).

## Branching and release policy

- Open PRs into `main` for all changes.
- Require CI to pass before merge.
- Merge to `main` triggers CD.
- Use `workflow_dispatch` for controlled redeploys/rollbacks without code changes.

## Optional hardening (recommended)

- Add GitHub protected environment rules for `production` requiring manual approval.
- Add required checks: `backend-checks`, `frontend-build`, `e2e-local`.
- Add Slack/email notifications for failed CD runs.
- Add post-deploy E2E against production URL as a follow-up job in `cd.yml`.
