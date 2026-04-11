"""Blueprint for the six PDF tool endpoints under ``/api/v1/``.

Each tool returns a JSON envelope by default.  Passing ``?download=true``
returns the raw file directly for backward compatibility.
"""

from __future__ import annotations

import io
import time
import zipfile
from typing import Any

import pdfplumber
from flask import Blueprint, jsonify, request, send_file
from pypdf import PdfReader, PdfWriter

from pdfforge_api.auth.api_key import require_api_key
from pdfforge_api.utils.async_executor import submit_async_job
from pdfforge_api.utils.job_store import create_async_job, create_job, new_job_id
from pdfforge_api.utils.response import (
    invalid_password_error,
    missing_file_error,
    processing_failed_error,
    success_response,
    unsupported_format_error,
)

tools_bp = Blueprint("tools_v1", __name__, url_prefix="/api/v1")


# ── Shared helpers ─────────────────────────────────────────────────────────

def _wants_download() -> bool:
    return request.args.get("download", "").lower() in ("true", "1", "yes")


def _validate_pdf_upload(field: str, *, allow_multiple: bool = False) -> list:
    """Return uploaded file(s) or raise ``ValueError``."""
    if allow_multiple:
        files = [f for f in request.files.getlist(field) if f and f.filename]
    else:
        single = request.files.get(field)
        files = [single] if single and single.filename else []

    if not files:
        raise ValueError("Please upload at least one PDF file.")

    invalid = [f.filename for f in files if not f.filename.lower().endswith(".pdf")]
    if invalid:
        raise ValueError(f"Only .pdf files are allowed. Invalid: {', '.join(invalid)}")
    return files


def _build_download_name(suffix: str, ext: str) -> str:
    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"pdfforge-{suffix}-{stamp}.{ext}"


def _envelope_or_download(
    *,
    tool: str,
    output_bytes: bytes,
    filename: str,
    mimetype: str,
    metadata: dict[str, Any],
):
    """If ``?download=true`` stream the file; otherwise persist as a job and return JSON."""
    if _wants_download():
        return send_file(
            io.BytesIO(output_bytes),
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype,
        )

    job_id = new_job_id()
    manifest = create_job(
        job_id=job_id,
        tool=tool,
        output_filename=filename,
        output_bytes=output_bytes,
        mimetype=mimetype,
        metadata=metadata,
    )
    body = success_response(
        job_id=job_id,
        tool=tool,
        output_url=manifest["output_url"],
        metadata=metadata,
        expires_at=manifest["expires_at"],
    )
    return jsonify(body), 200


def _record_usage(tool_id: str) -> None:
    """Best-effort import of the legacy usage counter."""
    try:
        import app as _app_mod
        _app_mod.record_tool_usage(tool_id)
    except Exception:
        pass


def _wants_async() -> bool:
    return (
        request.headers.get("X-Async", "").lower() in ("true", "1")
        or request.args.get("async", "").lower() in ("true", "1", "yes")
    )


def _read_files_to_memory(field: str, *, allow_multiple: bool = False) -> list[tuple[str, bytes]]:
    """Read uploaded files into memory so they survive beyond the request context."""
    if allow_multiple:
        uploads = [f for f in request.files.getlist(field) if f and f.filename]
    else:
        single = request.files.get(field)
        uploads = [single] if single and single.filename else []

    if not uploads:
        raise ValueError("Please upload at least one PDF file.")

    invalid = [f.filename for f in uploads if not f.filename.lower().endswith(".pdf")]
    if invalid:
        raise ValueError(f"Only .pdf files are allowed. Invalid: {', '.join(invalid)}")

    return [(f.filename, f.read()) for f in uploads]


# ── Sync processing functions (also used by async executor) ───────────────

def _do_merge(file_pairs: list[tuple[str, bytes]]) -> dict[str, Any]:
    writer = PdfWriter()
    for _name, data in file_pairs:
        reader = PdfReader(io.BytesIO(data))
        for page in reader.pages:
            writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    out = buf.getvalue()
    fname = _build_download_name("merged", "pdf")
    return {
        "tool": "merge",
        "output_bytes": out,
        "output_filename": fname,
        "mimetype": "application/pdf",
        "metadata": {"pages": len(writer.pages), "size_bytes": len(out), "processing_ms": 0, "filename": fname},
    }


def _do_split(file_data: bytes, ranges_text: str) -> dict[str, Any]:
    reader = PdfReader(io.BytesIO(file_data))
    total = len(reader.pages)
    from app import parse_ranges
    ranges = parse_ranges(ranges_text, total)
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as archive:
        for idx, (start, end) in enumerate(ranges, start=1):
            w = PdfWriter()
            for p in range(start - 1, end):
                w.add_page(reader.pages[p])
            pdf_bytes = io.BytesIO()
            w.write(pdf_bytes)
            pdf_bytes.seek(0)
            archive.writestr(f"split_{idx}_{start}-{end}.pdf", pdf_bytes.read())
    out = zip_buf.getvalue()
    fname = _build_download_name("split", "zip")
    return {
        "tool": "split",
        "output_bytes": out,
        "output_filename": fname,
        "mimetype": "application/zip",
        "metadata": {"pages": total, "size_bytes": len(out), "processing_ms": 0, "filename": fname},
    }


def _do_rotate(file_data: bytes, angle: int, pages_text: str) -> dict[str, Any]:
    reader = PdfReader(io.BytesIO(file_data))
    total = len(reader.pages)
    if pages_text:
        from app import parse_ranges, expand_ranges
        selected = expand_ranges(parse_ranges(pages_text, total))
    else:
        selected = set(range(1, total + 1))
    writer = PdfWriter()
    for i, page in enumerate(reader.pages, start=1):
        if i in selected:
            page.rotate(angle)
        writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    out = buf.getvalue()
    fname = _build_download_name("rotated", "pdf")
    return {
        "tool": "rotate",
        "output_bytes": out,
        "output_filename": fname,
        "mimetype": "application/pdf",
        "metadata": {"pages": total, "size_bytes": len(out), "processing_ms": 0, "filename": fname},
    }


def _do_extract_text(file_data: bytes) -> dict[str, Any]:
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_data)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            content = page.extract_text() or ""
            text_parts.append(f"--- Page {idx} ---\n{content}\n")
    out = "\n".join(text_parts).encode("utf-8")
    fname = _build_download_name("text", "txt")
    return {
        "tool": "extract_text",
        "output_bytes": out,
        "output_filename": fname,
        "mimetype": "text/plain",
        "metadata": {"pages": len(text_parts), "size_bytes": len(out), "processing_ms": 0, "filename": fname},
    }


def _do_encrypt(file_data: bytes, password: str) -> dict[str, Any]:
    reader = PdfReader(io.BytesIO(file_data))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    buf = io.BytesIO()
    writer.write(buf)
    out = buf.getvalue()
    fname = _build_download_name("encrypted", "pdf")
    return {
        "tool": "encrypt",
        "output_bytes": out,
        "output_filename": fname,
        "mimetype": "application/pdf",
        "metadata": {"pages": len(reader.pages), "size_bytes": len(out), "processing_ms": 0, "filename": fname},
    }


def _do_decrypt(file_data: bytes, password: str) -> dict[str, Any]:
    reader = PdfReader(io.BytesIO(file_data))
    if not reader.is_encrypted:
        raise ValueError("NOT_ENCRYPTED")
    unlock_ok = reader.decrypt(password)
    if unlock_ok == 0:
        raise ValueError("BAD_PASSWORD")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    out = buf.getvalue()
    fname = _build_download_name("decrypted", "pdf")
    return {
        "tool": "decrypt",
        "output_bytes": out,
        "output_filename": fname,
        "mimetype": "application/pdf",
        "metadata": {"pages": len(reader.pages), "size_bytes": len(out), "processing_ms": 0, "filename": fname},
    }


def _async_response(job_id: str, tool: str):
    """Return the 202 queued envelope for an async job."""
    manifest = create_async_job(job_id=job_id, tool=tool)
    return jsonify({
        "job_id": job_id,
        "status": "queued",
        "poll_url": f"/api/v1/jobs/{job_id}",
    }), 202


# ── Tool routes ────────────────────────────────────────────────────────────

@tools_bp.post("/merge")
@require_api_key
def merge_v1():
    _record_usage("merge")
    webhook_url = request.form.get("webhook_url", "").strip() or None
    webhook_secret = request.form.get("webhook_secret", "").strip() or None
    try:
        file_pairs = _read_files_to_memory("files", allow_multiple=True)
    except ValueError as exc:
        return missing_file_error(str(exc))

    if _wants_async():
        job_id = new_job_id()
        submit_async_job(job_id, _do_merge, file_pairs, webhook_url=webhook_url, webhook_secret=webhook_secret)
        return _async_response(job_id, "merge")

    t0 = time.monotonic()
    try:
        result = _do_merge(file_pairs)
        result["metadata"]["processing_ms"] = int((time.monotonic() - t0) * 1000)
        return _envelope_or_download(tool="merge", output_bytes=result["output_bytes"], filename=result["output_filename"], mimetype=result["mimetype"], metadata=result["metadata"])
    except Exception:
        return processing_failed_error()


@tools_bp.post("/split")
@require_api_key
def split_v1():
    _record_usage("split")
    webhook_url = request.form.get("webhook_url", "").strip() or None
    webhook_secret = request.form.get("webhook_secret", "").strip() or None
    ranges_text = request.form.get("ranges", "").strip()
    if not ranges_text:
        return missing_file_error("Please provide page ranges.")

    try:
        file_pairs = _read_files_to_memory("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    if _wants_async():
        job_id = new_job_id()
        submit_async_job(job_id, _do_split, file_pairs[0][1], ranges_text, webhook_url=webhook_url, webhook_secret=webhook_secret)
        return _async_response(job_id, "split")

    t0 = time.monotonic()
    try:
        result = _do_split(file_pairs[0][1], ranges_text)
        result["metadata"]["processing_ms"] = int((time.monotonic() - t0) * 1000)
        return _envelope_or_download(tool="split", output_bytes=result["output_bytes"], filename=result["output_filename"], mimetype=result["mimetype"], metadata=result["metadata"])
    except ValueError as exc:
        return missing_file_error(str(exc))
    except Exception:
        return processing_failed_error()


@tools_bp.post("/rotate")
@require_api_key
def rotate_v1():
    _record_usage("rotate")
    webhook_url = request.form.get("webhook_url", "").strip() or None
    webhook_secret = request.form.get("webhook_secret", "").strip() or None
    angle_text = request.form.get("angle", "90").strip()
    pages_text = request.form.get("pages", "").strip()
    try:
        angle = int(angle_text)
    except ValueError:
        return unsupported_format_error("Rotation angle must be 90, 180, or 270.")
    if angle not in (90, 180, 270):
        return unsupported_format_error("Rotation angle must be 90, 180, or 270.")

    try:
        file_pairs = _read_files_to_memory("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    if _wants_async():
        job_id = new_job_id()
        submit_async_job(job_id, _do_rotate, file_pairs[0][1], angle, pages_text, webhook_url=webhook_url, webhook_secret=webhook_secret)
        return _async_response(job_id, "rotate")

    t0 = time.monotonic()
    try:
        result = _do_rotate(file_pairs[0][1], angle, pages_text)
        result["metadata"]["processing_ms"] = int((time.monotonic() - t0) * 1000)
        return _envelope_or_download(tool="rotate", output_bytes=result["output_bytes"], filename=result["output_filename"], mimetype=result["mimetype"], metadata=result["metadata"])
    except ValueError as exc:
        return missing_file_error(str(exc))
    except Exception:
        return processing_failed_error()


@tools_bp.post("/extract_text")
@require_api_key
def extract_text_v1():
    _record_usage("extract_text")
    webhook_url = request.form.get("webhook_url", "").strip() or None
    webhook_secret = request.form.get("webhook_secret", "").strip() or None
    try:
        file_pairs = _read_files_to_memory("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    if _wants_async():
        job_id = new_job_id()
        submit_async_job(job_id, _do_extract_text, file_pairs[0][1], webhook_url=webhook_url, webhook_secret=webhook_secret)
        return _async_response(job_id, "extract_text")

    t0 = time.monotonic()
    try:
        result = _do_extract_text(file_pairs[0][1])
        result["metadata"]["processing_ms"] = int((time.monotonic() - t0) * 1000)
        return _envelope_or_download(tool="extract_text", output_bytes=result["output_bytes"], filename=result["output_filename"], mimetype=result["mimetype"], metadata=result["metadata"])
    except Exception:
        return processing_failed_error()


@tools_bp.post("/encrypt")
@require_api_key
def encrypt_v1():
    _record_usage("encrypt")
    webhook_url = request.form.get("webhook_url", "").strip() or None
    webhook_secret = request.form.get("webhook_secret", "").strip() or None
    password = request.form.get("password", "").strip()
    if not password:
        return invalid_password_error("Please provide a password.")

    try:
        file_pairs = _read_files_to_memory("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    if _wants_async():
        job_id = new_job_id()
        submit_async_job(job_id, _do_encrypt, file_pairs[0][1], password, webhook_url=webhook_url, webhook_secret=webhook_secret)
        return _async_response(job_id, "encrypt")

    t0 = time.monotonic()
    try:
        result = _do_encrypt(file_pairs[0][1], password)
        result["metadata"]["processing_ms"] = int((time.monotonic() - t0) * 1000)
        return _envelope_or_download(tool="encrypt", output_bytes=result["output_bytes"], filename=result["output_filename"], mimetype=result["mimetype"], metadata=result["metadata"])
    except Exception:
        return processing_failed_error()


@tools_bp.post("/decrypt")
@require_api_key
def decrypt_v1():
    _record_usage("decrypt")
    webhook_url = request.form.get("webhook_url", "").strip() or None
    webhook_secret = request.form.get("webhook_secret", "").strip() or None
    password = request.form.get("password", "").strip()
    if not password:
        return invalid_password_error("Please provide the current password.")

    try:
        file_pairs = _read_files_to_memory("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    if _wants_async():
        job_id = new_job_id()
        submit_async_job(job_id, _do_decrypt, file_pairs[0][1], password, webhook_url=webhook_url, webhook_secret=webhook_secret)
        return _async_response(job_id, "decrypt")

    t0 = time.monotonic()
    try:
        result = _do_decrypt(file_pairs[0][1], password)
        result["metadata"]["processing_ms"] = int((time.monotonic() - t0) * 1000)
        return _envelope_or_download(tool="decrypt", output_bytes=result["output_bytes"], filename=result["output_filename"], mimetype=result["mimetype"], metadata=result["metadata"])
    except ValueError as exc:
        msg = str(exc)
        if msg == "NOT_ENCRYPTED":
            return unsupported_format_error("This PDF is not encrypted.")
        if msg == "BAD_PASSWORD":
            return invalid_password_error("Incorrect password.")
        return missing_file_error(msg)
    except Exception:
        return processing_failed_error()
