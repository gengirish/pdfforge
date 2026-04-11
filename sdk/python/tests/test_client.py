"""Unit tests for the PDFForge client using mocked HTTP responses."""

from __future__ import annotations

import io
import json

import pytest
import responses

from pdfforge import PDFForge, JobResult, BatchResult, PipelineResult
from pdfforge.exceptions import AuthError, PDFForgeError

BASE = "https://pdfforge-api.fly.dev"


@pytest.fixture
def client():
    return PDFForge(api_key="test-key", base_url=BASE, auto_retry=False)


@pytest.fixture
def sample_pdf() -> bytes:
    from pypdf import PdfWriter
    buf = io.BytesIO()
    w = PdfWriter()
    w.add_blank_page(width=612, height=792)
    w.write(buf)
    return buf.getvalue()


# ── Health / capabilities ────────────────────────────────────────────────

@responses.activate
def test_capabilities(client):
    responses.add(responses.GET, f"{BASE}/api/v1/capabilities", status=404)
    responses.add(
        responses.GET,
        f"{BASE}/api/v1/tools",
        json={"tools": [{"id": "merge"}]},
    )
    result = client.capabilities()
    assert "tools" in result


# ── Merge ────────────────────────────────────────────────────────────────

@responses.activate
def test_merge_sync(client, sample_pdf):
    envelope = {
        "success": True,
        "job_id": "job_abc123",
        "tool": "merge",
        "output_url": "/api/v1/jobs/job_abc123/download",
        "metadata": {"pages": 1, "size_bytes": 500, "processing_ms": 42, "filename": "merged.pdf"},
        "expires_at": "2026-04-12T00:00:00",
    }
    responses.add(responses.POST, f"{BASE}/api/v1/merge", json=envelope, status=200)
    result = client.merge([sample_pdf])
    assert isinstance(result, JobResult)
    assert result.job_id == "job_abc123"
    assert result.is_done() is False  # status from envelope is not "done"
    assert result.tool == "merge"


@responses.activate
def test_merge_async(client, sample_pdf):
    responses.add(
        responses.POST,
        f"{BASE}/api/v1/merge",
        json={"job_id": "job_async1", "status": "queued", "poll_url": "/api/v1/jobs/job_async1"},
        status=202,
    )
    result = client.merge_async([sample_pdf])
    assert result.status == "queued"
    assert result.job_id == "job_async1"


# ── Auth errors ──────────────────────────────────────────────────────────

@responses.activate
def test_auth_error(client, sample_pdf):
    responses.add(responses.POST, f"{BASE}/api/v1/merge", status=401, json={
        "success": False, "type": "/errors/unauthorized", "title": "Unauthorized",
        "status": 401, "detail": "Invalid API key.",
    })
    with pytest.raises(AuthError):
        client.merge([sample_pdf])


# ── Job lifecycle ────────────────────────────────────────────────────────

@responses.activate
def test_get_job(client):
    manifest = {
        "job_id": "job_xyz",
        "status": "done",
        "tool": "merge",
        "output_url": "/api/v1/jobs/job_xyz/download",
        "metadata": {"pages": 2},
        "expires_at": "2026-04-12T00:00:00",
    }
    responses.add(responses.GET, f"{BASE}/api/v1/jobs/job_xyz", json=manifest)
    result = client.get_job("job_xyz")
    assert result.is_done()
    assert result.metadata["pages"] == 2


@responses.activate
def test_download_job(client, tmp_path):
    responses.add(
        responses.GET,
        f"{BASE}/api/v1/jobs/job_dl/download",
        body=b"%PDF-fake-content",
        content_type="application/pdf",
    )
    out = client.download_job("job_dl", tmp_path / "output.pdf")
    assert out.exists()
    assert out.read_bytes() == b"%PDF-fake-content"


@responses.activate
def test_delete_job(client):
    responses.add(responses.DELETE, f"{BASE}/api/v1/jobs/job_del", status=204)
    client.delete_job("job_del")


# ── Pipeline ─────────────────────────────────────────────────────────────

@responses.activate
def test_pipeline(client, sample_pdf):
    envelope = {
        "success": True,
        "job_id": "job_pipe",
        "tool": "pipeline",
        "output_url": "/api/v1/jobs/job_pipe/download",
        "metadata": {"pages": 1, "size_bytes": 100, "processing_ms": 50, "filename": "out.pdf"},
        "expires_at": "2026-04-12T00:00:00",
        "pipeline": {
            "total_steps": 2,
            "completed_steps": 2,
            "step_results": [
                {"step": 1, "tool": "merge", "duration_ms": 30},
                {"step": 2, "tool": "encrypt", "duration_ms": 20},
            ],
        },
    }
    responses.add(responses.POST, f"{BASE}/api/v1/pipeline", json=envelope)
    result = client.pipeline(
        steps=[{"tool": "merge", "params": {}}, {"tool": "encrypt", "params": {"password": "x"}}],
        files=[sample_pdf],
    )
    assert isinstance(result, PipelineResult)
    assert result.pipeline["total_steps"] == 2


# ── Batch ────────────────────────────────────────────────────────────────

@responses.activate
def test_batch(client, sample_pdf):
    batch_resp = {
        "batch_id": "batch_001",
        "total_files": 2,
        "tool": "extract_text",
        "jobs": [
            {"file_index": 0, "job_id": "job_b1", "status": "queued"},
            {"file_index": 1, "job_id": "job_b2", "status": "queued"},
        ],
    }
    responses.add(responses.POST, f"{BASE}/api/v1/batch", json=batch_resp, status=202)
    result = client.batch("extract_text", {}, [sample_pdf, sample_pdf])
    assert isinstance(result, BatchResult)
    assert result.batch_id == "batch_001"
    assert result.total_files == 2
    assert not result.all_done


@responses.activate
def test_get_batch(client):
    batch_resp = {
        "batch_id": "batch_002",
        "total_files": 1,
        "tool": "merge",
        "jobs": [{"file_index": 0, "job_id": "job_b3", "status": "done"}],
    }
    responses.add(responses.GET, f"{BASE}/api/v1/batch/batch_002", json=batch_resp)
    result = client.get_batch("batch_002")
    assert result.all_done


# ── Encrypt / Decrypt ────────────────────────────────────────────────────

@responses.activate
def test_encrypt(client, sample_pdf):
    envelope = {
        "success": True, "job_id": "job_enc", "tool": "encrypt",
        "output_url": "/dl", "metadata": {"pages": 1}, "expires_at": "2026-04-12T00:00:00",
    }
    responses.add(responses.POST, f"{BASE}/api/v1/encrypt", json=envelope)
    result = client.encrypt(sample_pdf, "pass123")
    assert result.job_id == "job_enc"


@responses.activate
def test_decrypt(client, sample_pdf):
    envelope = {
        "success": True, "job_id": "job_dec", "tool": "decrypt",
        "output_url": "/dl", "metadata": {"pages": 1}, "expires_at": "2026-04-12T00:00:00",
    }
    responses.add(responses.POST, f"{BASE}/api/v1/decrypt", json=envelope)
    result = client.decrypt(sample_pdf, "pass123")
    assert result.job_id == "job_dec"


# ── Split / Rotate / Extract ────────────────────────────────────────────

@responses.activate
def test_split(client, sample_pdf):
    envelope = {
        "success": True, "job_id": "job_spl", "tool": "split",
        "output_url": "/dl", "metadata": {"pages": 1}, "expires_at": "2026-04-12T00:00:00",
    }
    responses.add(responses.POST, f"{BASE}/api/v1/split", json=envelope)
    result = client.split(sample_pdf, [[1, 1]])
    assert result.job_id == "job_spl"


@responses.activate
def test_rotate(client, sample_pdf):
    envelope = {
        "success": True, "job_id": "job_rot", "tool": "rotate",
        "output_url": "/dl", "metadata": {"pages": 1}, "expires_at": "2026-04-12T00:00:00",
    }
    responses.add(responses.POST, f"{BASE}/api/v1/rotate", json=envelope)
    result = client.rotate(sample_pdf, 90, pages=[1])
    assert result.job_id == "job_rot"


@responses.activate
def test_extract_text(client, sample_pdf):
    envelope = {
        "success": True, "job_id": "job_ext", "tool": "extract_text",
        "output_url": "/dl", "metadata": {"pages": 1}, "expires_at": "2026-04-12T00:00:00",
    }
    responses.add(responses.POST, f"{BASE}/api/v1/extract_text", json=envelope)
    result = client.extract_text(sample_pdf)
    assert result.job_id == "job_ext"
