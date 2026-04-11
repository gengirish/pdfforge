"""Encrypt tool wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdfforge.client import PDFForge
    from pdfforge.models import JobResult


class EncryptTool:
    """Password-protects a PDF."""

    def __init__(self, client: "PDFForge"):
        self._client = client

    def run(self, file: str | Path | bytes, password: str) -> "JobResult":
        """Encrypt synchronously."""
        return self._client.encrypt(file, password)

    def run_async(self, file: str | Path | bytes, password: str, webhook_url: str | None = None) -> "JobResult":
        """Submit an encrypt job asynchronously."""
        return self._client.encrypt_async(file, password, webhook_url=webhook_url)
