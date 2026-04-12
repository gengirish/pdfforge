# PDFforge

PDFforge is a local-first PDF toolkit for fast everyday document ops.
It is built for solo founders, operators, students, and teams who need practical PDF workflows without sending files to cloud services.

## Why this is product-ready

- Privacy-first: runs fully on localhost (or your own host)
- Fast utility surface: the six most common PDF actions in one place, plus automation APIs
- Beginner-friendly UX: one-page dashboard with guided actions
- Safer defaults: upload validation, size limits, and clear error messages
- Versioned REST API under `/api/v1/*` with OpenAPI, Swagger UI, and ReDoc
- Live traction-style metrics endpoint at `/api/v1/metrics`

## Current features

### Dashboard (browser)

- Merge multiple PDFs into one
- Split by page ranges (download as ZIP)
- Rotate all pages or selected pages (90° / 180° / 270°)
- Extract machine-readable text to `.txt`
- Encrypt with a password
- Decrypt password-protected PDFs

### REST API — core tools

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/merge` | Combine PDFs (`files` field, multipart) |
| `POST /api/v1/split` | Page ranges → ZIP of PDFs (`file`, `ranges`) |
| `POST /api/v1/rotate` | Rotate pages (`file`, `angle`, optional `pages`) |
| `POST /api/v1/extract_text` | Text export (`file`) |
| `POST /api/v1/encrypt` | Password-protect (`file`, `password`) |
| `POST /api/v1/decrypt` | Remove password (`file`, `password`) |

By default, responses are JSON job envelopes with a download URL. Append `?download=true` to stream the raw file (legacy behavior). Authenticated routes expect an API key when enforcement is enabled (see deployment config).

### REST API — automation

- **`POST /api/v1/pipeline`** — Chain multiple operations in one request (JSON body with `steps` and base64 `files`).
- **`POST /api/v1/batch`** — Run the same tool on many PDFs in parallel (JSON).
- **Async jobs** — On core tool routes, send `X-Async: true` or `?async=true` for a `202` with `job_id` and `poll_url`; poll **`GET /api/v1/jobs/<id>`** until complete. Optional `webhook_url` and `webhook_secret` form fields for completion callbacks.
- **`GET /api/v1/capabilities`** — Machine-readable manifest (tools, limits, feature flags, agent hints).
- **`GET /api/v1/openapi.json`** — OpenAPI 3 specification.
- **`GET /api/v1/docs`** — Swagger UI.
- **`GET /api/v1/redoc`** — ReDoc.
- **`GET /.well-known/ai-plugin.json`** — AI plugin manifest for agent discovery.
- **`POST /api/v1/agent/interpret`** *(optional)* — Natural language → pipeline plan via Anthropic; set `ANTHROPIC_API_KEY` on the server. Can execute the plan when `execute` and `files` are provided.

### Product & ops

- Legacy **`GET /health`** and versioned **`GET /api/v1/health`**
- **`GET /api/v1/tools`** — Short list of core tool routes
- **`GET /api/v1/metrics`** — Waitlist summary, upload limit, tool usage counters
- **`GET /api/v1/usage`** — Tool usage counters
- **`GET /api/v1/test-pdf`** — Sample PDF for testing
- Public **waitlist** capture (HTML form + JSON API) and **admin** waitlist view (SQLite or Postgres)
- **`POST /api/v1/feedback`** — Beta feedback (optional admin **`GET /api/v1/feedback`**)
- Landing **pricing** section and Lemon Squeezy checkout hooks (see `docs/payments-setup.md`)

### Clients & integrations

- **Python SDK** — `sdk/python/` (async jobs, pipeline, batch); published as `pdfforge-sdk`.
- **MCP server** — `mcp/` exposes tools to Claude Desktop and other MCP hosts (`run_pipeline`, `batch_process`, etc.). See `mcp/README.md`.

## Tech stack

- Flask
- pypdf
- pdfplumber
- Next.js 14 (frontend in `frontend/`)

## Local setup

1. Open a terminal in the project root (the directory that contains `app.py`).

2. Create and activate a virtual environment:

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

   - App: `http://127.0.0.1:5050`
   - Health: `http://127.0.0.1:5050/health`
   - API health: `http://127.0.0.1:5050/api/v1/health`
   - API tools index: `http://127.0.0.1:5050/api/v1/tools`
   - Capabilities: `http://127.0.0.1:5050/api/v1/capabilities`
   - OpenAPI: `http://127.0.0.1:5050/api/v1/openapi.json`
   - Swagger UI: `http://127.0.0.1:5050/api/v1/docs`
   - Metrics: `http://127.0.0.1:5050/api/v1/metrics`
   - Waitlist admin: `http://127.0.0.1:5050/admin/waitlist`

## Next.js frontend

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

## Waitlist endpoints

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

## Product next steps (roadmap)

- OCR for scanned PDFs
- Drag-and-drop + progress UX
- E-sign and simple form-fill
- Team workspace + audit logs
- Usage-based billing + hosted mode
- Playwright E2E tests and CI pipeline

## CI/CD

- CI workflow: `.github/workflows/ci.yml`
- CD workflow: `.github/workflows/cd.yml`
- Strategy and required secrets: `docs/ci-cd-strategy.md`

## Further documentation

- `docs/beta-runbook.md` — Beta rollout and admin endpoints
- `docs/payments-setup.md` — Lemon Squeezy
- `docs/ci-cd-strategy.md` — GitHub Actions and secrets

## Notes

- This app does not upload files to a cloud service by default when self-hosted.
- OCR is not included yet, so scanned text extraction may be limited.
