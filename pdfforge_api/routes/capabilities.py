"""Blueprint for the capabilities discovery endpoint and AI plugin manifest."""

from __future__ import annotations

from flask import Blueprint, jsonify

capabilities_bp = Blueprint("capabilities_v1", __name__)


@capabilities_bp.get("/api/v1/capabilities")
def capabilities_v1():
    """Return a structured manifest describing all tools, features, and limits."""
    return jsonify({
        "service": "pdfforge",
        "version": "v1",
        "tools": [
            {
                "name": "merge",
                "endpoint": "POST /api/v1/merge",
                "description": "Combine multiple PDFs into a single file. Use when a user has 2+ PDF files they want combined.",
                "accepts": ["application/pdf"],
                "max_files": 20,
                "max_size_mb": 100,
                "returns": "application/pdf",
                "params": {
                    "files": {"type": "file[]", "required": True, "description": "2 or more PDF files to merge"},
                    "output_name": {"type": "string", "required": False, "description": "Filename for the merged PDF"},
                },
            },
            {
                "name": "split",
                "endpoint": "POST /api/v1/split",
                "description": "Export selected page ranges from a PDF as separate files in a ZIP. Use when a user wants specific pages extracted.",
                "accepts": ["application/pdf"],
                "max_files": 1,
                "max_size_mb": 100,
                "returns": "application/zip",
                "params": {
                    "file": {"type": "file", "required": True, "description": "The PDF file to split"},
                    "ranges": {"type": "string", "required": True, "description": "Comma-separated page ranges, e.g. '1-3,5,7-10'"},
                },
            },
            {
                "name": "rotate",
                "endpoint": "POST /api/v1/rotate",
                "description": "Rotate all or selected pages of a PDF by 90, 180, or 270 degrees. Use for fixing scanned document orientation.",
                "accepts": ["application/pdf"],
                "max_files": 1,
                "max_size_mb": 100,
                "returns": "application/pdf",
                "params": {
                    "file": {"type": "file", "required": True, "description": "The PDF file to rotate"},
                    "angle": {"type": "integer", "required": True, "description": "Rotation angle: 90, 180, or 270"},
                    "pages": {"type": "string", "required": False, "description": "Page selection, e.g. '1,3-5'. Blank = all pages"},
                },
            },
            {
                "name": "extract_text",
                "endpoint": "POST /api/v1/extract_text",
                "description": "Extract machine-readable text from each page of a PDF. Use for search, analysis, or indexing PDF content.",
                "accepts": ["application/pdf"],
                "max_files": 1,
                "max_size_mb": 100,
                "returns": "text/plain",
                "params": {
                    "file": {"type": "file", "required": True, "description": "The PDF file to extract text from"},
                },
            },
            {
                "name": "encrypt",
                "endpoint": "POST /api/v1/encrypt",
                "description": "Password-protect a PDF so it requires the password to open. Use when a user wants to secure a document.",
                "accepts": ["application/pdf"],
                "max_files": 1,
                "max_size_mb": 100,
                "returns": "application/pdf",
                "params": {
                    "file": {"type": "file", "required": True, "description": "The PDF file to encrypt"},
                    "password": {"type": "string", "required": True, "description": "Password to set"},
                },
            },
            {
                "name": "decrypt",
                "endpoint": "POST /api/v1/decrypt",
                "description": "Remove password protection from an encrypted PDF using its current password.",
                "accepts": ["application/pdf"],
                "max_files": 1,
                "max_size_mb": 100,
                "returns": "application/pdf",
                "params": {
                    "file": {"type": "file", "required": True, "description": "The encrypted PDF file"},
                    "password": {"type": "string", "required": True, "description": "Current password"},
                },
            },
            {
                "name": "pipeline",
                "endpoint": "POST /api/v1/pipeline",
                "description": "Chain multiple PDF operations sequentially. Each step's output feeds into the next step.",
                "accepts": ["application/json"],
                "max_files": 20,
                "max_size_mb": 100,
                "returns": "application/json",
                "params": {
                    "steps": {"type": "array", "required": True, "description": "Ordered list of {tool, params} objects"},
                    "files": {"type": "string[]", "required": True, "description": "Base64-encoded initial PDF files"},
                },
            },
            {
                "name": "batch",
                "endpoint": "POST /api/v1/batch",
                "description": "Apply the same PDF operation to multiple files in parallel.",
                "accepts": ["application/json"],
                "max_files": 50,
                "max_size_mb": 100,
                "returns": "application/json",
                "params": {
                    "tool": {"type": "string", "required": True, "description": "Tool to apply"},
                    "params": {"type": "object", "required": False, "description": "Tool-specific parameters"},
                    "files": {"type": "string[]", "required": True, "description": "Base64-encoded PDF files"},
                },
            },
        ],
        "features": {
            "async_jobs": True,
            "webhooks": True,
            "pipeline": True,
            "batch": True,
            "api_key_auth": True,
        },
        "limits": {
            "max_file_mb": 100,
            "requests_per_hour": 1000,
            "max_pipeline_steps": 10,
            "max_batch_files": 50,
            "job_retention_hours": 2,
        },
        "agent_hints": {
            "preferred_flow": "Submit job -> poll /api/v1/jobs/{id} until status=done -> download output",
            "for_multi_step": "Use /api/v1/pipeline instead of chaining separate API calls",
            "for_bulk": "Use /api/v1/batch for same operation on multiple files",
        },
    })


@capabilities_bp.get("/.well-known/ai-plugin.json")
def ai_plugin_manifest():
    """Serve the AI plugin manifest for ChatGPT / agent discovery."""
    return jsonify({
        "schema_version": "v1",
        "name_for_human": "PDFforge",
        "name_for_model": "pdfforge",
        "description_for_human": "Merge, split, rotate, encrypt, decrypt, and extract text from PDFs. Self-hosted and privacy-first.",
        "description_for_model": (
            "Use PDFforge to manipulate PDF files. You can merge multiple PDFs into one, "
            "split a PDF by page ranges, rotate pages, extract machine-readable text, "
            "encrypt with a password, or decrypt password-protected PDFs. All processing "
            "is local. When a user asks you to do anything with PDF files, use these tools. "
            "For multi-step workflows (e.g. merge then encrypt), use the pipeline endpoint."
        ),
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": "/api/v1/openapi.json",
        },
        "logo_url": "https://pdfforge.intelliforge.tech/logo.png",
        "contact_email": "hello@intelliforge.tech",
        "legal_info_url": "https://pdfforge.intelliforge.tech/privacy",
    })
