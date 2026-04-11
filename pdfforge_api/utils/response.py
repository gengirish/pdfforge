"""Standardized JSON response envelope helpers following RFC 7807 for errors."""

from __future__ import annotations

from typing import Any


def success_response(
    *,
    job_id: str,
    tool: str,
    output_url: str,
    metadata: dict[str, Any],
    expires_at: str,
) -> dict[str, Any]:
    """Build the standard success envelope returned by all tool endpoints."""
    return {
        "success": True,
        "job_id": job_id,
        "tool": tool,
        "output_url": output_url,
        "metadata": metadata,
        "expires_at": expires_at,
    }


def error_response(
    *,
    type_slug: str,
    title: str,
    status: int,
    detail: str,
    job_id: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Build an RFC 7807 problem-detail error response.

    Returns ``(body_dict, http_status)`` so callers can do
    ``return jsonify(*error_response(...))``.
    """
    return (
        {
            "success": False,
            "type": type_slug,
            "title": title,
            "status": status,
            "detail": detail,
            "job_id": job_id,
        },
        status,
    )


# ── Predefined error factories ────────────────────────────────────────────

def missing_file_error(detail: str = "No PDF file was included in the request.") -> tuple[dict, int]:
    return error_response(
        type_slug="/errors/missing-file",
        title="Missing file",
        status=400,
        detail=detail,
    )


def invalid_password_error(detail: str = "The supplied password is incorrect or missing.") -> tuple[dict, int]:
    return error_response(
        type_slug="/errors/invalid-password",
        title="Invalid password",
        status=400,
        detail=detail,
    )


def unsupported_format_error(detail: str = "Only .pdf files are accepted.") -> tuple[dict, int]:
    return error_response(
        type_slug="/errors/unsupported-format",
        title="Unsupported format",
        status=400,
        detail=detail,
    )


def file_too_large_error(max_mb: int) -> tuple[dict, int]:
    return error_response(
        type_slug="/errors/file-too-large",
        title="File too large",
        status=413,
        detail=f"Upload exceeds the {max_mb} MB limit.",
    )


def processing_failed_error(detail: str = "An error occurred while processing the PDF.") -> tuple[dict, int]:
    return error_response(
        type_slug="/errors/processing-failed",
        title="Processing failed",
        status=500,
        detail=detail,
    )


def job_not_found_error(job_id: str) -> tuple[dict, int]:
    return error_response(
        type_slug="/errors/job-not-found",
        title="Job not found",
        status=404,
        detail=f"No job with id '{job_id}' exists.",
        job_id=job_id,
    )


def expired_job_error(job_id: str) -> tuple[dict, int]:
    return error_response(
        type_slug="/errors/expired-job",
        title="Job expired",
        status=410,
        detail=f"Job '{job_id}' has expired and its output has been deleted.",
        job_id=job_id,
    )
