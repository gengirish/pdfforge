"""Tests for tool wrapper classes and utility functions."""

from __future__ import annotations

import io

import pytest
import responses

from pdfforge import PDFForge
from pdfforge.tools import MergeTool, SplitTool, RotateTool, ExtractTextTool, EncryptTool, DecryptTool
from pdfforge.utils.file_utils import to_base64, from_base64, validate_pdf

BASE = "https://pdfforge-api.fly.dev"


@pytest.fixture
def client():
    return PDFForge(base_url=BASE, auto_retry=False)


@pytest.fixture
def sample_pdf() -> bytes:
    from pypdf import PdfWriter
    buf = io.BytesIO()
    w = PdfWriter()
    w.add_blank_page(width=612, height=792)
    w.write(buf)
    return buf.getvalue()


# ── file_utils ───────────────────────────────────────────────────────────

def test_base64_roundtrip(sample_pdf):
    encoded = to_base64(sample_pdf)
    decoded = from_base64(encoded)
    assert decoded == sample_pdf


def test_validate_pdf_good(sample_pdf):
    result = validate_pdf(sample_pdf)
    assert result == sample_pdf


def test_validate_pdf_bad():
    with pytest.raises(ValueError, match="not appear to be a valid PDF"):
        validate_pdf(b"not a pdf")


# ── Tool wrappers ────────────────────────────────────────────────────────

ENVELOPE = {
    "success": True, "job_id": "job_tw", "tool": "merge",
    "output_url": "/dl", "metadata": {"pages": 1}, "expires_at": "2026-04-12T00:00:00",
}


@responses.activate
def test_merge_tool(client, sample_pdf):
    responses.add(responses.POST, f"{BASE}/api/v1/merge", json=ENVELOPE)
    tool = MergeTool(client)
    result = tool.run([sample_pdf])
    assert result.job_id == "job_tw"


@responses.activate
def test_split_tool(client, sample_pdf):
    env = {**ENVELOPE, "tool": "split", "job_id": "job_sp"}
    responses.add(responses.POST, f"{BASE}/api/v1/split", json=env)
    tool = SplitTool(client)
    result = tool.run(sample_pdf, [[1, 1]])
    assert result.job_id == "job_sp"


@responses.activate
def test_rotate_tool(client, sample_pdf):
    env = {**ENVELOPE, "tool": "rotate", "job_id": "job_rt"}
    responses.add(responses.POST, f"{BASE}/api/v1/rotate", json=env)
    tool = RotateTool(client)
    result = tool.run(sample_pdf, 90)
    assert result.job_id == "job_rt"


@responses.activate
def test_extract_text_tool(client, sample_pdf):
    env = {**ENVELOPE, "tool": "extract_text", "job_id": "job_et"}
    responses.add(responses.POST, f"{BASE}/api/v1/extract_text", json=env)
    tool = ExtractTextTool(client)
    result = tool.run(sample_pdf)
    assert result.job_id == "job_et"


@responses.activate
def test_encrypt_tool(client, sample_pdf):
    env = {**ENVELOPE, "tool": "encrypt", "job_id": "job_en"}
    responses.add(responses.POST, f"{BASE}/api/v1/encrypt", json=env)
    tool = EncryptTool(client)
    result = tool.run(sample_pdf, "pw")
    assert result.job_id == "job_en"


@responses.activate
def test_decrypt_tool(client, sample_pdf):
    env = {**ENVELOPE, "tool": "decrypt", "job_id": "job_dc"}
    responses.add(responses.POST, f"{BASE}/api/v1/decrypt", json=env)
    tool = DecryptTool(client)
    result = tool.run(sample_pdf, "pw")
    assert result.job_id == "job_dc"
