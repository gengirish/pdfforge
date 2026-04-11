"""PDFforge Python SDK — programmatic access to the PDFforge PDF toolkit API."""

from pdfforge.client import PDFForge
from pdfforge.models import BatchResult, JobResult, PipelineResult
from pdfforge.exceptions import (
    AuthError,
    JobFailedError,
    PDFForgeError,
    RateLimitError,
)

__version__ = "0.1.0"
__all__ = [
    "PDFForge",
    "JobResult",
    "BatchResult",
    "PipelineResult",
    "PDFForgeError",
    "AuthError",
    "RateLimitError",
    "JobFailedError",
]
