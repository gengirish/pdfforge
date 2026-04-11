"""Webhook delivery with HMAC-SHA256 signing and exponential-backoff retries."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

_MAX_RETRIES = int(os.getenv("WEBHOOK_MAX_RETRIES", "3"))
_BACKOFF_BASE = [1, 3, 9]


def _sign_payload(secret: str, body: bytes) -> str:
    """Compute ``sha256=<hex>`` HMAC signature."""
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _deliver(url: str, secret: str, payload: dict[str, Any]) -> None:
    """Blocking delivery with retries.  Runs in a background thread."""
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

    body = json.dumps(payload).encode("utf-8")
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if secret:
        headers["X-PDFforge-Signature"] = _sign_payload(secret, body)

    for attempt in range(_MAX_RETRIES):
        try:
            req = Request(url, data=body, method="POST", headers=headers)
            with urlopen(req, timeout=10) as resp:
                status = resp.status
            logger.info(
                "Webhook delivered to %s (attempt %d, status=%d, event=%s)",
                url, attempt + 1, status, payload.get("event"),
            )
            return
        except (HTTPError, URLError, OSError) as exc:
            wait = _BACKOFF_BASE[attempt] if attempt < len(_BACKOFF_BASE) else _BACKOFF_BASE[-1]
            logger.warning(
                "Webhook attempt %d/%d to %s failed (%s), retrying in %ds",
                attempt + 1, _MAX_RETRIES, url, exc, wait,
            )
            time.sleep(wait)

    logger.error("Webhook delivery to %s exhausted %d retries", url, _MAX_RETRIES)


def send_webhook(url: str, secret: str, payload: dict[str, Any]) -> None:
    """Fire-and-forget webhook delivery in a background daemon thread."""
    t = threading.Thread(target=_deliver, args=(url, secret, payload), daemon=True)
    t.start()
