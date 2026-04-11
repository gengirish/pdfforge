"""Extract text tool wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdfforge.client import PDFForge
    from pdfforge.models import JobResult


class ExtractTextTool:
    """Extracts machine-readable text from a PDF."""

    def __init__(self, client: "PDFForge"):
        self._client = client

    def run(self, file: str | Path | bytes) -> "JobResult":
        """Extract text synchronously."""
        return self._client.extract_text(file)

    def run_async(self, file: str | Path | bytes, webhook_url: str | None = None) -> "JobResult":
        """Submit an extract_text job asynchronously."""
        return self._client.extract_text_async(file, webhook_url=webhook_url)
