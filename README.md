# PDFforge

PDFforge is a local-first PDF toolkit for fast everyday document ops.
It is built for solo founders, operators, students, and teams who need practical PDF workflows without sending files to cloud services.

## Why this is product-ready

- Privacy-first: runs fully on localhost
- Fast utility surface: the 6 most common PDF actions in one place
- Beginner-friendly UX: one-page dashboard with guided actions
- Safer defaults: upload validation, size limits, and clear error messages
- Versioned API readiness: includes `/api/v1/health` and `/api/v1/tools`
- Live traction-style metrics endpoint at `/api/v1/metrics`

## Current Features

- Merge multiple PDFs into one
- Split by page ranges (download as ZIP)
- Rotate all pages or selected pages
- Extract text to `.txt`
- Encrypt PDF with password
- Decrypt password-protected PDF
- Health endpoint at `/health`
- Versioned API endpoints at `/api/v1/*`
- Public metrics endpoint for waitlist + product telemetry (`/api/v1/metrics`)
- Product-style pricing section for future hosted plans
- Public waitlist capture (form + API)
- Admin waitlist view backed by SQLite persistence

## Tech Stack

- Flask
- pypdf
- pdfplumber
- Next.js 14 (frontend in `frontend/`)

## Local Setup

1. Open terminal in this folder:

   ```bash
   cd pdfforge
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   python app.py
   ```

5. Open:

   - `http://127.0.0.1:5050`
   - Health check: `http://127.0.0.1:5050/health`
   - API health: `http://127.0.0.1:5050/api/v1/health`
   - API tools: `http://127.0.0.1:5050/api/v1/tools`
   - API metrics: `http://127.0.0.1:5050/api/v1/metrics`
   - Waitlist admin: `http://127.0.0.1:5050/admin/waitlist`

## Next.js Frontend

1. In a new terminal:

   ```bash
   cd frontend
   npm install
   cp .env.local.example .env.local
   npm run dev
   ```

2. Open:

   - `http://127.0.0.1:3000`

The frontend uses:

- `NEXT_PUBLIC_BACKEND_URL` for browser form actions
- `BACKEND_API_URL` for server-side route handlers (`/api/health`, `/api/waitlist`)

## Run with Docker

```bash
docker compose up --build
```

Then open:

- `http://localhost:5050`
- `http://localhost:5050/api/v1/health`

You can configure max upload size via `.env`:

```bash
cp .env.example .env
# edit MAX_CONTENT_LENGTH_MB / WAITLIST_DB_PATH / WAITLIST_DATABASE_URL / WAITLIST_ADMIN_TOKEN
```

Use one waitlist database mode:

- **SQLite (default):** set `WAITLIST_DB_PATH`
- **Postgres (recommended for production):** set `WAITLIST_DATABASE_URL`

Example:

```bash
WAITLIST_DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

## Waitlist Endpoints

- `POST /waitlist` (form submit from landing page)
- `POST /api/v1/waitlist` (JSON API)
- `GET /admin/waitlist` (HTML admin table)
- `GET /api/v1/waitlist` (JSON list, admin access)

Example API request:

```bash
curl -X POST http://127.0.0.1:5050/api/v1/waitlist \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"founder@example.com\",\"name\":\"Ava\",\"plan_interest\":\"pro\",\"use_case\":\"Invoice + contract workflows\"}"
```

If `WAITLIST_ADMIN_TOKEN` is set, pass it as:

- query param: `/admin/waitlist?token=YOUR_TOKEN`
- or header: `X-Admin-Token: YOUR_TOKEN`

## Product Next Steps (YC-style roadmap)

- OCR for scanned PDFs
- Drag-and-drop + progress UX
- E-sign and simple form-fill
- Team workspace + audit logs
- Usage-based billing + hosted mode
- Stripe checkout + customer portal
- Playwright E2E tests and CI pipeline

## CI/CD

- CI workflow: `.github/workflows/ci.yml`
- CD workflow: `.github/workflows/cd.yml`
- Strategy and required secrets: `docs/ci-cd-strategy.md`

## Notes

- This app does not upload files to a cloud service.
- OCR is not included yet, so scanned text extraction may be limited.
