"""Main PDFforge client for interacting with the PDFforge REST API."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from pdfforge.exceptions import AuthError, JobFailedError, PDFForgeError, RateLimitError
from pdfforge.models import BatchResult, JobResult, PipelineResult
from pdfforge.utils.file_utils import read_file_bytes, to_base64


class PDFForge:
    """Synchronous client for the PDFforge API.

    Args:
        api_key: Optional Bearer token for authenticated requests.
        base_url: Base URL of the PDFforge API server.
        timeout: Default request timeout in seconds.
        auto_retry: Automatically retry on transient failures (5xx, rate-limit).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://pdfforge-api.fly.dev",
        timeout: int = 30,
        auto_retry: bool = True,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auto_retry = auto_retry
        self._session = requests.Session()
        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"

    # ── Internal helpers ──────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make an HTTP request with optional retry logic."""
        kwargs.setdefault("timeout", self.timeout)
        max_attempts = 3 if self.auto_retry else 1

        for attempt in range(max_attempts):
            resp = self._session.request(method, self._url(path), **kwargs)

            if resp.status_code == 401:
                raise AuthError("Invalid or missing API key.", status=401)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "60"))
                if self.auto_retry and attempt < max_attempts - 1:
                    time.sleep(min(retry_after, 30))
                    continue
                raise RateLimitError(
                    "Rate limit exceeded.",
                    status=429,
                    retry_after=retry_after,
                )
            if resp.status_code >= 500 and self.auto_retry and attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue

            return resp

        return resp  # type: ignore[possibly-undefined]

    def _check_error(self, resp: requests.Response) -> None:
        """Raise ``PDFForgeError`` for non-2xx responses."""
        if resp.ok:
            return
        try:
            body = resp.json()
        except Exception:
            body = {}
        raise PDFForgeError(
            body.get("title", f"HTTP {resp.status_code}"),
            status=resp.status_code,
            detail=body.get("detail", resp.text),
        )

    def _upload_tool(
        self,
        tool: str,
        files_field: str,
        sources: list,
        *,
        extra_data: dict[str, Any] | None = None,
        async_mode: bool = False,
        webhook_url: str | None = None,
    ) -> JobResult:
        """Submit a multipart tool request and return a ``JobResult``."""
        multipart: list[tuple[str, Any]] = []
        for src in sources:
            data = read_file_bytes(src)
            multipart.append((files_field, ("file.pdf", data, "application/pdf")))

        form_data: dict[str, str] = {}
        if extra_data:
            for k, v in extra_data.items():
                form_data[k] = str(v)
        if webhook_url:
            form_data["webhook_url"] = webhook_url

        params: dict[str, str] = {}
        if async_mode:
            params["async"] = "true"

        resp = self._request("POST", f"/api/v1/{tool}", files=multipart, data=form_data, params=params)
        self._check_error(resp)
        return JobResult.from_dict(resp.json(), client=self)

    # ── Sync tool methods ─────────────────────────────────────────────────

    def merge(self, files: list[str | Path | bytes], output_name: str | None = None) -> JobResult:
        """Merge multiple PDFs into one document.

        Args:
            files: Two or more PDF file paths or raw bytes.
            output_name: Optional filename for the merged result.
        """
        extra = {"output_name": output_name} if output_name else None
        return self._upload_tool("merge", "files", files, extra_data=extra)

    def split(self, file: str | Path | bytes, ranges: list[list[int]]) -> JobResult:
        """Split a PDF by page ranges.

        Args:
            file: PDF file path or bytes.
            ranges: List of ``[start, end]`` page-number pairs (1-based).
        """
        ranges_str = ",".join(f"{r[0]}-{r[1]}" if len(r) == 2 else str(r[0]) for r in ranges)
        return self._upload_tool("split", "file", [file], extra_data={"ranges": ranges_str})

    def rotate(
        self,
        file: str | Path | bytes,
        degrees: int,
        pages: str | list[int] | None = None,
    ) -> JobResult:
        """Rotate pages of a PDF.

        Args:
            file: PDF file path or bytes.
            degrees: Rotation angle — 90, 180, or 270.
            pages: Page selection (e.g. ``"1,3-5"`` or ``[1,3,5]``). ``None`` = all.
        """
        extra: dict[str, Any] = {"angle": str(degrees)}
        if pages is not None:
            if isinstance(pages, list):
                extra["pages"] = ",".join(str(p) for p in pages)
            else:
                extra["pages"] = str(pages)
        return self._upload_tool("rotate", "file", [file], extra_data=extra)

    def extract_text(
        self,
        file: str | Path | bytes,
        pages: str | list[int] | None = None,
    ) -> JobResult:
        """Extract machine-readable text from a PDF.

        Args:
            file: PDF file path or bytes.
            pages: Page selection. ``None`` = all pages.
        """
        extra: dict[str, Any] = {}
        if pages is not None:
            if isinstance(pages, list):
                extra["pages"] = ",".join(str(p) for p in pages)
            else:
                extra["pages"] = str(pages)
        return self._upload_tool("extract_text", "file", [file], extra_data=extra)

    def encrypt(self, file: str | Path | bytes, password: str) -> JobResult:
        """Encrypt a PDF with a password.

        Args:
            file: PDF file path or bytes.
            password: Password to set on the PDF.
        """
        return self._upload_tool("encrypt", "file", [file], extra_data={"password": password})

    def decrypt(self, file: str | Path | bytes, password: str) -> JobResult:
        """Decrypt a password-protected PDF.

        Args:
            file: PDF file path or bytes.
            password: Current password of the encrypted PDF.
        """
        return self._upload_tool("decrypt", "file", [file], extra_data={"password": password})

    # ── Async tool methods ────────────────────────────────────────────────

    def merge_async(self, files: list[str | Path | bytes], webhook_url: str | None = None) -> JobResult:
        """Submit a merge job asynchronously. Returns immediately with status=queued."""
        return self._upload_tool("merge", "files", files, async_mode=True, webhook_url=webhook_url)

    def split_async(self, file: str | Path | bytes, ranges: list[list[int]], webhook_url: str | None = None) -> JobResult:
        """Submit a split job asynchronously."""
        ranges_str = ",".join(f"{r[0]}-{r[1]}" if len(r) == 2 else str(r[0]) for r in ranges)
        return self._upload_tool("split", "file", [file], extra_data={"ranges": ranges_str}, async_mode=True, webhook_url=webhook_url)

    def rotate_async(self, file: str | Path | bytes, degrees: int, pages: str | list[int] | None = None, webhook_url: str | None = None) -> JobResult:
        """Submit a rotate job asynchronously."""
        extra: dict[str, Any] = {"angle": str(degrees)}
        if pages is not None:
            extra["pages"] = ",".join(str(p) for p in pages) if isinstance(pages, list) else str(pages)
        return self._upload_tool("rotate", "file", [file], extra_data=extra, async_mode=True, webhook_url=webhook_url)

    def extract_text_async(self, file: str | Path | bytes, webhook_url: str | None = None) -> JobResult:
        """Submit an extract_text job asynchronously."""
        return self._upload_tool("extract_text", "file", [file], async_mode=True, webhook_url=webhook_url)

    def encrypt_async(self, file: str | Path | bytes, password: str, webhook_url: str | None = None) -> JobResult:
        """Submit an encrypt job asynchronously."""
        return self._upload_tool("encrypt", "file", [file], extra_data={"password": password}, async_mode=True, webhook_url=webhook_url)

    def decrypt_async(self, file: str | Path | bytes, password: str, webhook_url: str | None = None) -> JobResult:
        """Submit a decrypt job asynchronously."""
        return self._upload_tool("decrypt", "file", [file], extra_data={"password": password}, async_mode=True, webhook_url=webhook_url)

    # ── Job management ────────────────────────────────────────────────────

    def get_job(self, job_id: str) -> JobResult:
        """Fetch the current state of a job."""
        resp = self._request("GET", f"/api/v1/jobs/{job_id}")
        self._check_error(resp)
        return JobResult.from_dict(resp.json(), client=self)

    def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 0.5,
        timeout: int = 60,
    ) -> JobResult:
        """Poll a job until it reaches a terminal state (done or failed).

        Args:
            job_id: The job to poll.
            poll_interval: Seconds between polls.
            timeout: Maximum wait time in seconds.

        Raises:
            JobFailedError: If the job transitions to ``failed``.
            TimeoutError: If *timeout* is exceeded.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = self.get_job(job_id)
            if result.is_done():
                return result
            if result.is_failed():
                raise JobFailedError(
                    f"Job {job_id} failed.",
                    job_id=job_id,
                    error=result.error,
                )
            time.sleep(poll_interval)
        raise TimeoutError(f"Job {job_id} did not complete within {timeout}s.")

    def download_job(self, job_id: str, output_path: str | Path) -> Path:
        """Download a job's output file to disk.

        Returns the resolved ``Path`` of the saved file.
        """
        resp = self._request("GET", f"/api/v1/jobs/{job_id}/download")
        self._check_error(resp)
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        return dest

    def delete_job(self, job_id: str) -> None:
        """Delete a job's output early."""
        resp = self._request("DELETE", f"/api/v1/jobs/{job_id}")
        if resp.status_code not in (204, 404):
            self._check_error(resp)

    # ── Pipeline ──────────────────────────────────────────────────────────

    def pipeline(
        self,
        steps: list[dict[str, Any]],
        files: list[str | Path | bytes],
        async_mode: bool = False,
        webhook_url: str | None = None,
    ) -> PipelineResult:
        """Execute a multi-step pipeline.

        Args:
            steps: Ordered list of ``{"tool": "...", "params": {...}}`` dicts.
            files: Initial input files (paths or bytes).
            async_mode: If ``True``, return immediately with status=queued.
            webhook_url: URL to receive a webhook on completion.
        """
        encoded = [to_base64(f) for f in files]
        body: dict[str, Any] = {"steps": steps, "files": encoded}
        if async_mode:
            body["async"] = True
        if webhook_url:
            body["webhook_url"] = webhook_url

        resp = self._request("POST", "/api/v1/pipeline", json=body)
        self._check_error(resp)
        return PipelineResult.from_dict(resp.json(), client=self)

    # ── Batch ─────────────────────────────────────────────────────────────

    def batch(
        self,
        tool: str,
        params: dict[str, Any],
        files: list[str | Path | bytes],
        webhook_url: str | None = None,
    ) -> BatchResult:
        """Submit a batch of the same operation across multiple files.

        Args:
            tool: Tool name (e.g. ``"split"``).
            params: Tool-specific parameters.
            files: Input files (paths or bytes).
            webhook_url: URL to receive a webhook per-job on completion.
        """
        encoded = [to_base64(f) for f in files]
        body: dict[str, Any] = {
            "tool": tool,
            "params": params,
            "files": encoded,
            "async": True,
        }
        if webhook_url:
            body["webhook_url"] = webhook_url

        resp = self._request("POST", "/api/v1/batch", json=body)
        self._check_error(resp)
        return BatchResult.from_dict(resp.json(), client=self)

    def get_batch(self, batch_id: str) -> BatchResult:
        """Fetch the aggregate status of a batch."""
        resp = self._request("GET", f"/api/v1/batch/{batch_id}")
        self._check_error(resp)
        return BatchResult.from_dict(resp.json(), client=self)

    # ── Capabilities ──────────────────────────────────────────────────────

    def capabilities(self) -> dict[str, Any]:
        """Fetch the server's capabilities manifest."""
        resp = self._request("GET", "/api/v1/capabilities")
        if resp.status_code == 404:
            resp = self._request("GET", "/api/v1/tools")
        self._check_error(resp)
        return resp.json()
