"""Split tool wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdfforge.client import PDFForge
    from pdfforge.models import JobResult


class SplitTool:
    """Splits a PDF into separate files by page ranges."""

    def __init__(self, client: "PDFForge"):
        self._client = client

    def run(self, file: str | Path | bytes, ranges: list[list[int]]) -> "JobResult":
        """Split *file* by *ranges* synchronously."""
        return self._client.split(file, ranges)

    def run_async(self, file: str | Path | bytes, ranges: list[list[int]], webhook_url: str | None = None) -> "JobResult":
        """Submit a split job asynchronously."""
        return self._client.split_async(file, ranges, webhook_url=webhook_url)
