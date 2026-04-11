"""File encoding and validation utilities."""

from __future__ import annotations

import base64
from pathlib import Path


def to_base64(source: str | Path | bytes) -> str:
    """Encode a file path or raw bytes as a base64 string."""
    if isinstance(source, (str, Path)):
        data = Path(source).read_bytes()
    elif isinstance(source, bytes):
        data = source
    else:
        raise TypeError(f"Expected str, Path, or bytes — got {type(source).__name__}")
    return base64.b64encode(data).decode("ascii")


def from_base64(encoded: str) -> bytes:
    """Decode a base64 string back to bytes."""
    return base64.b64decode(encoded)


def validate_pdf(source: str | Path | bytes) -> bytes:
    """Read and minimally validate a PDF, returning raw bytes.

    Raises ``ValueError`` if the file doesn't start with ``%PDF``.
    """
    if isinstance(source, (str, Path)):
        data = Path(source).read_bytes()
    elif isinstance(source, bytes):
        data = source
    else:
        raise TypeError(f"Expected str, Path, or bytes — got {type(source).__name__}")
    if not data[:5].startswith(b"%PDF"):
        raise ValueError("File does not appear to be a valid PDF (missing %PDF header).")
    return data


def read_file_bytes(source: str | Path | bytes) -> bytes:
    """Normalize a file source to raw bytes."""
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    if isinstance(source, bytes):
        return source
    raise TypeError(f"Expected str, Path, or bytes — got {type(source).__name__}")
