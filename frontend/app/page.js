"use client";

import { useEffect, useMemo, useState } from "react";

const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:5050";

const tools = [
  { id: "merge", title: "Merge PDFs", action: "/merge" },
  { id: "split", title: "Split PDF", action: "/split" },
  { id: "rotate", title: "Rotate Pages", action: "/rotate" },
  { id: "extract", title: "Extract Text", action: "/extract-text" },
  { id: "encrypt", title: "Encrypt PDF", action: "/encrypt" },
  { id: "decrypt", title: "Decrypt PDF", action: "/decrypt" },
];

const useCases = [
  "Contracts and legal docs",
  "Invoices and accounting docs",
  "Hiring and candidate packets",
  "Ops runbooks and reports",
  "Client deliverables",
];

const faqs = [
  {
    q: "Where are my files processed?",
    a: "All processing runs in your local Flask backend. Files are not uploaded to a third-party cloud by default.",
  },
  {
    q: "Is there an API we can automate?",
    a: "Yes. Versioned endpoints are available at /api/v1/* so teams can script common document workflows.",
  },
  {
    q: "What is the paid roadmap?",
    a: "OCR, templates, team workspaces, audit logs, and usage-based hosted deployment for teams that need it.",
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

export default function Page() {
  const [health, setHealth] = useState({ status: "checking" });
  const [metrics, setMetrics] = useState({
    totalSignups: null,
    toolCount: tools.length,
    maxUploadMb: null,
  });
  const [waitlistStatus, setWaitlistStatus] = useState("");
  const [waitlistError, setWaitlistError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const waitlistAction = useMemo(() => "/api/waitlist", []);

  useEffect(() => {
    let isMounted = true;
    Promise.allSettled([fetch("/api/health"), fetch("/api/metrics")]).then(async ([healthRes, metricsRes]) => {
      if (!isMounted) return;

      if (healthRes.status === "fulfilled") {
        const healthJson = await healthRes.value.json();
        setHealth(healthJson);
      } else {
        setHealth({ status: "error", message: "Backend unreachable" });
      }

      if (metricsRes.status === "fulfilled") {
        const metricsJson = await metricsRes.value.json();
        const apiMetrics = metricsJson?.metrics || {};
        setMetrics({
          totalSignups:
            typeof apiMetrics.total_signups === "number" ? apiMetrics.total_signups : null,
          toolCount: typeof apiMetrics.tool_count === "number" ? apiMetrics.tool_count : tools.length,
          maxUploadMb: typeof apiMetrics.max_upload_mb === "number" ? apiMetrics.max_upload_mb : null,
        });
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  async function submitWaitlist(event) {
    event.preventDefault();
    setWaitlistStatus("");
    setWaitlistError("");
    setIsSubmitting(true);

    const form = new FormData(event.currentTarget);
    const payload = {
      name: String(form.get("name") || "").trim(),
      email: String(form.get("email") || "").trim(),
      plan_interest: String(form.get("plan_interest") || "pro"),
      use_case: buildUseCaseSummary(form),
    };

    try {
      const res = await fetch(waitlistAction, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setWaitlistError(data.message || "Could not join waitlist");
        return;
      }
      setWaitlistStatus(data.message || "Joined waitlist");
      event.currentTarget.reset();
    } catch (_error) {
      setWaitlistError("Could not join waitlist right now. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="container">
      <section className="hero">
        <span className="badge">Back-office PDF copilot for lean teams</span>
        <h1>Fix broken document workflows in minutes, not sprint cycles</h1>
        <p className="subtitle">
          PDFforge helps operators and founders process contracts, invoices, and reports without
          routing sensitive PDFs through external tools.
        </p>
        <div className="hero-cta-row">
          <a href="#waitlist" className="cta-primary">
            Get beta access
          </a>
          <a href="#tools" className="cta-secondary">
            Try local tools now
          </a>
        </div>
        <div className="chip-row">
          <span className="chip">No cloud upload by default</span>
          <span className="chip">Backend: Flask + pypdf</span>
          <span className="chip">Frontend: Next.js 14</span>
        </div>
      </section>

      <section className="traction-grid" aria-label="traction">
        <article className="metric-card">
          <p className="metric-label">Backend health</p>
          <p className="metric-value">
            <strong>{health.status || "unknown"}</strong>
          </p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Waitlist signups</p>
          <p className="metric-value">{metrics.totalSignups ?? "..."}</p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Core workflows</p>
          <p className="metric-value">{metrics.toolCount}</p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Max file size</p>
          <p className="metric-value">{metrics.maxUploadMb ? `${metrics.maxUploadMb}MB` : "..."}</p>
        </article>
      </section>

      <section className="status">
        <p className="muted">
          Backend health: <strong>{health.status || "unknown"}</strong>
        </p>
        <p className="muted">
          Connected backend: <code>{backendBase}</code>
        </p>
      </section>

      <section className="problem-solution">
        <article className="card">
          <h2>Why teams switch</h2>
          <ul className="muted">
            <li>Manual PDF cleanup blocks finance, legal, and ops every week</li>
            <li>Most online PDF tools create privacy and compliance concerns</li>
            <li>Single-click local workflows reduce repetitive busywork immediately</li>
          </ul>
        </article>
        <article className="card">
          <h2>Built for YC-style velocity</h2>
          <ul className="muted">
            <li>Ship value fast: six daily workflows out of the box</li>
            <li>Measure demand: structured waitlist with ICP signals</li>
            <li>Expand fast: versioned API ready for automation and SaaS rollout</li>
          </ul>
        </article>
      </section>

      <section id="tools">
        <h2>PDF Tools</h2>
        <p className="muted">
          Each tool submits directly to the Flask backend and returns downloadable output.
        </p>
        <div className="tools-grid">
          {tools.map((tool) => (
            <article className="card" key={tool.id}>
              <h3>{tool.title}</h3>
              {tool.id === "merge" && (
                <form method="post" action={`${backendBase}/merge`} encType="multipart/form-data">
                  <input type="file" name="files" accept=".pdf,application/pdf" multiple required />
                  <button type="submit">Merge & Download</button>
                </form>
              )}
              {tool.id === "split" && (
                <form method="post" action={`${backendBase}/split`} encType="multipart/form-data">
                  <input type="file" name="file" accept=".pdf,application/pdf" required />
                  <input type="text" name="ranges" placeholder="1-2,3,5-7" required />
                  <button type="submit">Split & Download ZIP</button>
                </form>
              )}
              {tool.id === "rotate" && (
                <form method="post" action={`${backendBase}/rotate`} encType="multipart/form-data">
                  <input type="file" name="file" accept=".pdf,application/pdf" required />
                  <select name="angle" defaultValue="90">
                    <option value="90">90 degrees</option>
                    <option value="180">180 degrees</option>
                    <option value="270">270 degrees</option>
                  </select>
                  <input type="text" name="pages" placeholder="Optional: 1,3-5" />
                  <button type="submit">Rotate & Download</button>
                </form>
              )}
              {tool.id === "extract" && (
                <form method="post" action={`${backendBase}/extract-text`} encType="multipart/form-data">
                  <input type="file" name="file" accept=".pdf,application/pdf" required />
                  <button type="submit">Extract TXT</button>
                </form>
              )}
              {tool.id === "encrypt" && (
                <form method="post" action={`${backendBase}/encrypt`} encType="multipart/form-data">
                  <input type="file" name="file" accept=".pdf,application/pdf" required />
                  <input type="password" name="password" placeholder="Password" required />
                  <button type="submit">Encrypt & Download</button>
                </form>
              )}
              {tool.id === "decrypt" && (
                <form method="post" action={`${backendBase}/decrypt`} encType="multipart/form-data">
                  <input type="file" name="file" accept=".pdf,application/pdf" required />
                  <input type="password" name="password" placeholder="Current password" required />
                  <button type="submit">Decrypt & Download</button>
                </form>
              )}
            </article>
          ))}
        </div>
      </section>

      <section id="waitlist">
        <h2>Pro Waitlist</h2>
        <div className="waitlist-grid">
          <article className="card">
            <h3>Join early access</h3>
            <p className="muted">Tell us your workflow so we can prioritize features that unblock your team fastest.</p>
            <form onSubmit={submitWaitlist}>
              <input type="text" name="name" placeholder="Name" maxLength={120} />
              <input type="email" name="email" placeholder="Work email" required />
              <input type="text" name="team_size" placeholder="Team size (e.g. 5-10)" maxLength={60} />
              <input type="text" name="monthly_volume" placeholder="Monthly PDF volume (e.g. 2,000 docs)" maxLength={80} />
              <select name="primary_use_case" defaultValue={useCases[0]}>
                {useCases.map((entry) => (
                  <option key={entry} value={entry}>
                    {entry}
                  </option>
                ))}
              </select>
              <select name="timeline" defaultValue="this-quarter">
                <option value="this-week">Need a fix this week</option>
                <option value="this-month">Need a fix this month</option>
                <option value="this-quarter">Planning this quarter</option>
              </select>
              <select name="plan_interest" defaultValue="pro">
                <option value="pro">Pro</option>
                <option value="team">Team</option>
                <option value="other">Not sure yet</option>
              </select>
              <textarea name="use_case" placeholder="What is the most painful PDF step right now?" maxLength={280} />
              <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Submitting..." : "Join Waitlist"}
              </button>
            </form>
            {waitlistStatus ? <p className="success">{waitlistStatus}</p> : null}
            {waitlistError ? <p className="error">{waitlistError}</p> : null}
          </article>

          <article className="card">
            <h3>Founder Console</h3>
            <p className="muted">Use backend admin endpoints to inspect signups and segment demand quickly.</p>
            <ul className="muted">
              <li>Pipeline table: /admin/waitlist</li>
              <li>JSON export: /api/v1/waitlist</li>
              <li>Live topline metrics: /api/v1/metrics</li>
            </ul>
          </article>
        </div>
      </section>

      <section>
        <h2>FAQ</h2>
        <div className="faq-grid">
          {faqs.map((entry) => (
            <article className="card" key={entry.q}>
              <h3>{entry.q}</h3>
              <p className="muted">{entry.a}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
