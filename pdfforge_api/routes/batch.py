"""Blueprint for batch processing — same operation on multiple files.

POST /api/v1/batch  — submit a batch
GET  /api/v1/batch/<batch_id> — aggregate status
"""

from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request

from pdfforge_api.auth.api_key import require_api_key
from pdfforge_api.utils.async_executor import submit_async_job
from pdfforge_api.utils.job_store import (
    JOB_DIR,
    create_async_job,
    new_job_id,
    read_manifest,
)
from pdfforge_api.utils.response import error_response

batch_bp = Blueprint("batch_v1", __name__, url_prefix="/api/v1")

_BATCH_DIR = JOB_DIR / "_batches"


def _batch_manifest_path(batch_id: str) -> Path:
    return _BATCH_DIR / f"{batch_id}.json"


def _save_batch(batch_id: str, data: dict[str, Any]) -> None:
    _BATCH_DIR.mkdir(parents=True, exist_ok=True)
    _batch_manifest_path(batch_id).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_batch(batch_id: str) -> dict[str, Any] | None:
    p = _batch_manifest_path(batch_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _get_tool_fn(name: str):
    """Lazy-import tool processing functions."""
    from pdfforge_api.routes.tools import (
        _do_decrypt,
        _do_encrypt,
        _do_extract_text,
        _do_merge,
        _do_rotate,
        _do_split,
    )
    fns = {
        "merge": _do_merge,
        "split": _do_split,
        "rotate": _do_rotate,
        "extract_text": _do_extract_text,
        "encrypt": _do_encrypt,
        "decrypt": _do_decrypt,
    }
    return fns.get(name)


def _make_single_job_fn(tool: str, params: dict, file_data: bytes):
    """Build a callable that processes one file with the given tool + params."""
    fn = _get_tool_fn(tool)
    if fn is None:
        raise ValueError(f"Unknown tool: {tool}")

    def _run() -> dict[str, Any]:
        if tool == "merge":
            return fn([("input.pdf", file_data)])
        elif tool == "split":
            ranges = params.get("ranges", "")
            if isinstance(ranges, list):
                ranges = ",".join(f"{r[0]}-{r[1]}" if len(r) == 2 else str(r[0]) for r in ranges)
            return fn(file_data, ranges)
        elif tool == "rotate":
            degrees = int(params.get("degrees", 90))
            pages = params.get("pages", "")
            if isinstance(pages, list):
                pages = ",".join(str(p) for p in pages)
            return fn(file_data, degrees, str(pages))
        elif tool == "extract_text":
            return fn(file_data)
        elif tool == "encrypt":
            return fn(file_data, params.get("password", ""))
        elif tool == "decrypt":
            return fn(file_data, params.get("password", ""))
        else:
            raise ValueError(f"Unsupported tool: {tool}")

    return _run


@batch_bp.post("/batch")
@require_api_key
def batch_submit():
    body = request.get_json(silent=True) or {}
    tool = body.get("tool", "").strip()
    params = body.get("params", {})
    files_b64 = body.get("files", [])
    want_async = body.get("async", True)
    webhook_url = body.get("webhook_url") or None
    webhook_secret = body.get("webhook_secret") or None

    if not tool or _get_tool_fn(tool) is None:
        return error_response(
            type_slug="/errors/missing-file",
            title="Invalid tool",
            status=400,
            detail=f"Unknown tool '{tool}'. Must be one of: merge, split, rotate, extract_text, encrypt, decrypt.",
        )
    if not files_b64 or not isinstance(files_b64, list):
        return error_response(
            type_slug="/errors/missing-file",
            title="Missing files",
            status=400,
            detail="'files' must be a non-empty array of base64-encoded PDFs.",
        )
    if len(files_b64) > 50:
        return error_response(
            type_slug="/errors/file-too-large",
            title="Too many files",
            status=400,
            detail="Batch is limited to 50 files.",
        )

    try:
        decoded = [base64.b64decode(f) for f in files_b64]
    except Exception:
        return error_response(
            type_slug="/errors/unsupported-format",
            title="Invalid files",
            status=400,
            detail="All files must be valid base64-encoded data.",
        )

    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    jobs: list[dict] = []

    for idx, file_data in enumerate(decoded):
        job_id = new_job_id()
        job_fn = _make_single_job_fn(tool, params, file_data)
        submit_async_job(job_id, job_fn, webhook_url=webhook_url, webhook_secret=webhook_secret)
        create_async_job(job_id=job_id, tool=tool)
        jobs.append({"file_index": idx, "job_id": job_id, "status": "queued"})

    batch_manifest = {
        "batch_id": batch_id,
        "total_files": len(decoded),
        "tool": tool,
        "jobs": jobs,
    }
    _save_batch(batch_id, batch_manifest)

    return jsonify(batch_manifest), 202


@batch_bp.get("/batch/<batch_id>")
@require_api_key
def batch_status(batch_id: str):
    batch = _load_batch(batch_id)
    if batch is None:
        return error_response(
            type_slug="/errors/job-not-found",
            title="Batch not found",
            status=404,
            detail=f"No batch with id '{batch_id}' exists.",
        )

    for entry in batch.get("jobs", []):
        manifest = read_manifest(entry["job_id"])
        if manifest:
            entry["status"] = manifest.get("status", entry["status"])

    done = sum(1 for j in batch["jobs"] if j["status"] in ("done", "failed"))
    batch["completed"] = done
    batch["all_done"] = done == batch["total_files"]

    return jsonify(batch), 200
