"""Decrypt tool wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdfforge.client import PDFForge
    from pdfforge.models import JobResult


class DecryptTool:
    """Removes password protection from a PDF."""

    def __init__(self, client: "PDFForge"):
        self._client = client

    def run(self, file: str | Path | bytes, password: str) -> "JobResult":
        """Decrypt synchronously."""
        return self._client.decrypt(file, password)

    def run_async(self, file: str | Path | bytes, password: str, webhook_url: str | None = None) -> "JobResult":
        """Submit a decrypt job asynchronously."""
        return self._client.decrypt_async(file, password, webhook_url=webhook_url)
