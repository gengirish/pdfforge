"""Thread-pool executor for async PDF job processing.

Wraps ``concurrent.futures.ThreadPoolExecutor`` and provides a simple
``submit_job`` helper that transitions job status through
queued → processing → done | failed.
"""

from __future__ import annotations

import logging
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from pdfforge_api.utils.job_store import update_manifest

logger = logging.getLogger(__name__)

_MAX_WORKERS = int(os.getenv("WORKER_THREADS", "4"))
_pool: ThreadPoolExecutor | None = None


def _get_pool() -> ThreadPoolExecutor:
    global _pool
    if _pool is None:
        _pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS, thread_name_prefix="pdfforge")
        logger.info("ThreadPoolExecutor started (max_workers=%d)", _MAX_WORKERS)
    return _pool


def submit_async_job(
    job_id: str,
    fn: Callable[..., dict[str, Any]],
    *args: Any,
    webhook_url: str | None = None,
    webhook_secret: str | None = None,
    **kwargs: Any,
) -> None:
    """Submit *fn* for background execution.

    *fn* must return a dict with at least ``output_bytes``, ``output_filename``,
    ``mimetype``, ``metadata``, and ``tool`` keys — identical to what
    ``create_job`` expects.  On success the manifest is updated to status=done;
    on failure it transitions to status=failed.
    """
    update_manifest(job_id, status="queued", progress=0)

    def _wrapper() -> None:
        try:
            update_manifest(job_id, status="processing", progress=10)
            result = fn(*args, **kwargs)
            from pdfforge_api.utils.job_store import _manifest_path, job_dir
            import json
            from datetime import datetime, timedelta, timezone
            from pdfforge_api.utils.job_store import JOB_RETENTION_HOURS

            d = job_dir(job_id)
            d.mkdir(parents=True, exist_ok=True)
            out_path = d / result["output_filename"]
            out_path.write_bytes(result["output_bytes"])

            now = datetime.now(timezone.utc)
            expires = now + timedelta(hours=JOB_RETENTION_HOURS)

            update_manifest(
                job_id,
                status="done",
                progress=100,
                output_url=f"/api/v1/jobs/{job_id}/download",
                output_filename=result["output_filename"],
                mimetype=result["mimetype"],
                metadata=result["metadata"],
                tool=result["tool"],
                expires_at=expires.isoformat(timespec="seconds"),
            )
            logger.info("Async job %s completed (tool=%s)", job_id, result["tool"])

            if webhook_url:
                _fire_webhook(job_id, webhook_url, webhook_secret, success=True)

        except Exception as exc:
            tb = traceback.format_exc()
            logger.error("Async job %s failed: %s\n%s", job_id, exc, tb)
            update_manifest(
                job_id,
                status="failed",
                progress=100,
                error={"type": "/errors/processing-failed", "detail": str(exc)},
            )
            if webhook_url:
                _fire_webhook(job_id, webhook_url, webhook_secret, success=False, error_detail=str(exc))

    _get_pool().submit(_wrapper)


def _fire_webhook(
    job_id: str,
    webhook_url: str,
    webhook_secret: str | None,
    success: bool,
    error_detail: str | None = None,
) -> None:
    """Best-effort webhook delivery after job completion."""
    try:
        from pdfforge_api.utils.job_store import read_manifest
        from pdfforge_api.utils.webhook import send_webhook

        manifest = read_manifest(job_id) or {}
        event = "job.completed" if success else "job.failed"
        payload = {
            "event": event,
            "job_id": job_id,
            "tool": manifest.get("tool", ""),
            "status": manifest.get("status", "failed"),
            "output_url": manifest.get("output_url", ""),
            "metadata": manifest.get("metadata", {}),
            "error": manifest.get("error") if not success else None,
            "timestamp": manifest.get("updated_at", ""),
        }
        send_webhook(webhook_url, webhook_secret or "", payload)
    except Exception:
        logger.exception("Failed to fire webhook for job %s", job_id)
