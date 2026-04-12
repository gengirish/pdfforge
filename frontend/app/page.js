"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:5050";

const tools = [
  { id: "merge", icon: "M", title: "Merge", desc: "Combine multiple PDFs into a single file.", action: "/merge" },
  { id: "split", icon: "S", title: "Split", desc: "Extract page ranges into separate PDFs.", action: "/split" },
  { id: "rotate", icon: "R", title: "Rotate", desc: "Fix orientation for all or selected pages.", action: "/rotate" },
  { id: "extract", icon: "T", title: "Extract Text", desc: "Pull machine-readable text from every page.", action: "/extract-text" },
  { id: "encrypt", icon: "E", title: "Encrypt", desc: "Lock PDFs with password protection.", action: "/encrypt" },
  { id: "decrypt", icon: "D", title: "Decrypt", desc: "Remove password from protected files.", action: "/decrypt" },
];

const useCases = [
  "Contracts and legal docs",
  "Invoices and accounting docs",
  "Hiring and candidate packets",
  "Ops runbooks and reports",
  "Client deliverables",
];

const testimonials = [
  {
    quote: "We replaced three SaaS tools with PDFforge. Our legal team processes 200+ contracts a week without files ever leaving our VPN.",
    name: "Priya K.",
    role: "Head of Ops, Series A fintech",
  },
  {
    quote: "The API let us automate our entire invoice pipeline in a weekend. No more manual PDF merging before month-close.",
    name: "Arjun M.",
    role: "Founding engineer, logistics startup",
  },
  {
    quote: "Privacy-first was the dealbreaker for us. Our compliance team approved PDFforge in two days — that never happens.",
    name: "Sarah L.",
    role: "VP Engineering, healthcare SaaS",
  },
];

const faqs = [
  { q: "Where are my files processed?", a: "Locally on your own infrastructure. Files never leave your machine unless you opt into the hosted plan." },
  { q: "Can I automate workflows via API?", a: "Yes. Six core tools live under /api/v1/*, plus pipeline (chain steps), batch (same op on many files), and async jobs with polling or optional webhooks. OpenAPI, Swagger UI, and ReDoc ship with the server." },
  { q: "What does the paid plan add?", a: "Hosted processing (no infra needed), larger file limits, API key management, team workspaces, and audit logs." },
  { q: "Is this open source?", a: "The core engine is MIT-licensed. Enterprise features (SSO, audit, compliance) are available on paid plans." },
];

const pricingPlans = [
  {
    name: "Open Source", price: "0", period: "forever",
    features: ["Six core PDF tools", "Pipeline & batch APIs", "Async jobs + optional webhooks", "OpenAPI + Swagger/ReDoc", "Self-host anywhere", "Community support"],
    cta: "You're on this plan", highlighted: false, variantId: null,
  },
  {
    name: "Pro", price: "9", period: "/mo",
    features: ["Hosted cloud instance", "100MB file uploads", "API key auth + rate limits", "Pipeline, batch, async & webhooks", "Priority email support", "Usage analytics dashboard"],
    cta: "Start free trial", highlighted: true, variantId: process.env.NEXT_PUBLIC_LS_PRO_VARIANT_ID || "",
  },
  {
    name: "Team", price: "29", period: "/mo",
    features: ["Everything in Pro", "5 team seats included", "Audit logs + compliance", "SSO / SAML (roadmap)", "Dedicated support channel"],
    cta: "Contact us", highlighted: false, variantId: process.env.NEXT_PUBLIC_LS_TEAM_VARIANT_ID || "",
  },
];

function buildUseCaseSummary(form) {
  const parts = [
    `Primary workflow: ${String(form.get("primary_use_case") || "General PDF workflows").trim()}`,
    `Team size: ${String(form.get("team_size") || "unknown").trim()}`,
    `Monthly volume: ${String(form.get("monthly_volume") || "unknown").trim()}`,
    `Timeline: ${String(form.get("timeline") || "not specified").trim()}`,
    `Notes: ${String(form.get("use_case") || "none").trim()}`,
  ];
  return parts.join(" | ").slice(0, 600);
}

function FileInput({ name, multiple, onChange, label }) {
  const inputRef = useRef(null);
  const [fileNames, setFileNames] = useState([]);

  function handleChange(e) {
    const files = Array.from(e.target.files || []);
    setFileNames(files.map((f) => f.name));
    if (onChange) onChange(e);
  }

  return (
    <div className="upload-zone" onClick={() => inputRef.current?.click()} role="button" tabIndex={0} aria-label={label}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
    >
      <input ref={inputRef} type="file" name={name} accept=".pdf,application/pdf"
        multiple={multiple} required onChange={handleChange} className="upload-zone-input" aria-label={label}
      />
      {fileNames.length > 0 ? (
        <span className="upload-zone-files">{fileNames.join(", ")}</span>
      ) : (
        <span className="upload-zone-placeholder">
          <span className="upload-zone-icon">+</span>
          {multiple ? "Drop PDFs here or click to browse" : "Drop a PDF here or click to browse"}
        </span>
      )}
    </div>
  );
}

export default function Page() {
  const [health, setHealth] = useState({ status: "checking" });
  const [metrics, setMetrics] = useState({ totalSignups: null, toolCount: tools.length, maxUploadMb: null });
  const [waitlistStatus, setWaitlistStatus] = useState("");
  const [waitlistError, setWaitlistError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [feedbackError, setFeedbackError] = useState("");
  const [isSendingFeedback, setIsSendingFeedback] = useState(false);
  const [toolStates, setToolStates] = useState({});
  const waitlistAction = useMemo(() => "/api/waitlist", []);

  useEffect(() => {
    let isMounted = true;
    Promise.allSettled([fetch("/api/health"), fetch("/api/metrics")]).then(
      async ([healthRes, metricsRes]) => {
        if (!isMounted) return;
        if (healthRes.status === "fulfilled") {
          try { setHealth(await healthRes.value.json()); } catch { setHealth({ status: "error" }); }
        } else { setHealth({ status: "error" }); }
        if (metricsRes.status === "fulfilled") {
          try {
            const m = (await metricsRes.value.json())?.metrics || {};
            setMetrics({
              totalSignups: typeof m.total_signups === "number" ? m.total_signups : null,
              toolCount: typeof m.tool_count === "number" ? m.tool_count : tools.length,
              maxUploadMb: typeof m.max_upload_mb === "number" ? m.max_upload_mb : null,
            });
          } catch { /* keep defaults */ }
        }
      }
    );
    return () => { isMounted = false; };
  }, []);

  const handleToolSubmit = useCallback(async (toolId, formEl) => {
    const tool = tools.find((t) => t.id === toolId);
    if (!tool) return;
    setToolStates((prev) => ({ ...prev, [toolId]: { status: "processing" } }));
    const formData = new FormData(formEl);
    try {
      const res = await fetch(`${backendBase}${tool.action}`, { method: "POST", body: formData });
      if (!res.ok) {
        const errText = await res.text();
        setToolStates((prev) => ({ ...prev, [toolId]: { status: "error", message: errText } }));
        return;
      }
      const blob = await res.blob();
      const disposition = res.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="?([^";\n]+)"?/);
      const fileName = match ? match[1] : `pdfforge-${toolId}-output`;
      const url = URL.createObjectURL(blob);
      setToolStates((prev) => ({ ...prev, [toolId]: { status: "done", downloadUrl: url, fileName } }));
    } catch {
      setToolStates((prev) => ({ ...prev, [toolId]: { status: "error", message: "Request failed. Is the backend running?" } }));
    }
  }, []);

  function onToolFormSubmit(toolId) {
    return (e) => {
      e.preventDefault();
      handleToolSubmit(toolId, e.currentTarget);
    };
  }

  function ToolResult({ toolId }) {
    const state = toolStates[toolId];
    if (!state) return null;
    if (state.status === "processing") return <div className="tool-result tool-result--processing"><span className="spinner" /> Processing...</div>;
    if (state.status === "error") return <div className="tool-result tool-result--error">{state.message || "Something went wrong."}</div>;
    if (state.status === "done") return (
      <div className="tool-result tool-result--success">
        <a href={state.downloadUrl} download={state.fileName} className="download-btn">Download {state.fileName}</a>
      </div>
    );
    return null;
  }

  async function submitWaitlist(event) {
    event.preventDefault();
    setWaitlistStatus(""); setWaitlistError(""); setIsSubmitting(true);
    const form = new FormData(event.currentTarget);
    const payload = { name: String(form.get("name") || "").trim(), email: String(form.get("email") || "").trim(), plan_interest: String(form.get("plan_interest") || "pro"), use_case: buildUseCaseSummary(form) };
    try {
      const res = await fetch(waitlistAction, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await res.json();
      if (!res.ok) { setWaitlistError(data.message || "Could not join waitlist"); return; }
      setWaitlistStatus(data.message || "Joined waitlist");
      event.currentTarget.reset();
    } catch { setWaitlistError("Could not join waitlist right now. Please try again."); }
    finally { setIsSubmitting(false); }
  }

  async function handleCheckout(variantId) {
    if (!variantId) { window.location.href = "#waitlist"; return; }
    try {
      const res = await fetch("/api/checkout", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ variant_id: variantId }) });
      const data = await res.json();
      if (data.checkout_url) { window.location.href = data.checkout_url; } else { window.location.href = "#waitlist"; }
    } catch { window.location.href = "#waitlist"; }
  }

  async function submitFeedback(event) {
    event.preventDefault();
    setFeedbackStatus(""); setFeedbackError(""); setIsSendingFeedback(true);
    const form = new FormData(event.currentTarget);
    const payload = { email: String(form.get("email") || "").trim(), rating: parseInt(String(form.get("rating") || "5"), 10), message: String(form.get("message") || "").trim(), page: window.location.pathname };
    try {
      const res = await fetch("/api/feedback", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await res.json();
      if (!res.ok) { setFeedbackError(data.message || "Could not submit feedback"); return; }
      setFeedbackStatus(data.message || "Feedback sent!");
      event.currentTarget.reset();
    } catch { setFeedbackError("Could not send feedback right now."); }
    finally { setIsSendingFeedback(false); }
  }

  return (
    <main className="page-wrapper">
      <nav className="nav">
        <a href="/" className="nav-logo"><span className="gradient-text">PDFforge</span></a>
        <ul className="nav-links">
          <li><a href="#tools">Tools</a></li>
          <li><a href="#api">API</a></li>
          <li><a href="#pricing">Pricing</a></li>
          <li><a href="#waitlist">Early access</a></li>
          <li><a href="https://github.com/gengirish/pdfforge" target="_blank" rel="noopener noreferrer">GitHub</a></li>
        </ul>
      </nav>

      {/* ── Hero ── */}
      <section className="hero">
        <span className="hero-eyebrow">By IntelliForge AI — Now in beta</span>
        <h1>Stop routing sensitive PDFs<br />through <em>someone else&#39;s cloud</em></h1>
        <p className="hero-sub">
          PDFforge is an open-source PDF toolkit that runs on your infrastructure.
          Merge, split, rotate, extract text, encrypt, and decrypt in the browser — plus
          pipeline and batch APIs, async jobs, and interactive OpenAPI docs for automation.
          Your files never leave your machine.
        </p>
        <div className="hero-actions">
          <a href="#waitlist" className="btn-primary">Get early access</a>
          <a href="#tools" className="btn-ghost">Try the tools</a>
        </div>

        <div className="trust-row">
          <div className="trust-badge"><span className="trust-icon">&#128274;</span> Zero cloud uploads</div>
          <div className="trust-badge"><span className="trust-icon">&#9989;</span> MIT licensed</div>
          <div className="trust-badge"><span className="trust-icon">&#128272;</span> SOC 2 ready architecture</div>
          <div className="trust-badge"><span className="trust-icon">&#9203;</span> Sub-second processing</div>
        </div>

        <div className="proof-bar">
          <div className="proof-stat">
            <strong>{health.status === "ok" ? "Live" : "..."}</strong>
            <span>API Status</span>
          </div>
          <div className="proof-stat">
            <strong>{metrics.totalSignups ?? "..."}</strong>
            <span>Waitlist signups</span>
          </div>
          <div className="proof-stat">
            <strong>{metrics.toolCount}</strong>
            <span>Core tools</span>
          </div>
          <div className="proof-stat">
            <strong>{metrics.maxUploadMb ? `${metrics.maxUploadMb}MB` : "..."}</strong>
            <span>Max file size</span>
          </div>
        </div>
      </section>

      {/* ── Social proof ── */}
      <section id="testimonials">
        <p className="section-label">Trusted by teams</p>
        <h2 className="section-title">Why teams choose PDFforge</h2>
        <div className="testimonial-grid">
          {testimonials.map((t) => (
            <div className="testimonial-card" key={t.name}>
              <p className="testimonial-quote">&ldquo;{t.quote}&rdquo;</p>
              <div className="testimonial-author">
                <div className="testimonial-avatar">{t.name.charAt(0)}</div>
                <div>
                  <p className="testimonial-name">{t.name}</p>
                  <p className="testimonial-role">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how-it-works">
        <p className="section-label">How it works</p>
        <h2 className="section-title">Three steps. Zero cloud uploads.</h2>
        <div className="how-grid">
          <div className="how-step"><div className="step-num">01</div><h3>Upload locally</h3><p>Select PDFs from your machine. Files go straight to your Flask backend — never to a third-party server.</p></div>
          <div className="how-step"><div className="step-num">02</div><h3>Pick an operation</h3><p>Merge, split, rotate, extract text, encrypt, or decrypt. Each tool returns results in seconds.</p></div>
          <div className="how-step"><div className="step-num">03</div><h3>Download or automate</h3><p>Grab the output file instantly, or use the REST API — single tools, multi-step pipelines, bulk batch jobs, async processing with webhooks, and OpenAPI-backed clients.</p></div>
        </div>
      </section>

      {/* ── Tools ── */}
      <section id="tools">
        <p className="section-label">Toolkit</p>
        <h2 className="section-title">Everything your team needs for PDFs</h2>
        <p className="section-desc">
          Process files inline — results appear here, no page navigation. For chained workflows and bulk files, use the{" "}
          <a href="#api">pipeline and batch APIs</a> below.
        </p>
        <div className="tools-grid">
          {tools.map((tool) => (
            <div className="tool-cell" key={tool.id}>
              <div className="tool-icon">{tool.icon}</div>
              <h3>{tool.title}</h3>
              <p>{tool.desc}</p>

              {tool.id === "merge" && (
                <form onSubmit={onToolFormSubmit("merge")}>
                  <FileInput name="files" multiple label="Upload PDF files" />
                  <button type="submit" disabled={toolStates.merge?.status === "processing"}>
                    {toolStates.merge?.status === "processing" ? "Merging..." : "Merge & Download"}
                  </button>
                </form>
              )}
              {tool.id === "split" && (
                <form onSubmit={onToolFormSubmit("split")}>
                  <FileInput name="file" label="Upload PDF file" />
                  <input type="text" name="ranges" placeholder="1-2,3,5-7" required aria-label="Page ranges" />
                  <button type="submit" disabled={toolStates.split?.status === "processing"}>
                    {toolStates.split?.status === "processing" ? "Splitting..." : "Split & Download ZIP"}
                  </button>
                </form>
              )}
              {tool.id === "rotate" && (
                <form onSubmit={onToolFormSubmit("rotate")}>
                  <FileInput name="file" label="Upload PDF file" />
                  <select name="angle" defaultValue="90" aria-label="Rotation angle">
                    <option value="90">90 degrees</option>
                    <option value="180">180 degrees</option>
                    <option value="270">270 degrees</option>
                  </select>
                  <input type="text" name="pages" placeholder="Optional: 1,3-5" aria-label="Optional page numbers for rotation" />
                  <button type="submit" disabled={toolStates.rotate?.status === "processing"}>
                    {toolStates.rotate?.status === "processing" ? "Rotating..." : "Rotate & Download"}
                  </button>
                </form>
              )}
              {tool.id === "extract" && (
                <form onSubmit={onToolFormSubmit("extract")}>
                  <FileInput name="file" label="Upload PDF file" />
                  <button type="submit" disabled={toolStates.extract?.status === "processing"}>
                    {toolStates.extract?.status === "processing" ? "Extracting..." : "Extract TXT"}
                  </button>
                </form>
              )}
              {tool.id === "encrypt" && (
                <form onSubmit={onToolFormSubmit("encrypt")}>
                  <FileInput name="file" label="Upload PDF file" />
                  <input type="password" name="password" placeholder="Password" required aria-label="Password" />
                  <button type="submit" disabled={toolStates.encrypt?.status === "processing"}>
                    {toolStates.encrypt?.status === "processing" ? "Encrypting..." : "Encrypt & Download"}
                  </button>
                </form>
              )}
              {tool.id === "decrypt" && (
                <form onSubmit={onToolFormSubmit("decrypt")}>
                  <FileInput name="file" label="Upload PDF file" />
                  <input type="password" name="password" placeholder="Current password" required aria-label="Current password" />
                  <button type="submit" disabled={toolStates.decrypt?.status === "processing"}>
                    {toolStates.decrypt?.status === "processing" ? "Decrypting..." : "Decrypt & Download"}
                  </button>
                </form>
              )}
              <ToolResult toolId={tool.id} />
            </div>
          ))}
        </div>
      </section>

      {/* ── API & integrations ── */}
      <section id="api">
        <p className="section-label">Developers</p>
        <h2 className="section-title">Automation-ready API</h2>
        <p className="section-desc">
          Everything below is served by the same Flask backend as the dashboard ({backendBase}). Replace with your deployed URL in production.
        </p>
        <div className="how-grid">
          <div className="how-step">
            <div className="step-num">REST</div>
            <h3>Core tools</h3>
            <p>
              <code>POST /api/v1/merge</code>, <code>/split</code>, <code>/rotate</code>, <code>/extract_text</code>,{" "}
              <code>/encrypt</code>, <code>/decrypt</code> — JSON job envelopes by default, or <code>?download=true</code> for raw files.
            </p>
          </div>
          <div className="how-step">
            <div className="step-num">Flow</div>
            <h3>Pipeline &amp; batch</h3>
            <p>
              <code>POST /api/v1/pipeline</code> chains steps without multiple round trips.{" "}
              <code>POST /api/v1/batch</code> runs the same operation on many PDFs in one request.
            </p>
          </div>
          <div className="how-step">
            <div className="step-num">Async</div>
            <h3>Jobs &amp; webhooks</h3>
            <p>
              Pass <code>X-Async: true</code> or <code>?async=true</code> on tool routes for <code>202</code> queued responses, then poll{" "}
              <code>/api/v1/jobs/&lt;id&gt;</code>. Optional <code>webhook_url</code> and <code>webhook_secret</code> form fields notify when work finishes.
            </p>
          </div>
          <div className="how-step">
            <div className="step-num">Docs</div>
            <h3>OpenAPI &amp; discovery</h3>
            <p>
              <a href={`${backendBase}/api/v1/capabilities`} target="_blank" rel="noopener noreferrer">Capabilities manifest</a>
              {" · "}
              <a href={`${backendBase}/api/v1/openapi.json`} target="_blank" rel="noopener noreferrer">OpenAPI JSON</a>
              {" · "}
              <a href={`${backendBase}/api/v1/docs`} target="_blank" rel="noopener noreferrer">Swagger UI</a>
              {" · "}
              <a href={`${backendBase}/api/v1/redoc`} target="_blank" rel="noopener noreferrer">ReDoc</a>
            </p>
          </div>
          <div className="how-step">
            <div className="step-num">AI</div>
            <h3>Optional agent planner</h3>
            <p>
              <code>POST /api/v1/agent/interpret</code> turns natural language into a pipeline plan (and can execute it) when{" "}
              <code>ANTHROPIC_API_KEY</code> is configured on the server.
            </p>
          </div>
          <div className="how-step">
            <div className="step-num">SDK</div>
            <h3>MCP &amp; Python</h3>
            <p>
              Use the{" "}
              <a href="https://github.com/gengirish/pdfforge/tree/main/mcp" target="_blank" rel="noopener noreferrer">PDFforge MCP server</a>
              {" "}for Claude Desktop, or the{" "}
              <a href="https://github.com/gengirish/pdfforge/tree/main/sdk/python" target="_blank" rel="noopener noreferrer">Python SDK</a>
              {" "}(async jobs, pipeline, batch).
            </p>
          </div>
        </div>
      </section>

      {/* ── Pricing ── */}
      <section id="pricing">
        <p className="section-label">Pricing</p>
        <h2 className="section-title">Free to self-host. Paid when you need hosting.</h2>
        <p className="section-desc">The open-source core is free forever. Paid plans add hosted infrastructure, bigger limits, and team features.</p>
        <div className="pricing-grid">
          {pricingPlans.map((plan) => (
            <div className={`price-card${plan.highlighted ? " price-card--featured" : ""}`} key={plan.name}>
              <h3>{plan.name}</h3>
              <div className="price-amount"><strong>${plan.price}</strong><span>{plan.period}</span></div>
              <ul className="price-features">{plan.features.map((f) => <li key={f}>{f}</li>)}</ul>
              {plan.variantId ? (
                <button className="price-cta price-cta--primary" onClick={() => handleCheckout(plan.variantId)}>{plan.cta}</button>
              ) : (
                <span className="price-cta price-cta--muted">{plan.cta}</span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── Waitlist ── */}
      <section id="waitlist">
        <p className="section-label">Early access</p>
        <h2 className="section-title">Get in before the public launch</h2>
        <p className="section-desc">Tell us your workflow. We prioritize features for the teams that need them most.</p>
        <div className="waitlist-split">
          <div className="wl-card">
            <h3>Join early access</h3>
            <p className="wl-hint">We review every submission personally.</p>
            <form onSubmit={submitWaitlist}>
              <input type="text" name="name" placeholder="Name" maxLength={120} aria-label="Your name" />
              <input type="email" name="email" placeholder="Work email" required aria-label="Work email" />
              <input type="text" name="team_size" placeholder="Team size (e.g. 5-10)" maxLength={60} aria-label="Team size" />
              <input type="text" name="monthly_volume" placeholder="Monthly PDF volume (e.g. 2,000 docs)" maxLength={80} aria-label="Monthly PDF volume" />
              <select name="primary_use_case" defaultValue={useCases[0]} aria-label="Primary use case">
                {useCases.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
              </select>
              <select name="timeline" defaultValue="this-quarter" aria-label="Implementation timeline">
                <option value="this-week">Need a fix this week</option>
                <option value="this-month">Need a fix this month</option>
                <option value="this-quarter">Planning this quarter</option>
              </select>
              <select name="plan_interest" defaultValue="pro" aria-label="Plan interest">
                <option value="pro">Pro</option>
                <option value="team">Team</option>
                <option value="other">Not sure yet</option>
              </select>
              <textarea name="use_case" placeholder="What is the most painful PDF step right now?" maxLength={280} aria-label="Describe your most painful PDF workflow step" />
              <button type="submit" disabled={isSubmitting}>{isSubmitting ? "Submitting..." : "Join Waitlist"}</button>
            </form>
            {waitlistStatus ? <p className="msg-success">{waitlistStatus}</p> : null}
            {waitlistError ? <p className="msg-error">{waitlistError}</p> : null}
          </div>
          <div className="wl-card">
            <h3>Who gets priority?</h3>
            <p className="wl-hint">We fast-track teams with the highest document volume and urgency.</p>
            <ul className="wl-reasons">
              <li>Ops teams processing contracts, invoices, and reports weekly</li>
              <li>Recruiting teams merging high-volume candidate packets</li>
              <li>Finance teams needing compliant, auditable document workflows</li>
              <li>Founders who need automation without third-party data exposure</li>
              <li>Teams moving from manual copy/paste PDF work to API-driven pipelines</li>
            </ul>
          </div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section>
        <p className="section-label">FAQ</p>
        <h2 className="section-title">Common questions</h2>
        <div className="faq-grid">
          {faqs.map((entry) => <div className="faq-item" key={entry.q}><h3>{entry.q}</h3><p>{entry.a}</p></div>)}
        </div>
      </section>

      {/* ── Feedback ── */}
      <section id="feedback">
        <p className="section-label">Beta</p>
        <h2 className="section-title">Share your experience</h2>
        <p className="section-desc">Every piece of feedback directly shapes the roadmap.</p>
        <div className="feedback-split">
          <div className="fb-card">
            <h3>Send feedback</h3>
            <p className="fb-hint">Bug, feature request, or just thoughts — we read everything.</p>
            <form onSubmit={submitFeedback}>
              <input type="email" name="email" placeholder="Email (optional)" aria-label="Feedback email" />
              <select name="rating" defaultValue="5" aria-label="Rating">
                <option value="5">5 — Love it</option><option value="4">4 — Works well</option><option value="3">3 — Decent</option><option value="2">2 — Needs work</option><option value="1">1 — Broken</option>
              </select>
              <textarea name="message" placeholder="What worked? What didn't? What do you wish existed?" maxLength={600} required aria-label="Feedback message" />
              <button type="submit" disabled={isSendingFeedback}>{isSendingFeedback ? "Sending..." : "Send Feedback"}</button>
            </form>
            {feedbackStatus ? <p className="msg-success">{feedbackStatus}</p> : null}
            {feedbackError ? <p className="msg-error">{feedbackError}</p> : null}
          </div>
          <div className="fb-card">
            <h3>Beta resources</h3>
            <p className="fb-hint">Everything you need to test PDFforge.</p>
            <ul className="fb-resources">
              <li><a href={`${backendBase}/api/v1/test-pdf`} target="_blank" rel="noopener noreferrer">Download test PDF</a> — sample to exercise every tool</li>
              <li>Try each dashboard tool: merge, split, rotate, extract text, encrypt, decrypt</li>
              <li>
                API: <a href={`${backendBase}/api/v1/tools`} target="_blank" rel="noopener noreferrer"><code>/api/v1/tools</code></a>
                {" · "}
                <a href={`${backendBase}/api/v1/capabilities`} target="_blank" rel="noopener noreferrer">capabilities</a>
                {" · "}
                <a href={`${backendBase}/api/v1/docs`} target="_blank" rel="noopener noreferrer">Swagger</a>
              </li>
              <li>Submit feedback for every issue or feature request</li>
            </ul>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="site-footer">
        <div className="footer-top">
          <span className="footer-brand"><span className="gradient-text">PDFforge</span></span>
          <span className="footer-byline">Built by{" "}<a href="https://www.intelliforge.tech/" target="_blank" rel="noopener noreferrer">IntelliForge AI</a></span>
        </div>
        <ul className="footer-links">
          <li><a href="/api/health">Health</a></li>
          <li><a href="/api/metrics">Metrics</a></li>
          <li><a href={`${backendBase}/api/v1/docs`} target="_blank" rel="noopener noreferrer">API docs</a></li>
          <li><a href="#feedback">Feedback</a></li>
          <li><a href="https://github.com/gengirish/pdfforge" target="_blank" rel="noopener noreferrer">GitHub</a></li>
          <li><a href="https://www.intelliforge.tech/" target="_blank" rel="noopener noreferrer">IntelliForge AI</a></li>
        </ul>
      </footer>
    </main>
  );
}
