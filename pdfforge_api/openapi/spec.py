"""Generate the full OpenAPI 3.1 specification for the PDFforge API."""

from __future__ import annotations

from typing import Any


def _error_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "type": {"type": "string", "example": "/errors/missing-file"},
            "title": {"type": "string", "example": "Missing file"},
            "status": {"type": "integer", "example": 400},
            "detail": {"type": "string"},
            "job_id": {"type": ["string", "null"]},
        },
        "required": ["success", "type", "title", "status", "detail"],
    }


def _metadata_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "pages": {"type": "integer"},
            "size_bytes": {"type": "integer"},
            "processing_ms": {"type": "integer"},
            "filename": {"type": "string"},
        },
    }


def _success_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "job_id": {"type": "string", "example": "job_a1b2c3d4e5f6"},
            "tool": {"type": "string"},
            "output_url": {"type": "string", "example": "/api/v1/jobs/job_a1b2c3d4e5f6/download"},
            "metadata": _metadata_schema(),
            "expires_at": {"type": "string", "format": "date-time"},
        },
        "required": ["success", "job_id", "tool", "output_url", "metadata", "expires_at"],
    }


def _job_manifest_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "job_id": {"type": "string"},
            "status": {"type": "string", "enum": ["queued", "processing", "done", "failed"]},
            "tool": {"type": "string"},
            "output_url": {"type": "string"},
            "output_filename": {"type": "string"},
            "mimetype": {"type": "string"},
            "metadata": _metadata_schema(),
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"},
            "expires_at": {"type": "string", "format": "date-time"},
            "error": {"type": ["object", "null"]},
        },
    }


def _tool_endpoint(
    *,
    tool_name: str,
    summary: str,
    description: str,
    file_field: str = "file",
    multiple: bool = False,
    extra_fields: list[dict] | None = None,
) -> dict[str, Any]:
    """Build the POST path item for a single PDF tool."""
    fields: list[dict] = []
    if multiple:
        fields.append({
            "name": file_field,
            "in": "formData",
            "schema": {"type": "array", "items": {"type": "string", "format": "binary"}},
            "required": True,
            "description": "One or more PDF files.",
        })
    else:
        fields.append({
            "name": file_field,
            "in": "formData",
            "schema": {"type": "string", "format": "binary"},
            "required": True,
            "description": "The PDF file to process.",
        })
    if extra_fields:
        fields.extend(extra_fields)

    properties: dict[str, Any] = {}
    required_fields: list[str] = []
    for f in fields:
        prop: dict[str, Any] = dict(f.get("schema", {"type": "string"}))
        if f.get("description"):
            prop["description"] = f["description"]
        properties[f["name"]] = prop
        if f.get("required"):
            required_fields.append(f["name"])

    return {
        "post": {
            "tags": ["PDF Tools"],
            "summary": summary,
            "description": description,
            "operationId": tool_name,
            "parameters": [
                {
                    "name": "download",
                    "in": "query",
                    "schema": {"type": "boolean", "default": False},
                    "description": "Set to true to receive the raw output file instead of the JSON envelope.",
                },
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "properties": properties,
                            "required": required_fields,
                        },
                    },
                },
            },
            "responses": {
                "200": {
                    "description": "Job completed successfully.",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/SuccessEnvelope"}},
                    },
                },
                "400": {
                    "description": "Bad request — missing or invalid input.",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/ErrorEnvelope"}},
                    },
                },
                "401": {"description": "Unauthorized — invalid or missing API key."},
                "500": {"description": "Processing failed."},
            },
        },
    }


def build_openapi_spec() -> dict[str, Any]:
    """Return the full OpenAPI 3.1.0 spec as a Python dict."""
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "PDFforge API",
            "version": "1.0.0",
            "description": (
                "Open-source, privacy-first PDF toolkit API by IntelliForge AI. "
                "Merge, split, rotate, extract text, encrypt, and decrypt PDFs "
                "via simple REST calls. Self-host or use the hosted service."
            ),
            "contact": {"email": "hello@intelliforge.tech"},
            "license": {"name": "MIT"},
        },
        "servers": [
            {"url": "https://pdfforge-api.fly.dev", "description": "Production"},
            {"url": "http://localhost:5050", "description": "Local development"},
        ],
        "tags": [
            {"name": "PDF Tools", "description": "Core PDF processing operations."},
            {"name": "Jobs", "description": "Retrieve, download, or delete job results."},
            {"name": "System", "description": "Health, metrics, and capability endpoints."},
        ],
        "paths": {
            "/api/v1/merge": _tool_endpoint(
                tool_name="merge",
                summary="Merge multiple PDFs into one",
                description=(
                    "Combine 2 or more PDF files into a single document. "
                    "Upload multiple files under the 'files' field. "
                    "Use this when a user has several PDFs they want combined into one file."
                ),
                file_field="files",
                multiple=True,
            ),
            "/api/v1/split": _tool_endpoint(
                tool_name="split",
                summary="Split a PDF by page ranges",
                description=(
                    "Export selected page ranges from a PDF as separate files (returned in a ZIP). "
                    "Use when a user wants to extract specific pages or ranges like '1-3,5,7-10'."
                ),
                extra_fields=[{
                    "name": "ranges",
                    "schema": {"type": "string"},
                    "required": True,
                    "description": "Comma-separated page ranges, e.g. '1-3,5,7-10'. 1-based.",
                }],
            ),
            "/api/v1/rotate": _tool_endpoint(
                tool_name="rotate",
                summary="Rotate PDF pages",
                description=(
                    "Rotate all or selected pages of a PDF by 90, 180, or 270 degrees. "
                    "Use when a user has a PDF with pages in the wrong orientation."
                ),
                extra_fields=[
                    {
                        "name": "angle",
                        "schema": {"type": "integer", "enum": [90, 180, 270]},
                        "required": True,
                        "description": "Rotation angle in degrees (90, 180, or 270).",
                    },
                    {
                        "name": "pages",
                        "schema": {"type": "string"},
                        "required": False,
                        "description": "Optional page selection, e.g. '1,3-5'. Blank = all pages.",
                    },
                ],
            ),
            "/api/v1/extract_text": _tool_endpoint(
                tool_name="extract_text",
                summary="Extract text from a PDF",
                description=(
                    "Extract machine-readable text from every page of a PDF and return as a .txt file. "
                    "Use when a user needs the text content of a PDF for search, analysis, or indexing."
                ),
            ),
            "/api/v1/encrypt": _tool_endpoint(
                tool_name="encrypt",
                summary="Password-protect a PDF",
                description=(
                    "Encrypt a PDF with a user-supplied password so it requires the password to open. "
                    "Use when a user wants to secure a PDF before sharing it."
                ),
                extra_fields=[{
                    "name": "password",
                    "schema": {"type": "string"},
                    "required": True,
                    "description": "The password to set on the PDF.",
                }],
            ),
            "/api/v1/decrypt": _tool_endpoint(
                tool_name="decrypt",
                summary="Remove password from a PDF",
                description=(
                    "Decrypt a password-protected PDF using the current password and produce an unlocked copy. "
                    "Use when a user has the password for an encrypted PDF and wants to remove the protection."
                ),
                extra_fields=[{
                    "name": "password",
                    "schema": {"type": "string"},
                    "required": True,
                    "description": "The current password of the encrypted PDF.",
                }],
            ),
            # ── Job endpoints ──
            "/api/v1/jobs/{job_id}": {
                "get": {
                    "tags": ["Jobs"],
                    "summary": "Get job status and metadata",
                    "description": "Retrieve the full manifest for a job. Returns 404 if the job does not exist or 410 if it has expired.",
                    "operationId": "getJob",
                    "parameters": [
                        {"name": "job_id", "in": "path", "required": True, "schema": {"type": "string"}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Job manifest.",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/JobManifest"}}},
                        },
                        "404": {"description": "Job not found."},
                        "410": {"description": "Job expired."},
                    },
                },
                "delete": {
                    "tags": ["Jobs"],
                    "summary": "Delete a job early",
                    "operationId": "deleteJob",
                    "parameters": [
                        {"name": "job_id", "in": "path", "required": True, "schema": {"type": "string"}},
                    ],
                    "responses": {
                        "204": {"description": "Job deleted."},
                        "404": {"description": "Job not found."},
                    },
                },
            },
            "/api/v1/jobs/{job_id}/download": {
                "get": {
                    "tags": ["Jobs"],
                    "summary": "Download job output file",
                    "description": "Download the processed output file for a completed job.",
                    "operationId": "downloadJob",
                    "parameters": [
                        {"name": "job_id", "in": "path", "required": True, "schema": {"type": "string"}},
                    ],
                    "responses": {
                        "200": {
                            "description": "The output file.",
                            "content": {"application/pdf": {}, "application/zip": {}, "text/plain": {}},
                        },
                        "404": {"description": "Job not found."},
                        "410": {"description": "Job expired."},
                    },
                },
            },
            # ── System ──
            "/api/v1/health": {
                "get": {
                    "tags": ["System"],
                    "summary": "Health check",
                    "operationId": "healthCheck",
                    "responses": {
                        "200": {
                            "description": "Service healthy.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "ok"},
                                            "service": {"type": "string", "example": "pdfforge"},
                                            "version": {"type": "string", "example": "v1"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "components": {
            "schemas": {
                "SuccessEnvelope": _success_schema(),
                "ErrorEnvelope": _error_schema(),
                "Metadata": _metadata_schema(),
                "JobManifest": _job_manifest_schema(),
            },
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "API key passed as Bearer token. Only enforced when API_KEY_REQUIRED=true.",
                },
            },
        },
        "security": [{"BearerAuth": []}],
    }
