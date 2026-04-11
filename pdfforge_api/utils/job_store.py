"""Temporary job output storage backed by the local filesystem.

Jobs are stored under ``JOB_DIR/<job_id>/`` with a ``manifest.json``
and the actual output file.  A background cleanup thread removes jobs
older than ``JOB_RETENTION_HOURS``.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

JOB_DIR = Path(os.getenv("JOB_DIR", "/tmp/pdfforge_jobs"))
JOB_RETENTION_HOURS = int(os.getenv("JOB_RETENTION_HOURS", "2"))
_CLEANUP_INTERVAL = 15 * 60  # 15 minutes


def _ensure_dir() -> None:
    JOB_DIR.mkdir(parents=True, exist_ok=True)


def new_job_id() -> str:
    return f"job_{uuid.uuid4().hex[:12]}"


def job_dir(job_id: str) -> Path:
    return JOB_DIR / job_id


def _manifest_path(job_id: str) -> Path:
    return job_dir(job_id) / "manifest.json"


def create_job(
    *,
    job_id: str,
    tool: str,
    status: str = "done",
    output_filename: str,
    output_bytes: bytes,
    mimetype: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Persist a completed job's output file and manifest to disk."""
    _ensure_dir()
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)

    out_path = d / output_filename
    out_path.write_bytes(output_bytes)

    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=JOB_RETENTION_HOURS)

    manifest: dict[str, Any] = {
        "job_id": job_id,
        "status": status,
        "tool": tool,
        "output_url": f"/api/v1/jobs/{job_id}/download",
        "output_filename": output_filename,
        "mimetype": mimetype,
        "metadata": metadata,
        "created_at": now.isoformat(timespec="seconds"),
        "updated_at": now.isoformat(timespec="seconds"),
        "expires_at": expires.isoformat(timespec="seconds"),
        "error": None,
    }
    _manifest_path(job_id).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def read_manifest(job_id: str) -> dict[str, Any] | None:
    """Load the manifest for *job_id*, or ``None`` if missing."""
    p = _manifest_path(job_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def output_file_path(job_id: str) -> Path | None:
    """Return the ``Path`` to the output file, or ``None``."""
    manifest = read_manifest(job_id)
    if manifest is None:
        return None
    p = job_dir(job_id) / manifest["output_filename"]
    return p if p.exists() else None


def delete_job(job_id: str) -> bool:
    """Remove job directory.  Returns ``True`` if it existed."""
    d = job_dir(job_id)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
        return True
    return False


def is_expired(manifest: dict[str, Any]) -> bool:
    try:
        exp = datetime.fromisoformat(manifest["expires_at"])
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > exp
    except (KeyError, ValueError):
        return True


# ── Background cleanup ────────────────────────────────────────────────────

def _cleanup_expired_jobs() -> None:
    """Delete all job directories whose manifest has expired."""
    if not JOB_DIR.exists():
        return
    removed = 0
    for entry in JOB_DIR.iterdir():
        if not entry.is_dir():
            continue
        manifest = read_manifest(entry.name)
        if manifest is None or is_expired(manifest):
            shutil.rmtree(entry, ignore_errors=True)
            removed += 1
    if removed:
        logger.info("Job cleanup: removed %d expired job(s)", removed)


_cleanup_timer: threading.Timer | None = None


def _schedule_cleanup() -> None:
    global _cleanup_timer
    try:
        _cleanup_expired_jobs()
    except Exception:
        logger.exception("Job cleanup failed")
    _cleanup_timer = threading.Timer(_CLEANUP_INTERVAL, _schedule_cleanup)
    _cleanup_timer.daemon = True
    _cleanup_timer.start()


def start_cleanup_thread() -> None:
    """Start the periodic cleanup thread (safe to call multiple times)."""
    global _cleanup_timer
    if _cleanup_timer is not None:
        return
    _cleanup_timer = threading.Timer(_CLEANUP_INTERVAL, _schedule_cleanup)
    _cleanup_timer.daemon = True
    _cleanup_timer.start()
    logger.info(
        "Job cleanup thread started (interval=%ds, retention=%dh)",
        _CLEANUP_INTERVAL,
        JOB_RETENTION_HOURS,
    )
