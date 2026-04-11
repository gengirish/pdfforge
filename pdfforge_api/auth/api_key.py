"""API key authentication decorator for PDFforge endpoints.

When ``API_KEY_REQUIRED`` env var is set to ``true``, every decorated
endpoint requires a valid ``Authorization: Bearer <key>`` header.
Valid keys come from the ``API_KEYS`` env var (comma-separated).

When ``API_KEY_REQUIRED`` is unset or ``false``, auth is skipped
entirely (open self-hosted mode).
"""

from __future__ import annotations

import functools
import os
from typing import Any, Callable

from flask import g, jsonify, request

from pdfforge_api.utils.response import error_response

_API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "false").strip().lower() == "true"
_VALID_KEYS: set[str] = set()

if _API_KEY_REQUIRED:
    raw = os.getenv("API_KEYS", "")
    _VALID_KEYS = {k.strip() for k in raw.split(",") if k.strip()}


def require_api_key(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Flask route decorator that enforces API key auth when enabled."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not _API_KEY_REQUIRED:
            g.api_key = None
            return fn(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "").strip()
        if not auth_header.startswith("Bearer "):
            body, status = error_response(
                type_slug="/errors/unauthorized",
                title="Unauthorized",
                status=401,
                detail="Missing or malformed Authorization header. Expected: Bearer <api_key>",
            )
            return jsonify(body), status

        token = auth_header[7:].strip()
        if token not in _VALID_KEYS:
            body, status = error_response(
                type_slug="/errors/unauthorized",
                title="Unauthorized",
                status=401,
                detail="Invalid API key.",
            )
            return jsonify(body), status

        g.api_key = token
        return fn(*args, **kwargs)

    return wrapper
