---
name: flask-api-patterns
description: Production-grade Flask API patterns for file processing backends. Use when building REST APIs with Flask that handle file uploads, database persistence (SQLite/PostgreSQL), CORS, admin auth, error handling, and deployment with gunicorn.
---

# Flask API Patterns

## App Structure

```python
from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=False)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB
```

## Versioned API Routes

```python
@app.get("/api/v1/health")
def health_v1():
    return jsonify({"status": "ok", "service": "myapp", "version": "v1"})

@app.get("/api/v1/metrics")
def metrics_v1():
    return jsonify({"status": "ok", "metrics": {...}})
```

## File Upload Validation

```python
def validate_pdf_upload(field_name, allow_multiple=False):
    if allow_multiple:
        files = [f for f in request.files.getlist(field_name) if f and f.filename]
    else:
        single = request.files.get(field_name)
        files = [single] if single and single.filename else []
    if not files:
        raise ValueError("Please upload at least one file.")
    invalid = [f.filename for f in files if not f.filename.lower().endswith(".pdf")]
    if invalid:
        raise ValueError(f"Only .pdf files allowed. Invalid: {', '.join(invalid)}")
    return files
```

## Safe Error Messages

Never expose internal errors to users:

```python
def safe_error_message(exc):
    safe_types = (ValueError, zipfile.BadZipFile)
    if isinstance(exc, safe_types):
        return str(exc)
    app.logger.exception("Unexpected error")
    return "An error occurred. Please check the file and try again."
```

## Admin Authentication (Token-Based)

```python
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

def is_admin_authorized():
    if not ADMIN_TOKEN:
        return True  # No token = dev mode
    supplied = request.args.get("token", "") or request.headers.get("X-Admin-Token", "")
    return hmac.compare_digest(supplied, ADMIN_TOKEN)
```

## Dual Database Support (SQLite + PostgreSQL)

```python
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

def _using_postgres():
    return DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

def init_db():
    if _using_postgres():
        with psycopg.connect(DATABASE_URL) as conn:
            # CREATE TABLE IF NOT EXISTS ...
    else:
        with sqlite3.connect(DB_PATH) as conn:
            # CREATE TABLE IF NOT EXISTS ...
```

## File Response Pattern

```python
@app.post("/merge")
def merge():
    try:
        files = validate_pdf_upload("files", allow_multiple=True)
        # ... process files ...
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return send_file(out, as_attachment=True,
                        download_name="output.pdf",
                        mimetype="application/pdf")
    except Exception as exc:
        return Response(safe_error_message(exc), status=400, mimetype="text/plain")
```

## CORS Configuration

```python
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=False)
```

## Security Headers (via Next.js proxy or Flask)

```python
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

## Gunicorn Production Config

```bash
gunicorn app:app --bind 0.0.0.0:8080 --workers 2 --timeout 120 --access-logfile -
```

## Dockerfile Pattern

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN mkdir -p /app/data && chown appuser:appgroup /app/data
USER appuser
ENV PORT=8080
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]
```

## Request Size Handling

```python
@app.errorhandler(413)
def request_too_large(_):
    max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return Response(f"File too large. Max size: {max_mb}MB.", status=400)
```
