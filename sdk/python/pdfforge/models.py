"""Data models for PDFforge SDK responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class JobResult:
    """Represents the result of a single PDF tool invocation."""

    job_id: str
    status: str
    tool: str
    output_url: str
    metadata: dict[str, Any] = field(default_factory=dict)
    expires_at: datetime | None = None
    error: dict[str, Any] | None = None

    # internal ref to the client for .download()
    _client: Any = field(default=None, repr=False)

    def download(self, output_path: str | Path) -> Path:
        """Download the job output to *output_path* and return the Path."""
        if self._client is None:
            raise RuntimeError("JobResult is detached — no client reference for download.")
        return self._client.download_job(self.job_id, output_path)

    def is_done(self) -> bool:
        """Return ``True`` if the job completed successfully."""
        return self.status == "done"

    def is_failed(self) -> bool:
        """Return ``True`` if the job ended with a failure."""
        return self.status == "failed"

    @classmethod
    def from_dict(cls, data: dict[str, Any], client: Any = None) -> "JobResult":
        """Construct a ``JobResult`` from an API response dict."""
        expires = None
        raw = data.get("expires_at")
        if raw:
            try:
                expires = datetime.fromisoformat(str(raw))
            except (ValueError, TypeError):
                pass
        return cls(
            job_id=data.get("job_id", ""),
            status=data.get("status", "unknown"),
            tool=data.get("tool", ""),
            output_url=data.get("output_url", ""),
            metadata=data.get("metadata", {}),
            expires_at=expires,
            error=data.get("error"),
            _client=client,
        )


@dataclass
class PipelineResult(JobResult):
    """Extended result that includes per-step pipeline timing."""

    pipeline: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], client: Any = None) -> "PipelineResult":
        """Construct from API response."""
        base = JobResult.from_dict(data, client)
        return cls(
            job_id=base.job_id,
            status=base.status,
            tool=base.tool,
            output_url=base.output_url,
            metadata=base.metadata,
            expires_at=base.expires_at,
            error=base.error,
            _client=client,
            pipeline=data.get("pipeline", {}),
        )


@dataclass
class BatchResult:
    """Represents the result of a batch submission."""

    batch_id: str
    total_files: int
    tool: str
    jobs: list[dict[str, Any]] = field(default_factory=list)

    _client: Any = field(default=None, repr=False)

    def refresh(self) -> "BatchResult":
        """Re-fetch batch status from the API."""
        if self._client is None:
            raise RuntimeError("BatchResult is detached.")
        return self._client.get_batch(self.batch_id)

    @property
    def all_done(self) -> bool:
        return all(j.get("status") in ("done", "failed") for j in self.jobs)

    @classmethod
    def from_dict(cls, data: dict[str, Any], client: Any = None) -> "BatchResult":
        return cls(
            batch_id=data.get("batch_id", ""),
            total_files=data.get("total_files", 0),
            tool=data.get("tool", ""),
            jobs=data.get("jobs", []),
            _client=client,
        )
