# PDFforge v2: PDF tools that finally scale with your automation stack

*Merge, split, rotate, extract, encrypt, and decrypt in the browser—plus pipelines, batch jobs, async processing, webhooks, and OpenAPI-backed docs. Self-host or use hosted; your files stay yours.*

**Medium topics (add when publishing — up to 5):**

1. Developer Tools  
2. API  
3. Open Source  
4. Software Development  
5. Automation  

---

Most PDF utilities stop at the upload button. That is fine until you need to merge twelve files, encrypt the result, and run the same workflow every night without babysitting curl. **PDFforge v2** is our answer: the same six core tools in a simple dashboard, with a proper **developer layer** underneath—versioned REST APIs, multi-step pipelines, bulk batch runs, async jobs, optional webhooks, and first-class documentation you can actually hand to another engineer.

This post walks through what shipped, who it is for, and where to try it.

## Why we built a v2

Teams rarely need “one more merge UI.” They need **composability**: chain steps without six round trips, apply one operation to many files, and avoid blocking a web worker for sixty seconds while a large PDF processes. They also need **clarity**—OpenAPI, Swagger, ReDoc—so automation is not tribal knowledge.

PDFforge started as a local-first toolkit: privacy-minded, fast, honest about limits. v2 keeps that contract for the browser experience and adds an API surface that matches how real pipelines are built.

## What is new

### Pipeline and batch

- **Pipeline** (`POST /api/v1/pipeline`) runs multiple PDF steps in order in a single request. Think merge, then encrypt—without scripting intermediate downloads between calls.
- **Batch** (`POST /api/v1/batch`) applies the same tool to many PDFs in one shot, with a consistent response shape for your orchestration layer.

### Async jobs and webhooks

Core tool routes support **async mode** (`X-Async: true` or `?async=true`): you get a `202` with a job id and poll URL instead of holding the connection open. For integrations that prefer push over poll, you can pass optional **webhook** parameters so your system gets notified when work completes.

### Documentation and discovery

Shipping an API without docs is not shipping. v2 includes:

- **OpenAPI 3** at `/api/v1/openapi.json`
- **Swagger UI** at `/api/v1/docs`
- **ReDoc** at `/api/v1/redoc`
- A **capabilities** endpoint (`GET /api/v1/capabilities`) with limits, tools, and hints for agents
- An **AI plugin manifest** at `/.well-known/ai-plugin.json` for tools that discover integrations programmatically

### Optional AI-assisted planning

If you run Anthropic on the server (`ANTHROPIC_API_KEY`), **`POST /api/v1/agent/interpret`** can turn a plain-English intent into a structured pipeline plan—and optionally execute it when you provide files. It is optional by design; the REST tools stand on their own.

### Clients: Python SDK and MCP

- **Python SDK** (`pdfforge-sdk`) covers merge through batch and async helpers so you are not hand-rolling multipart forms in every script.
- **MCP server** exposes the same operations—including pipeline and batch—to Claude Desktop and other MCP-compatible hosts, which matters if your “user” is an agent, not only a human.

### Product polish

The marketing site now includes a **Developers** section that points to the automation surface and live doc links. We also aligned **CORS** so a production frontend and API on different origins can work together without browser surprises.

## Who this is for

**Backend and platform engineers** — Pipeline, batch, and async match how you already think about file jobs: idempotent steps, polling or callbacks, observable failures.

**Security- and compliance-minded teams** — Self-hosting is still first-class. v2 adds automation; it does not force a new document cloud.

**AI and automation builders** — MCP, optional natural-language planning, and a capabilities manifest are there so agents and scripts can discover what the server can do without reading the source.

**Indie hackers and students** — The open self-host story and the six dashboard tools are unchanged. The API is additive when you are ready.

## Try it

- **Product:** [https://pdfforge.intelliforge.tech](https://pdfforge.intelliforge.tech)
- **Interactive API (Swagger):** [https://pdfforge-api.fly.dev/api/v1/docs](https://pdfforge-api.fly.dev/api/v1/docs)
- **ReDoc:** [https://pdfforge-api.fly.dev/api/v1/redoc](https://pdfforge-api.fly.dev/api/v1/redoc)
- **OpenAPI JSON:** [https://pdfforge-api.fly.dev/api/v1/openapi.json](https://pdfforge-api.fly.dev/api/v1/openapi.json)
- **Source:** [https://github.com/gengirish/pdfforge](https://github.com/gengirish/pdfforge)

If you are evaluating for production, start with Swagger “Try it out” on a test PDF, then wire the same calls from your runner or SDK.

## Closing

v2 is about meeting builders where they are: same honest PDF tools in the UI, and an API layer that does not apologize for being real software—pipelines, batch, async, webhooks, and docs included.

We are **IntelliForge AI**. PDFforge is our open, privacy-conscious PDF toolkit; v2 is the chapter where automation stops being an afterthought.

---

## Pasting into Medium (quick tips)

1. **Title and subtitle:** Copy the H1 line into Medium’s title field. Copy the italic line under it into Medium’s **subtitle** field (kicker), or paste as the first paragraph and set style to *subtitle* if you prefer.
2. **Headings:** `##` becomes a section title; avoid more than one top-level `#` in the body after import.
3. **Tables:** Medium’s editor does not love Markdown tables; this article uses lists instead.
4. **Code:** Inline endpoints like `` `/api/v1/pipeline` `` paste fine; use Medium’s code block (` ``` `) for multi-line examples if you add them later.
5. **Links:** Keep full `https://` URLs; Medium will unfurl some domains—still worth keeping explicit links for the API and GitHub.
6. **Topics:** In **Story settings → Change topics**, add up to **five** from the list at the top of this file (Medium matches existing topic names as you type).
7. **Cover image:** Medium rewards a strong hero image; consider a simple visual (documents + terminal or workflow arrows)—you can add it in Medium’s story settings.

*For internal distribution, a wider launch kit (social snippets, email subjects) lives in `docs/v2-feature-launch-post.md`.*
