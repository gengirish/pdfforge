"""Simple in-memory per-key rate limiter that resets every hour."""

from __future__ import annotations

import math
import os
import threading
import time
import uuid
from typing import Any

from flask import Response, request

_lock = threading.Lock()
_buckets: dict[str, list[float]] = {}

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "1000"))


def _current_hour_boundary() -> float:
    """Return the Unix timestamp of the start of the current UTC hour."""
    now = time.time()
    return now - (now % 3600)


def _next_hour_boundary() -> int:
    """Return the Unix timestamp when the current hour window resets."""
    return int(_current_hour_boundary() + 3600)


def _prune_old(entries: list[float], window_start: float) -> list[float]:
    return [t for t in entries if t >= window_start]


def check_rate_limit(key: str) -> tuple[int, int, int]:
    """Record a request and return (limit, remaining, reset_unix).

    Raises no exception — the caller decides whether to reject.
    """
    window_start = _current_hour_boundary()
    reset_ts = _next_hour_boundary()

    with _lock:
        entries = _buckets.get(key, [])
        entries = _prune_old(entries, window_start)
        entries.append(time.time())
        _buckets[key] = entries
        used = len(entries)

    remaining = max(0, RATE_LIMIT - used)
    return RATE_LIMIT, remaining, reset_ts


def rate_limit_key() -> str:
    """Derive the rate-limit bucket key from the current request.

    Uses the API key (attached to ``flask.g`` by the auth decorator)
    or falls back to the client IP address.
    """
    from flask import g
    return getattr(g, "api_key", None) or (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
        or "unknown"
    )


def inject_rate_limit_headers(response: Response) -> Response:
    """After-request hook that adds rate-limit and request-id headers."""
    key = rate_limit_key()
    limit, remaining, reset_ts = check_rate_limit(key)

    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_ts)
    response.headers.setdefault("X-Request-Id", uuid.uuid4().hex)
    return response
