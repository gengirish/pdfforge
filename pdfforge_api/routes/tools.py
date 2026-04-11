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
from pdfforge_api.utils.job_store import create_job, new_job_id
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


# ── Tool routes ────────────────────────────────────────────────────────────

@tools_bp.post("/merge")
@require_api_key
def merge_v1():
    _record_usage("merge")
    t0 = time.monotonic()
    try:
        files = _validate_pdf_upload("files", allow_multiple=True)
    except ValueError as exc:
        return missing_file_error(str(exc))

    try:
        writer = PdfWriter()
        for f in files:
            reader = PdfReader(f.stream)
            for page in reader.pages:
                writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        out_bytes = buf.getvalue()
        elapsed = int((time.monotonic() - t0) * 1000)
        fname = _build_download_name("merged", "pdf")
        return _envelope_or_download(
            tool="merge",
            output_bytes=out_bytes,
            filename=fname,
            mimetype="application/pdf",
            metadata={
                "pages": len(writer.pages),
                "size_bytes": len(out_bytes),
                "processing_ms": elapsed,
                "filename": fname,
            },
        )
    except Exception:
        return processing_failed_error()


@tools_bp.post("/split")
@require_api_key
def split_v1():
    _record_usage("split")
    t0 = time.monotonic()

    ranges_text = request.form.get("ranges", "").strip()
    if not ranges_text:
        return missing_file_error("Please provide page ranges.")

    try:
        files = _validate_pdf_upload("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    try:
        reader = PdfReader(files[0].stream)
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

        out_bytes = zip_buf.getvalue()
        elapsed = int((time.monotonic() - t0) * 1000)
        fname = _build_download_name("split", "zip")
        return _envelope_or_download(
            tool="split",
            output_bytes=out_bytes,
            filename=fname,
            mimetype="application/zip",
            metadata={
                "pages": total,
                "size_bytes": len(out_bytes),
                "processing_ms": elapsed,
                "filename": fname,
            },
        )
    except ValueError as exc:
        return missing_file_error(str(exc))
    except Exception:
        return processing_failed_error()


@tools_bp.post("/rotate")
@require_api_key
def rotate_v1():
    _record_usage("rotate")
    t0 = time.monotonic()

    angle_text = request.form.get("angle", "90").strip()
    pages_text = request.form.get("pages", "").strip()
    try:
        angle = int(angle_text)
    except ValueError:
        return unsupported_format_error("Rotation angle must be 90, 180, or 270.")

    if angle not in (90, 180, 270):
        return unsupported_format_error("Rotation angle must be 90, 180, or 270.")

    try:
        files = _validate_pdf_upload("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    try:
        reader = PdfReader(files[0].stream)
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
        out_bytes = buf.getvalue()
        elapsed = int((time.monotonic() - t0) * 1000)
        fname = _build_download_name("rotated", "pdf")
        return _envelope_or_download(
            tool="rotate",
            output_bytes=out_bytes,
            filename=fname,
            mimetype="application/pdf",
            metadata={
                "pages": total,
                "size_bytes": len(out_bytes),
                "processing_ms": elapsed,
                "filename": fname,
            },
        )
    except ValueError as exc:
        return missing_file_error(str(exc))
    except Exception:
        return processing_failed_error()


@tools_bp.post("/extract_text")
@require_api_key
def extract_text_v1():
    _record_usage("extract_text")
    t0 = time.monotonic()

    try:
        files = _validate_pdf_upload("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    try:
        file_bytes = files[0].read()
        text_parts: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                content = page.extract_text() or ""
                text_parts.append(f"--- Page {idx} ---\n{content}\n")

        out_bytes = "\n".join(text_parts).encode("utf-8")
        elapsed = int((time.monotonic() - t0) * 1000)
        fname = _build_download_name("text", "txt")
        return _envelope_or_download(
            tool="extract_text",
            output_bytes=out_bytes,
            filename=fname,
            mimetype="text/plain",
            metadata={
                "pages": len(text_parts),
                "size_bytes": len(out_bytes),
                "processing_ms": elapsed,
                "filename": fname,
            },
        )
    except Exception:
        return processing_failed_error()


@tools_bp.post("/encrypt")
@require_api_key
def encrypt_v1():
    _record_usage("encrypt")
    t0 = time.monotonic()

    password = request.form.get("password", "").strip()
    if not password:
        return invalid_password_error("Please provide a password.")

    try:
        files = _validate_pdf_upload("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    try:
        reader = PdfReader(files[0].stream)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)

        buf = io.BytesIO()
        writer.write(buf)
        out_bytes = buf.getvalue()
        elapsed = int((time.monotonic() - t0) * 1000)
        fname = _build_download_name("encrypted", "pdf")
        return _envelope_or_download(
            tool="encrypt",
            output_bytes=out_bytes,
            filename=fname,
            mimetype="application/pdf",
            metadata={
                "pages": len(reader.pages),
                "size_bytes": len(out_bytes),
                "processing_ms": elapsed,
                "filename": fname,
            },
        )
    except Exception:
        return processing_failed_error()


@tools_bp.post("/decrypt")
@require_api_key
def decrypt_v1():
    _record_usage("decrypt")
    t0 = time.monotonic()

    password = request.form.get("password", "").strip()
    if not password:
        return invalid_password_error("Please provide the current password.")

    try:
        files = _validate_pdf_upload("file")
    except ValueError as exc:
        return missing_file_error(str(exc))

    try:
        reader = PdfReader(files[0].stream)
        if not reader.is_encrypted:
            return unsupported_format_error("This PDF is not encrypted.")

        unlock_ok = reader.decrypt(password)
        if unlock_ok == 0:
            return invalid_password_error("Incorrect password.")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        out_bytes = buf.getvalue()
        elapsed = int((time.monotonic() - t0) * 1000)
        fname = _build_download_name("decrypted", "pdf")
        return _envelope_or_download(
            tool="decrypt",
            output_bytes=out_bytes,
            filename=fname,
            mimetype="application/pdf",
            metadata={
                "pages": len(reader.pages),
                "size_bytes": len(out_bytes),
                "processing_ms": elapsed,
                "filename": fname,
            },
        )
    except Exception:
        return processing_failed_error()
