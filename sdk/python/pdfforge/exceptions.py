"""Exception hierarchy for the PDFforge SDK."""

from __future__ import annotations


class PDFForgeError(Exception):
    """Base exception for all PDFforge SDK errors."""

    def __init__(self, message: str, status: int | None = None, detail: str | None = None):
        super().__init__(message)
        self.status = status
        self.detail = detail


class AuthError(PDFForgeError):
    """Raised when the API key is missing, invalid, or rejected (HTTP 401)."""


class RateLimitError(PDFForgeError):
    """Raised when the hourly rate limit has been exceeded (HTTP 429)."""

    def __init__(self, message: str, retry_after: int | None = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class JobFailedError(PDFForgeError):
    """Raised when a job finishes with status=failed."""

    def __init__(self, message: str, job_id: str | None = None, error: dict | None = None, **kwargs):
        super().__init__(message, **kwargs)
        self.job_id = job_id
        self.error = error
