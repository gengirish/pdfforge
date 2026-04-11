"""Blueprint for multi-step pipeline chaining — POST /api/v1/pipeline.

Accepts a JSON body with ordered steps and initial files (base64),
runs them sequentially, and returns a single job result.
"""

from __future__ import annotations

import base64
import io
import time
from typing import Any

from flask import Blueprint, jsonify, request

from pdfforge_api.auth.api_key import require_api_key
from pdfforge_api.utils.async_executor import submit_async_job
from pdfforge_api.utils.job_store import create_async_job, create_job, new_job_id
from pdfforge_api.utils.response import error_response, success_response

pipeline_bp = Blueprint("pipeline_v1", __name__, url_prefix="/api/v1")

_TOOL_FNS: dict[str, Any] = {}


def _get_tool_fn(name: str):
    """Lazy-import tool functions to avoid circular imports."""
    if not _TOOL_FNS:
        from pdfforge_api.routes.tools import (
            _do_decrypt,
            _do_encrypt,
            _do_extract_text,
            _do_merge,
            _do_rotate,
            _do_split,
        )
        _TOOL_FNS.update({
            "merge": _do_merge,
            "split": _do_split,
            "rotate": _do_rotate,
            "extract_text": _do_extract_text,
            "encrypt": _do_encrypt,
            "decrypt": _do_decrypt,
        })
    return _TOOL_FNS.get(name)


def _decode_files(encoded: list[str]) -> list[bytes]:
    """Decode base64-encoded file strings."""
    result: list[bytes] = []
    for item in encoded:
        if isinstance(item, str):
            result.append(base64.b64decode(item))
        else:
            raise ValueError("Each file must be a base64-encoded string.")
    return result


def _run_pipeline(steps: list[dict], initial_files: list[bytes]) -> dict[str, Any]:
    """Execute pipeline steps sequentially, passing output as next input."""
    current_data = initial_files
    step_results: list[dict] = []

    for i, step in enumerate(steps):
        tool_name = step.get("tool", "")
        params = step.get("params", {})
        fn = _get_tool_fn(tool_name)
        if fn is None:
            raise ValueError(f"Step {i + 1}: unknown tool '{tool_name}'")

        t0 = time.monotonic()
        try:
            if tool_name == "merge":
                file_pairs = [(f"input_{j}.pdf", d) for j, d in enumerate(current_data)]
                result = fn(file_pairs)
            elif tool_name == "split":
                ranges_text = params.get("ranges", "")
                if isinstance(ranges_text, list):
                    ranges_text = ",".join(f"{r[0]}-{r[1]}" if len(r) == 2 else str(r[0]) for r in ranges_text)
                result = fn(current_data[0], ranges_text)
            elif tool_name == "rotate":
                degrees = int(params.get("degrees", 90))
                pages = params.get("pages", "")
                if isinstance(pages, list):
                    pages = ",".join(str(p) for p in pages)
                result = fn(current_data[0], degrees, str(pages))
            elif tool_name == "extract_text":
                result = fn(current_data[0])
            elif tool_name == "encrypt":
                result = fn(current_data[0], params.get("password", ""))
            elif tool_name == "decrypt":
                result = fn(current_data[0], params.get("password", ""))
            else:
                raise ValueError(f"Unsupported tool: {tool_name}")
        except Exception as exc:
            raise ValueError(f"Step {i + 1} ({tool_name}) failed: {exc}") from exc

        elapsed = int((time.monotonic() - t0) * 1000)
        step_results.append({"step": i + 1, "tool": tool_name, "duration_ms": elapsed})
        current_data = [result["output_bytes"]]

    last = result  # type: ignore[possibly-undefined]
    last["metadata"]["processing_ms"] = sum(s["duration_ms"] for s in step_results)
    return {
        **last,
        "pipeline": {
            "total_steps": len(steps),
            "completed_steps": len(step_results),
            "step_results": step_results,
        },
    }


@pipeline_bp.post("/pipeline")
@require_api_key
def pipeline_v1():
    body = request.get_json(silent=True) or {}
    steps = body.get("steps")
    files_b64 = body.get("files", [])
    want_async = body.get("async", False)
    webhook_url = body.get("webhook_url") or None
    webhook_secret = body.get("webhook_secret") or None

    if not steps or not isinstance(steps, list):
        return error_response(
            type_slug="/errors/missing-file",
            title="Invalid pipeline",
            status=400,
            detail="'steps' must be a non-empty array of {tool, params} objects.",
        )
    if len(steps) > 10:
        return error_response(
            type_slug="/errors/file-too-large",
            title="Too many steps",
            status=400,
            detail="Pipeline is limited to 10 steps.",
        )
    if not files_b64 or not isinstance(files_b64, list):
        return error_response(
            type_slug="/errors/missing-file",
            title="Missing files",
            status=400,
            detail="'files' must be a non-empty array of base64-encoded PDFs.",
        )

    try:
        initial_files = _decode_files(files_b64)
    except Exception as exc:
        return error_response(
            type_slug="/errors/unsupported-format",
            title="Invalid files",
            status=400,
            detail=str(exc),
        )

    job_id = new_job_id()

    if want_async:
        def _run():
            return _run_pipeline(steps, initial_files)
        submit_async_job(job_id, _run, webhook_url=webhook_url, webhook_secret=webhook_secret)
        create_async_job(job_id=job_id, tool="pipeline")
        return jsonify({"job_id": job_id, "status": "queued", "poll_url": f"/api/v1/jobs/{job_id}"}), 202

    try:
        result = _run_pipeline(steps, initial_files)
    except ValueError as exc:
        return error_response(
            type_slug="/errors/processing-failed",
            title="Pipeline failed",
            status=400,
            detail=str(exc),
        )
    except Exception:
        return error_response(
            type_slug="/errors/processing-failed",
            title="Pipeline failed",
            status=500,
            detail="An unexpected error occurred.",
        )

    manifest = create_job(
        job_id=job_id,
        tool="pipeline",
        output_filename=result["output_filename"],
        output_bytes=result["output_bytes"],
        mimetype=result["mimetype"],
        metadata=result["metadata"],
    )
    body_out = success_response(
        job_id=job_id,
        tool="pipeline",
        output_url=manifest["output_url"],
        metadata=result["metadata"],
        expires_at=manifest["expires_at"],
    )
    body_out["pipeline"] = result["pipeline"]
    return jsonify(body_out), 200
