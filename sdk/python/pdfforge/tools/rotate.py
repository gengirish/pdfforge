"""Rotate tool wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdfforge.client import PDFForge
    from pdfforge.models import JobResult


class RotateTool:
    """Rotates pages of a PDF by 90, 180, or 270 degrees."""

    def __init__(self, client: "PDFForge"):
        self._client = client

    def run(self, file: str | Path | bytes, degrees: int, pages: str | list[int] | None = None) -> "JobResult":
        """Rotate pages synchronously."""
        return self._client.rotate(file, degrees, pages)

    def run_async(self, file: str | Path | bytes, degrees: int, pages: str | list[int] | None = None, webhook_url: str | None = None) -> "JobResult":
        """Submit a rotate job asynchronously."""
        return self._client.rotate_async(file, degrees, pages, webhook_url=webhook_url)
