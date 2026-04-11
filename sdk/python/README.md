# PDFforge Python SDK

Official Python SDK for the [PDFforge](https://pdfforge.intelliforge.tech) PDF toolkit API by IntelliForge AI.

## Installation

```bash
pip install pdfforge-sdk
```

## Quick Start

```python
from pdfforge import PDFForge

client = PDFForge(
    api_key="your-api-key",           # optional for self-hosted
    base_url="http://localhost:5050",  # or https://pdfforge-api.fly.dev
)

# Merge PDFs
result = client.merge(["file1.pdf", "file2.pdf"])
result.download("merged.pdf")

# Split by page ranges
result = client.split("report.pdf", ranges=[[1, 3], [4, 10]])
result.download("split.zip")

# Rotate pages
result = client.rotate("scan.pdf", degrees=90, pages=[1, 3])

# Extract text
result = client.extract_text("contract.pdf")

# Encrypt / Decrypt
result = client.encrypt("sensitive.pdf", password="secret")
result = client.decrypt("locked.pdf", password="secret")
```

## Async Jobs

```python
job = client.merge_async(["a.pdf", "b.pdf"], webhook_url="https://example.com/hook")
result = client.wait_for_job(job.job_id, timeout=60)
result.download("output.pdf")
```

## Pipeline

```python
result = client.pipeline(
    steps=[
        {"tool": "merge", "params": {}},
        {"tool": "encrypt", "params": {"password": "secret"}},
    ],
    files=["a.pdf", "b.pdf"],
)
```

## Batch Processing

```python
batch = client.batch("extract_text", {}, ["a.pdf", "b.pdf", "c.pdf"])
# Poll: batch = client.get_batch(batch.batch_id)
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/
```

## License

MIT
