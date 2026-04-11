"""Merge tool wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdfforge.client import PDFForge
    from pdfforge.models import JobResult


class MergeTool:
    """Combines multiple PDFs into a single file."""

    def __init__(self, client: "PDFForge"):
        self._client = client

    def run(self, files: list[str | Path | bytes], output_name: str | None = None) -> "JobResult":
        """Merge *files* synchronously and return a ``JobResult``."""
        return self._client.merge(files, output_name=output_name)

    def run_async(self, files: list[str | Path | bytes], webhook_url: str | None = None) -> "JobResult":
        """Submit a merge job asynchronously."""
        return self._client.merge_async(files, webhook_url=webhook_url)
