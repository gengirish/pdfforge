# PDFforge v2 — Feature launch kit

Use this doc for your blog, newsletter, changelog, and social posts. Tone: direct, builder-friendly, privacy-conscious.

---

## Hero (owned: blog / landing / email)

**Headline:** PDFforge v2: PDF tools that finally scale with your automation stack

**Subhead:** The same merge, split, rotate, extract, encrypt, and decrypt workflows you run in the browser—now with pipelines, batch jobs, async processing, webhooks, and first-class API docs. Self-host or use our hosted stack; your documents stay yours.

**Primary CTA:** Try the toolkit → [https://pdfforge.intelliforge.tech](https://pdfforge.intelliforge.tech)

**Secondary CTA:** Open the API docs → `https://pdfforge-api.fly.dev/api/v1/docs` (Swagger) · `…/api/v1/redoc` (ReDoc)

---

## The story (why v2)

Teams outgrew “one PDF at a time.” They needed to chain steps (merge then encrypt), run the same operation across dozens of files, and not block HTTP workers on long jobs. PDFforge v2 adds a **developer layer** on top of the dashboard: versioned REST endpoints under `/api/v1/*`, a **pipeline** endpoint for multi-step workflows, **batch** for parallel same-tool runs, **async jobs** with polling and optional **webhooks**, plus **OpenAPI**, **capabilities discovery**, and integrations (**Python SDK**, **MCP** for AI assistants). The UI still prioritizes privacy and clarity; the API prioritizes composability.

---

## What shipped in v2

### Automation API

- **Pipeline** — `POST /api/v1/pipeline`: chain tools in one request instead of scripting six round trips.
- **Batch** — `POST /api/v1/batch`: one operation, many PDFs, one response shape.
- **Async + webhooks** — `X-Async: true` or `?async=true` on core tool routes; poll `GET /api/v1/jobs/<id>`; optional `webhook_url` / `webhook_secret` for completion callbacks.
- **Capabilities** — `GET /api/v1/capabilities`: machine-readable limits, tools, and agent hints.

### Documentation & discovery

- **OpenAPI 3** — `GET /api/v1/openapi.json`
- **Swagger UI** — `GET /api/v1/docs`
- **ReDoc** — `GET /api/v1/redoc`
- **AI plugin manifest** — `GET /.well-known/ai-plugin.json` for agent discovery

### Optional AI planner

- **`POST /api/v1/agent/interpret`** — Turn natural language into a pipeline plan (Anthropic); can execute when `ANTHROPIC_API_KEY` is set on the server.

### Clients

- **Python SDK** (`pdfforge-sdk`) — merge through batch and async helpers.
- **MCP server** — expose merge/split/rotate/extract/encrypt/decrypt, `run_pipeline`, and `batch_process` to Claude Desktop and other MCP hosts.

### Product surface

- Landing **Developers** section documenting the automation surface and links to docs.
- **CORS** updated for production frontend origins so browser tools call the API safely across deploys.

---

## Who it’s for

| Audience | Message |
|----------|---------|
| Backend engineers | Pipeline + batch + async match how you already build file pipelines. |
| Security / compliance | Self-hosted path unchanged; automation doesn’t require a new vendor for document processing. |
| AI / automation builders | MCP + optional agent interpret + capabilities endpoint fit agentic workflows. |
| Indie hackers & students | Free self-host tier; six core tools unchanged; API is additive. |

---

## Rented channels — short copy blocks

### LinkedIn (single post, ~1,300 chars)

We just shipped **PDFforge v2**.

If you’ve ever glued together five curl calls to merge PDFs, encrypt them, and pray nothing times out—this release is for you.

What’s new:

- **Pipeline API** — chain steps in one HTTP call  
- **Batch API** — same operation, many files  
- **Async jobs** + optional **webhooks**  
- **OpenAPI + Swagger + ReDoc** shipped with the server  
- **Python SDK** + **MCP** for Claude / agent workflows  

The dashboard still does merge, split, rotate, extract text, encrypt, and decrypt with a privacy-first story. The API is for when you’re ready to automate.

Live: pdfforge.intelliforge.tech  
Built by IntelliForge AI.

### X / Twitter (thread starter + 3 bullets)

**Tweet 1:** PDFforge v2 is live: pipeline + batch + async PDF APIs, OpenAPI/Swagger/ReDoc, Python SDK & MCP—not just merge/split in the UI.

**Tweet 2:** Self-host friendly. Chain merge→encrypt in one request. Webhooks when jobs finish. Capabilities endpoint for agents.

**Tweet 3:** Try it: [pdfforge.intelliforge.tech](https://pdfforge.intelliforge.tech) · API docs on the hosted API under `/api/v1/docs`

### Email subject lines (A/B ideas)

- PDFforge v2: pipelines, batch jobs, and webhooks  
- Your PDF stack just grew an API (OpenAPI included)  
- Merge/split in the UI; automate everything else via v2  

---

## Changelog (release notes style)

- Add `POST /api/v1/pipeline` for multi-step PDF workflows.  
- Add `POST /api/v1/batch` for bulk same-tool processing.  
- Add async job flow (`202` + poll URLs) and optional webhooks on core tool routes.  
- Publish OpenAPI spec, Swagger UI, ReDoc, and `/api/v1/capabilities`.  
- Add optional `POST /api/v1/agent/interpret` (Anthropic) for NL → pipeline plans.  
- Ship Python SDK (`pdfforge-sdk`) and MCP package for AI toolchains.  
- Document automation on the marketing site (Developers section).  
- Align CORS for production frontend ↔ API deployments.  

---

## Launch checklist (quick)

- [ ] Publish this story on your **owned** blog or changelog.  
- [ ] Send to **email** list with one clear CTA (try tools or open Swagger).  
- [ ] Post **LinkedIn** + one **X** thread; reply to comments with GitHub link.  
- [ ] Pin **docs** link in GitHub README (already linked from repo).  
- [ ] Optional: short **demo video** (2 min): dashboard tool → same flow in Swagger `Try it out`.  

---

## Links reference

| Resource | URL |
|----------|-----|
| Product | https://pdfforge.intelliforge.tech |
| API (Swagger) | https://pdfforge-api.fly.dev/api/v1/docs |
| OpenAPI JSON | https://pdfforge-api.fly.dev/api/v1/openapi.json |
| Capabilities | https://pdfforge-api.fly.dev/api/v1/capabilities |
| GitHub | https://github.com/gengirish/pdfforge |

---

*IntelliForge AI · PDFforge — local-first PDF tooling with an automation API when you need it.*
