"""Blueprint for the AI agent intent-interpretation endpoint.

POST /api/v1/agent/interpret uses the Anthropic API (Claude) to convert
natural-language instructions into a structured pipeline plan, and
optionally executes it.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from flask import Blueprint, jsonify, request

from pdfforge_api.auth.api_key import require_api_key
from pdfforge_api.utils.response import error_response

logger = logging.getLogger(__name__)

agent_bp = Blueprint("agent_v1", __name__, url_prefix="/api/v1/agent")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()

_SYSTEM_PROMPT = """You are a PDF workflow planner. Given a user's natural language intent and a list \
of available PDF tools (merge, split, rotate, extract_text, encrypt, decrypt), \
output ONLY a JSON object with this structure:
{
  "steps": [
    { "tool": "<tool_name>", "params": { ... } }
  ],
  "reasoning": "<brief explanation of the plan>"
}
Available params per tool:
- merge: output_name (optional string)
- split: ranges (array of [start, end] page number pairs)
- rotate: degrees (90|180|270), pages ('all' or array of page numbers)
- extract_text: pages ('all' or array of page numbers)
- encrypt: password (string)
- decrypt: password (string)
Output only valid JSON. No markdown, no explanation outside the JSON."""


@agent_bp.post("/interpret")
@require_api_key
def interpret():
    """Convert a natural-language PDF intent into a pipeline plan."""
    if not ANTHROPIC_API_KEY:
        return error_response(
            type_slug="/errors/processing-failed",
            title="Not Implemented",
            status=501,
            detail="ANTHROPIC_API_KEY environment variable is not set. Set it to enable AI intent interpretation.",
        )

    body = request.get_json(silent=True) or {}
    intent = str(body.get("intent", "")).strip()
    files_b64 = body.get("files", [])
    execute = bool(body.get("execute", False))
    want_async = bool(body.get("async", False))

    if not intent:
        return error_response(
            type_slug="/errors/missing-file",
            title="Missing intent",
            status=400,
            detail="'intent' field is required.",
        )

    try:
        plan = _call_claude(intent)
    except Exception as exc:
        logger.exception("Claude API call failed: %s", exc)
        return error_response(
            type_slug="/errors/processing-failed",
            title="AI interpretation failed",
            status=502,
            detail=str(exc),
        )

    result: dict[str, Any] = {
        "interpreted_plan": plan,
        "executed": False,
    }

    if execute and files_b64 and plan.get("steps"):
        try:
            from pdfforge_api.routes.pipeline import _run_pipeline, _decode_files
            from pdfforge_api.utils.job_store import create_job, new_job_id
            from pdfforge_api.utils.response import success_response

            initial_files = _decode_files(files_b64)
            pipeline_result = _run_pipeline(plan["steps"], initial_files)

            job_id = new_job_id()
            manifest = create_job(
                job_id=job_id,
                tool="agent_pipeline",
                output_filename=pipeline_result["output_filename"],
                output_bytes=pipeline_result["output_bytes"],
                mimetype=pipeline_result["mimetype"],
                metadata=pipeline_result["metadata"],
            )
            result["executed"] = True
            result["job"] = success_response(
                job_id=job_id,
                tool="agent_pipeline",
                output_url=manifest["output_url"],
                metadata=pipeline_result["metadata"],
                expires_at=manifest["expires_at"],
            )
            if "pipeline" in pipeline_result:
                result["job"]["pipeline"] = pipeline_result["pipeline"]
        except Exception as exc:
            logger.exception("Pipeline execution failed: %s", exc)
            result["execution_error"] = str(exc)

    return jsonify(result), 200


def _call_claude(intent: str) -> dict[str, Any]:
    """Call the Anthropic Messages API and parse the JSON response."""
    from urllib.request import Request, urlopen

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "system": _SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": intent}],
    }).encode("utf-8")

    req = Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        method="POST",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )

    with urlopen(req, timeout=30) as resp:
        resp_body = json.loads(resp.read().decode("utf-8"))

    text_block = ""
    for block in resp_body.get("content", []):
        if block.get("type") == "text":
            text_block += block.get("text", "")

    text_block = text_block.strip()
    if text_block.startswith("```"):
        lines = text_block.split("\n")
        text_block = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return json.loads(text_block)
