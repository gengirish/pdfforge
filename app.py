from __future__ import annotations

import hmac
import io
import logging
import os
import re
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pdfplumber
from flask import Flask, Response, jsonify, redirect, render_template_string, request, send_file, url_for
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency in local dev
    psycopg = None

app = Flask(__name__)

ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000").split(",")
    if o.strip()
]
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=False)

DEFAULT_MAX_MB = int(os.getenv("MAX_CONTENT_LENGTH_MB", "50"))
app.config["MAX_CONTENT_LENGTH"] = DEFAULT_MAX_MB * 1024 * 1024
WAITLIST_DB_PATH = Path(os.getenv("WAITLIST_DB_PATH", Path(__file__).with_name("waitlist.db")))
WAITLIST_DATABASE_URL = os.getenv("WAITLIST_DATABASE_URL", "").strip()
WAITLIST_ADMIN_TOKEN = os.getenv("WAITLIST_ADMIN_TOKEN", "")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


TOOL_CARDS = [
    {
        "title": "Merge",
        "subtitle": "Combine multiple PDFs into one file",
        "icon": "M",
        "href": "#merge",
    },
    {
        "title": "Split",
        "subtitle": "Export selected page ranges as separate PDFs",
        "icon": "S",
        "href": "#split",
    },
    {
        "title": "Rotate",
        "subtitle": "Fix page orientation for all or selected pages",
        "icon": "R",
        "href": "#rotate",
    },
    {
        "title": "Extract Text",
        "subtitle": "Convert PDF text to downloadable TXT",
        "icon": "T",
        "href": "#extract",
    },
    {
        "title": "Encrypt",
        "subtitle": "Protect PDFs with password security",
        "icon": "E",
        "href": "#encrypt",
    },
    {
        "title": "Decrypt",
        "subtitle": "Unlock encrypted PDFs with current password",
        "icon": "D",
        "href": "#decrypt",
    },
]

PRICING_PLANS = [
    {
        "name": "Free",
        "price": "0",
        "period": "/mo",
        "features": "Local tools, no account, localhost only",
        "cta": "Current mode",
        "href": "#",
        "highlight": False,
    },
    {
        "name": "Pro",
        "price": "9",
        "period": "/mo",
        "features": "OCR, presets, larger files, priority support",
        "cta": "Join waitlist",
        "href": "#waitlist",
        "highlight": True,
    },
    {
        "name": "Team",
        "price": "29",
        "period": "/mo",
        "features": "Shared workspace, audit logs, admin controls",
        "cta": "Contact sales",
        "href": "#waitlist",
        "highlight": False,
    },
]


HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PDFforge</title>
    <style>
      :root {
        --bg: #0b1020;
        --surface: #121a30;
        --surface-soft: #1a2646;
        --text: #e7ecff;
        --text-soft: #b8c4ea;
        --primary: #6ea8fe;
        --success: #2eb67d;
        --danger: #ff6b6b;
        --border: rgba(255, 255, 255, 0.12);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Inter, Segoe UI, Arial, sans-serif;
        background: radial-gradient(circle at top, #1d2a4f 0%, var(--bg) 40%);
        color: var(--text);
      }
      .container {
        width: min(1120px, 92%);
        margin: 0 auto;
      }
      .hero {
        padding: 38px 0 24px;
      }
      .badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(110, 168, 254, 0.14);
        border: 1px solid rgba(110, 168, 254, 0.35);
        color: #dbe9ff;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 12px;
        margin-bottom: 14px;
      }
      h1 {
        margin: 0;
        font-size: clamp(28px, 4vw, 44px);
        line-height: 1.1;
      }
      .subtitle {
        color: var(--text-soft);
        margin-top: 10px;
        max-width: 760px;
      }
      .trust {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 16px;
      }
      .chip {
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 8px 12px;
        color: var(--text-soft);
        font-size: 13px;
        background: rgba(255, 255, 255, 0.03);
      }
      .tools-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin: 18px 0 24px;
      }
      .tool-link {
        text-decoration: none;
        color: inherit;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.03);
        border-radius: 14px;
        padding: 14px;
        display: block;
      }
      .tool-link:hover {
        border-color: rgba(110, 168, 254, 0.55);
        transform: translateY(-1px);
      }
      .tool-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 600;
      }
      .icon {
        width: 24px;
        height: 24px;
        display: grid;
        place-items: center;
        border-radius: 7px;
        background: rgba(110, 168, 254, 0.18);
        color: #cfe0ff;
        font-size: 12px;
      }
      .tool-sub {
        color: var(--text-soft);
        margin-top: 8px;
        font-size: 13px;
      }
      .pricing {
        margin-top: 14px;
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
      }
      .plan {
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px;
        background: rgba(255, 255, 255, 0.03);
      }
      .plan.highlight {
        border-color: rgba(110, 168, 254, 0.6);
        box-shadow: 0 0 0 1px rgba(110, 168, 254, 0.25) inset;
      }
      .plan h4 {
        margin: 0 0 6px;
      }
      .price-row {
        display: flex;
        align-items: baseline;
        gap: 4px;
        margin: 4px 0 8px;
      }
      .price {
        font-size: 28px;
        font-weight: 800;
      }
      .period {
        color: var(--text-soft);
      }
      .plan-feature {
        color: var(--text-soft);
        font-size: 13px;
        min-height: 36px;
      }
      .plan-cta {
        margin-top: 10px;
        width: 100%;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 8px 10px;
        background: rgba(255, 255, 255, 0.04);
        color: var(--text);
        font-weight: 600;
        text-align: center;
        text-decoration: none;
        display: inline-block;
      }
      .alert {
        margin: 8px 0 18px;
        border: 1px solid rgba(255, 107, 107, 0.55);
        background: rgba(255, 107, 107, 0.1);
        color: #ffc6c6;
        border-radius: 10px;
        padding: 10px 12px;
      }
      .alert-success {
        margin: 8px 0 18px;
        border: 1px solid rgba(46, 182, 125, 0.55);
        background: rgba(46, 182, 125, 0.1);
        color: #b7f5da;
        border-radius: 10px;
        padding: 10px 12px;
      }
      .alert-info {
        margin: 8px 0 18px;
        border: 1px solid rgba(110, 168, 254, 0.55);
        background: rgba(110, 168, 254, 0.1);
        color: #d2e4ff;
        border-radius: 10px;
        padding: 10px 12px;
      }
      .section-title {
        margin: 24px 0 10px;
        color: #d5e2ff;
      }
      .forms {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
        padding-bottom: 30px;
      }
      .card {
        border: 1px solid var(--border);
        background: linear-gradient(180deg, var(--surface) 0%, var(--surface-soft) 100%);
        border-radius: 14px;
        padding: 16px;
      }
      .card h3 {
        margin-top: 0;
        margin-bottom: 6px;
      }
      .hint {
        margin: 0 0 10px;
        color: var(--text-soft);
        font-size: 13px;
      }
      .row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }
      .waitlist-grid {
        display: grid;
        grid-template-columns: 1.1fr 1fr;
        gap: 12px;
        margin-top: 14px;
      }
      .waitlist-list {
        margin: 0;
        padding-left: 20px;
        color: var(--text-soft);
      }
      input, select, button {
        width: 100%;
        padding: 10px 11px;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: rgba(5, 10, 20, 0.35);
        color: var(--text);
        margin-top: 8px;
      }
      button {
        border: none;
        background: linear-gradient(180deg, #6ea8fe 0%, #4e8ef0 100%);
        color: #04132f;
        font-weight: 700;
        cursor: pointer;
      }
      button:hover {
        filter: brightness(1.05);
      }
      code {
        background: rgba(255, 255, 255, 0.12);
        padding: 2px 6px;
        border-radius: 5px;
      }
      textarea {
        width: 100%;
        padding: 10px 11px;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: rgba(5, 10, 20, 0.35);
        color: var(--text);
        margin-top: 8px;
        min-height: 88px;
        resize: vertical;
      }
      footer {
        color: var(--text-soft);
        border-top: 1px solid var(--border);
        margin-top: 18px;
        padding: 14px 0 24px;
        font-size: 12px;
      }
      @media (max-width: 880px) {
        .tools-grid { grid-template-columns: 1fr 1fr; }
        .pricing { grid-template-columns: 1fr; }
      }
      @media (max-width: 680px) {
        .tools-grid, .row { grid-template-columns: 1fr; }
        .waitlist-grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <main class="container">
      <section class="hero">
        <span class="badge">Local-first PDF workflow</span>
        <h1>PDFforge</h1>
        <p class="subtitle">
          A fast, privacy-first PDF toolkit for founders, operators, and teams.
          Your files stay on your machine while you merge, split, rotate, extract, encrypt, and decrypt in seconds.
        </p>
        <div class="trust">
          <span class="chip">No cloud upload</span>
          <span class="chip">Runs on localhost</span>
          <span class="chip">Max file size: {{ max_mb }}MB</span>
          <span class="chip">Open-source stack: Flask + pypdf</span>
        </div>
      </section>

      {% if error %}
        <div class="alert">Error: {{ error }}</div>
      {% endif %}
      {% if success %}
        <div class="alert-success">{{ success }}</div>
      {% endif %}
      {% if info %}
        <div class="alert-info">{{ info }}</div>
      {% endif %}

      <section class="tools-grid" aria-label="tool navigation">
        {% for card in tool_cards %}
          <a class="tool-link" href="{{ card.href }}">
            <div class="tool-title">
              <span class="icon">{{ card.icon }}</span>
              <span>{{ card.title }}</span>
            </div>
            <div class="tool-sub">{{ card.subtitle }}</div>
          </a>
        {% endfor %}
      </section>

      <h2 class="section-title">Tools</h2>
      <section class="forms">
        <article class="card" id="merge">
          <h3>1) Merge PDFs</h3>
          <p class="hint">Upload multiple PDFs in order, and get one merged file.</p>
          <form method="post" action="/merge" enctype="multipart/form-data">
            <input type="file" name="files" accept=".pdf,application/pdf" multiple required />
            <button type="submit">Merge and Download</button>
          </form>
        </article>

        <article class="card" id="split">
          <h3>2) Split PDF by page ranges</h3>
          <p class="hint">
            Use 1-based ranges like <code>1-2,3,5-7</code>. Output is a ZIP with one PDF per range.
          </p>
          <form method="post" action="/split" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf,application/pdf" required />
            <input type="text" name="ranges" placeholder="Example: 1-2,3,5-7" required />
            <button type="submit">Split and Download ZIP</button>
          </form>
        </article>

        <article class="card" id="rotate">
          <h3>3) Rotate pages</h3>
          <p class="hint">Rotate all pages or only selected pages.</p>
          <form method="post" action="/rotate" enctype="multipart/form-data">
            <div class="row">
              <input type="file" name="file" accept=".pdf,application/pdf" required />
              <select name="angle" required>
                <option value="90">90 degrees</option>
                <option value="180">180 degrees</option>
                <option value="270">270 degrees</option>
              </select>
            </div>
            <input type="text" name="pages" placeholder="Optional pages, e.g. 1,3-5 (blank = all)" />
            <button type="submit">Rotate and Download</button>
          </form>
        </article>

        <article class="card" id="extract">
          <h3>4) Extract text</h3>
          <p class="hint">Extract machine-readable text from each page to a .txt file.</p>
          <form method="post" action="/extract-text" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf,application/pdf" required />
            <button type="submit">Extract to TXT</button>
          </form>
        </article>

        <article class="card" id="encrypt">
          <h3>5) Encrypt PDF</h3>
          <p class="hint">Protect your file with a password before sharing.</p>
          <form method="post" action="/encrypt" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf,application/pdf" required />
            <input type="password" name="password" placeholder="Set password" required />
            <button type="submit">Encrypt and Download</button>
          </form>
        </article>

        <article class="card" id="decrypt">
          <h3>6) Decrypt PDF</h3>
          <p class="hint">Unlock an encrypted PDF with the current password.</p>
          <form method="post" action="/decrypt" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf,application/pdf" required />
            <input type="password" name="password" placeholder="Current password" required />
            <button type="submit">Decrypt and Download</button>
          </form>
        </article>
      </section>

      <h2 class="section-title">Pricing (planned)</h2>
      <section class="pricing" aria-label="pricing">
        {% for plan in plans %}
          <article class="plan {% if plan.highlight %}highlight{% endif %}">
            <h4>{{ plan.name }}</h4>
            <div class="price-row">
              <span class="price">${{ plan.price }}</span>
              <span class="period">{{ plan.period }}</span>
            </div>
            <p class="plan-feature">{{ plan.features }}</p>
            <a class="plan-cta" href="{{ plan.href }}">{{ plan.cta }}</a>
          </article>
        {% endfor %}
      </section>

      <h2 class="section-title" id="waitlist">Pro Waitlist</h2>
      <section class="waitlist-grid" aria-label="waitlist">
        <article class="card">
          <h3>Get early access</h3>
          <p class="hint">
            Join the waitlist for OCR, hosted collaboration, templates, and billing features.
          </p>
          <form method="post" action="/waitlist">
            <input type="text" name="name" placeholder="Name (optional)" maxlength="120" />
            <input type="email" name="email" placeholder="Work email" required />
            <select name="plan_interest">
              <option value="pro">Pro</option>
              <option value="team">Team</option>
              <option value="other">Not sure yet</option>
            </select>
            <textarea
              name="use_case"
              placeholder="What PDF workflows are most painful today?"
              maxlength="600"
            ></textarea>
            <button type="submit">Join Waitlist</button>
          </form>
        </article>
        <article class="card">
          <h3>Who this is for</h3>
          <p class="hint">Priority access goes to teams with frequent document workflows.</p>
          <ul class="waitlist-list">
            <li>Ops teams handling contracts, invoices, and reports</li>
            <li>Recruiting teams processing high-volume resumes</li>
            <li>Founders who need secure local-first PDF automation</li>
            <li>Teams moving from manual copy/paste document work</li>
          </ul>
          <p class="hint" style="margin-top:10px">
            Admin view: <code>/admin/waitlist</code>
            {% if has_admin_token %}(token required){% endif %}
          </p>
        </article>
      </section>

      <footer>
        Built for local use. Scanned PDF OCR is not included yet.
        Health check endpoints: <code>/health</code>, <code>/api/v1/health</code>
      </footer>
    </main>
  </body>
</html>
"""


def bad_request(message: str) -> Response:
    return Response(message, status=400, mimetype="text/plain")


def safe_error_message(exc: Exception) -> str:
    """Return a user-safe error message, hiding internal details in production."""
    safe_types = (ValueError, zipfile.BadZipFile)
    if isinstance(exc, safe_types):
        return str(exc)
    app.logger.exception("Unexpected error in PDF operation")
    return "An error occurred processing your PDF. Please check the file and try again."


def init_waitlist_db() -> None:
    using_postgres = WAITLIST_DATABASE_URL.startswith("postgresql://") or WAITLIST_DATABASE_URL.startswith("postgres://")
    if using_postgres:
        if psycopg is None:
            raise RuntimeError("WAITLIST_DATABASE_URL is set but psycopg is not installed.")
        with psycopg.connect(WAITLIST_DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS waitlist_signups (
                        id BIGSERIAL PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL DEFAULT '',
                        use_case TEXT NOT NULL DEFAULT '',
                        plan_interest TEXT NOT NULL DEFAULT 'pro',
                        source_ip TEXT NOT NULL DEFAULT '',
                        user_agent TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS idx_waitlist_created ON waitlist_signups(created_at DESC)")
            conn.commit()
        return

    WAITLIST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(WAITLIST_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS waitlist_signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL DEFAULT '',
                use_case TEXT NOT NULL DEFAULT '',
                plan_interest TEXT NOT NULL DEFAULT 'pro',
                source_ip TEXT NOT NULL DEFAULT '',
                user_agent TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_waitlist_created ON waitlist_signups(created_at DESC)")
        conn.commit()


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def create_waitlist_signup(
    *,
    email: str,
    name: str,
    use_case: str,
    plan_interest: str,
    source_ip: str,
    user_agent: str,
) -> tuple[bool, str]:
    normalized_email = email.strip().lower()
    if not is_valid_email(normalized_email):
        return False, "Please provide a valid email address."
    if len(name) > 120:
        return False, "Name is too long (max 120 characters)."
    if len(use_case) > 600:
        return False, "Use case is too long (max 600 characters)."
    if plan_interest not in {"pro", "team", "other"}:
        return False, "Invalid plan selection."

    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    using_postgres = WAITLIST_DATABASE_URL.startswith("postgresql://") or WAITLIST_DATABASE_URL.startswith("postgres://")
    if using_postgres:
        try:
            if psycopg is None:
                return False, "Postgres driver not installed. Add psycopg to requirements."
            with psycopg.connect(WAITLIST_DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO waitlist_signups (email, name, use_case, plan_interest, source_ip, user_agent, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (normalized_email, name.strip(), use_case.strip(), plan_interest, source_ip, user_agent, now),
                    )
                conn.commit()
        except Exception as exc:
            if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                return False, "This email is already on the waitlist."
            return False, f"Database error: {exc}"
        return True, "Thanks! You are on the waitlist."

    try:
        with sqlite3.connect(WAITLIST_DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO waitlist_signups (email, name, use_case, plan_interest, source_ip, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (normalized_email, name.strip(), use_case.strip(), plan_interest, source_ip, user_agent, now),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return False, "This email is already on the waitlist."

    return True, "Thanks! You are on the waitlist."


def read_waitlist_signups(limit: int = 500) -> list[dict]:
    using_postgres = WAITLIST_DATABASE_URL.startswith("postgresql://") or WAITLIST_DATABASE_URL.startswith("postgres://")
    if using_postgres:
        if psycopg is None:
            return []
        with psycopg.connect(WAITLIST_DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, email, name, use_case, plan_interest, source_ip, user_agent, created_at
                    FROM waitlist_signups
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "email": row[1],
                "name": row[2],
                "use_case": row[3],
                "plan_interest": row[4],
                "source_ip": row[5],
                "user_agent": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]

    with sqlite3.connect(WAITLIST_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, email, name, use_case, plan_interest, source_ip, user_agent, created_at
            FROM waitlist_signups
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def waitlist_summary() -> dict:
    using_postgres = WAITLIST_DATABASE_URL.startswith("postgresql://") or WAITLIST_DATABASE_URL.startswith("postgres://")
    if using_postgres:
        if psycopg is None:
            return {"total_signups": 0, "by_plan": {"pro": 0, "team": 0, "other": 0}}
        with psycopg.connect(WAITLIST_DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM waitlist_signups")
                total_signups = int(cur.fetchone()[0] or 0)
                cur.execute(
                    """
                    SELECT plan_interest, COUNT(*) AS c
                    FROM waitlist_signups
                    GROUP BY plan_interest
                    """
                )
                rows = cur.fetchall()
        by_plan = {"pro": 0, "team": 0, "other": 0}
        for plan_name, count in rows:
            key = str(plan_name or "other").strip().lower()
            if key not in by_plan:
                key = "other"
            by_plan[key] += int(count or 0)
        return {"total_signups": total_signups, "by_plan": by_plan}

    with sqlite3.connect(WAITLIST_DB_PATH) as conn:
        total_signups = int(conn.execute("SELECT COUNT(*) FROM waitlist_signups").fetchone()[0] or 0)
        rows = conn.execute(
            """
            SELECT plan_interest, COUNT(*) AS c
            FROM waitlist_signups
            GROUP BY plan_interest
            """
        ).fetchall()
    by_plan = {"pro": 0, "team": 0, "other": 0}
    for plan_name, count in rows:
        key = str(plan_name or "other").strip().lower()
        if key not in by_plan:
            key = "other"
        by_plan[key] += int(count or 0)
    return {"total_signups": total_signups, "by_plan": by_plan}


def is_admin_authorized() -> bool:
    if not WAITLIST_ADMIN_TOKEN:
        return True
    supplied = request.args.get("token", "").strip() or request.headers.get("X-Admin-Token", "").strip()
    return hmac.compare_digest(supplied, WAITLIST_ADMIN_TOKEN)


def validate_pdf_upload(field_name: str, allow_multiple: bool = False) -> list:
    if allow_multiple:
        files = [f for f in request.files.getlist(field_name) if f and f.filename]
    else:
        single = request.files.get(field_name)
        files = [single] if single and single.filename else []

    if not files:
        raise ValueError("Please upload at least one PDF file.")

    invalid = [f.filename for f in files if not f.filename.lower().endswith(".pdf")]
    if invalid:
        raise ValueError(f"Only .pdf files are allowed. Invalid: {', '.join(invalid)}")

    return files


def parse_ranges(range_text: str, total_pages: int) -> list[tuple[int, int]]:
    parts = [p.strip() for p in range_text.split(",") if p.strip()]
    if not parts:
        raise ValueError("No ranges provided.")

    output: list[tuple[int, int]] = []
    for part in parts:
        if "-" in part:
            left, right = part.split("-", 1)
            start = int(left)
            end = int(right)
        else:
            start = int(part)
            end = start

        if start < 1 or end < 1 or start > end or end > total_pages:
            raise ValueError(f"Invalid range '{part}'. Allowed pages: 1-{total_pages}.")
        output.append((start, end))

    return output


def expand_ranges(ranges: Iterable[tuple[int, int]]) -> set[int]:
    pages: set[int] = set()
    for start, end in ranges:
        pages.update(range(start, end + 1))
    return pages


def build_download_name(suffix: str, extension: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"pdfforge-{suffix}-{stamp}.{extension}"


init_waitlist_db()


@app.get("/")
def index() -> str:
    joined = request.args.get("joined", "")
    success = "You're in! We'll notify you when Pro beta opens." if joined == "1" else None
    info = request.args.get("info") or None
    error = request.args.get("error") or None
    return render_template_string(
        HTML,
        error=error,
        success=success,
        info=info,
        tool_cards=TOOL_CARDS,
        max_mb=app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
        plans=PRICING_PLANS,
        has_admin_token=bool(WAITLIST_ADMIN_TOKEN),
    )


@app.get("/health")
def health() -> Response:
    return jsonify({"status": "ok", "service": "pdfforge"})


@app.get("/api/v1/health")
def health_v1() -> Response:
    return jsonify({"status": "ok", "service": "pdfforge", "version": "v1"})


@app.get("/api/v1/tools")
def tools_v1() -> Response:
    return jsonify(
        {
            "tools": [
                {"id": "merge", "method": "POST", "path": "/merge"},
                {"id": "split", "method": "POST", "path": "/split"},
                {"id": "rotate", "method": "POST", "path": "/rotate"},
                {"id": "extract_text", "method": "POST", "path": "/extract-text"},
                {"id": "encrypt", "method": "POST", "path": "/encrypt"},
                {"id": "decrypt", "method": "POST", "path": "/decrypt"},
            ]
        }
    )


@app.get("/api/v1/metrics")
def metrics_v1() -> Response:
    summary = waitlist_summary()
    return jsonify(
        {
            "status": "ok",
            "service": "pdfforge",
            "metrics": {
                "total_signups": summary["total_signups"],
                "waitlist_by_plan": summary["by_plan"],
                "tool_count": len(TOOL_CARDS),
                "max_upload_mb": app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
                "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            },
        }
    )


@app.post("/waitlist")
def waitlist_signup() -> Response:
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    use_case = request.form.get("use_case", "").strip()
    plan_interest = request.form.get("plan_interest", "pro").strip().lower()
    source_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (request.remote_addr or "")
    user_agent = request.headers.get("User-Agent", "")

    ok, message = create_waitlist_signup(
        email=email,
        name=name,
        use_case=use_case,
        plan_interest=plan_interest,
        source_ip=source_ip,
        user_agent=user_agent,
    )
    if ok:
        return redirect(url_for("index", joined="1") + "#waitlist")
    if "already" in message.lower():
        return redirect(url_for("index", info=message) + "#waitlist")
    return redirect(url_for("index", error=message) + "#waitlist")


@app.post("/api/v1/waitlist")
def waitlist_signup_v1() -> Response:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    use_case = str(payload.get("use_case", "")).strip()
    plan_interest = str(payload.get("plan_interest", "pro")).strip().lower()
    source_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (request.remote_addr or "")
    user_agent = request.headers.get("User-Agent", "")

    ok, message = create_waitlist_signup(
        email=email,
        name=name,
        use_case=use_case,
        plan_interest=plan_interest,
        source_ip=source_ip,
        user_agent=user_agent,
    )
    if ok:
        return jsonify({"status": "ok", "message": message}), 201
    status_code = 409 if "already" in message.lower() else 400
    return jsonify({"status": "error", "message": message}), status_code


@app.get("/admin/waitlist")
def admin_waitlist() -> Response:
    if not is_admin_authorized():
        return Response(
            "Unauthorized. Provide WAITLIST_ADMIN_TOKEN via query (?token=...) or X-Admin-Token header.",
            status=401,
            mimetype="text/plain",
        )

    signups = read_waitlist_signups(limit=1000)
    admin_html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>PDFforge Waitlist Admin</title>
        <style>
          body { font-family: Inter, Segoe UI, Arial, sans-serif; margin: 24px; color: #111827; }
          h1 { margin-bottom: 6px; }
          .muted { color: #6b7280; margin-top: 0; }
          table { width: 100%; border-collapse: collapse; margin-top: 18px; }
          th, td { border: 1px solid #e5e7eb; padding: 8px; text-align: left; vertical-align: top; }
          th { background: #f9fafb; }
          code { background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }
        </style>
      </head>
      <body>
        <h1>Waitlist Signups</h1>
        <p class="muted">Total: {{ signups|length }}</p>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Created</th>
              <th>Email</th>
              <th>Name</th>
              <th>Plan</th>
              <th>Use Case</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            {% for row in signups %}
            <tr>
              <td>{{ row.id }}</td>
              <td><code>{{ row.created_at }}</code></td>
              <td>{{ row.email }}</td>
              <td>{{ row.name }}</td>
              <td>{{ row.plan_interest }}</td>
              <td>{{ row.use_case }}</td>
              <td>{{ row.source_ip }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </body>
    </html>
    """
    return Response(render_template_string(admin_html, signups=signups), mimetype="text/html")


@app.get("/api/v1/waitlist")
def waitlist_list_v1() -> Response:
    if not is_admin_authorized():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    return jsonify({"status": "ok", "items": read_waitlist_signups(limit=1000)})


@app.errorhandler(413)
def request_too_large(_: Exception) -> Response:
    max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return bad_request(f"File too large. Maximum upload size is {max_mb}MB.")


@app.post("/merge")
def merge() -> Response:
    try:
        files = validate_pdf_upload("files", allow_multiple=True)
        writer = PdfWriter()
        for file in files:
            reader = PdfReader(file.stream)
            for page in reader.pages:
                writer.add_page(page)

        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return send_file(
            out,
            as_attachment=True,
            download_name=build_download_name("merged", "pdf"),
            mimetype="application/pdf",
        )
    except Exception as exc:
        return bad_request(safe_error_message(exc))


@app.post("/split")
def split() -> Response:
    ranges_text = request.form.get("ranges", "").strip()
    if not ranges_text:
        return bad_request("Please provide page ranges.")

    try:
        file = validate_pdf_upload("file")[0]
        reader = PdfReader(file.stream)
        total = len(reader.pages)
        ranges = parse_ranges(ranges_text, total)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for idx, (start, end) in enumerate(ranges, start=1):
                writer = PdfWriter()
                for page_num in range(start - 1, end):
                    writer.add_page(reader.pages[page_num])
                pdf_bytes = io.BytesIO()
                writer.write(pdf_bytes)
                pdf_bytes.seek(0)
                archive.writestr(f"split_{idx}_{start}-{end}.pdf", pdf_bytes.read())

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=build_download_name("split", "zip"),
            mimetype="application/zip",
        )
    except Exception as exc:
        return bad_request(safe_error_message(exc))


@app.post("/rotate")
def rotate() -> Response:
    angle_text = request.form.get("angle", "90").strip()
    pages_text = request.form.get("pages", "").strip()
    try:
        angle = int(angle_text)
    except ValueError:
        return bad_request("Rotation angle must be 90, 180, or 270.")

    if angle not in (90, 180, 270):
        return bad_request("Rotation angle must be 90, 180, or 270.")

    try:
        file = validate_pdf_upload("file")[0]
        reader = PdfReader(file.stream)
        total = len(reader.pages)

        if pages_text:
            selected_pages = expand_ranges(parse_ranges(pages_text, total))
        else:
            selected_pages = set(range(1, total + 1))

        writer = PdfWriter()
        for i, page in enumerate(reader.pages, start=1):
            if i in selected_pages:
                page.rotate(angle)
            writer.add_page(page)

        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return send_file(
            out,
            as_attachment=True,
            download_name=build_download_name("rotated", "pdf"),
            mimetype="application/pdf",
        )
    except Exception as exc:
        return bad_request(safe_error_message(exc))


@app.post("/extract-text")
def extract_text() -> Response:
    try:
        file = validate_pdf_upload("file")[0]
        file_bytes = file.read()
        text_parts: list[str] = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                content = page.extract_text() or ""
                text_parts.append(f"--- Page {idx} ---\n{content}\n")

        out = io.BytesIO("\n".join(text_parts).encode("utf-8"))
        out.seek(0)
        return send_file(
            out,
            as_attachment=True,
            download_name=build_download_name("text", "txt"),
            mimetype="text/plain",
        )
    except Exception as exc:
        return bad_request(safe_error_message(exc))


@app.post("/encrypt")
def encrypt() -> Response:
    password = request.form.get("password", "").strip()
    if not password:
        return bad_request("Please provide a password.")

    try:
        file = validate_pdf_upload("file")[0]
        reader = PdfReader(file.stream)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)

        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return send_file(
            out,
            as_attachment=True,
            download_name=build_download_name("encrypted", "pdf"),
            mimetype="application/pdf",
        )
    except Exception as exc:
        return bad_request(safe_error_message(exc))


@app.post("/decrypt")
def decrypt() -> Response:
    password = request.form.get("password", "").strip()
    if not password:
        return bad_request("Please provide the current password.")

    try:
        file = validate_pdf_upload("file")[0]
        reader = PdfReader(file.stream)
        if not reader.is_encrypted:
            return bad_request("This PDF is not encrypted.")

        unlock_ok = reader.decrypt(password)
        if unlock_ok == 0:
            return bad_request("Incorrect password.")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return send_file(
            out,
            as_attachment=True,
            download_name=build_download_name("decrypted", "pdf"),
            mimetype="application/pdf",
        )
    except Exception as exc:
        return bad_request(safe_error_message(exc))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
