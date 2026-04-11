"""Async job submission with polling and webhook examples."""

from pdfforge import PDFForge

client = PDFForge(base_url="http://localhost:5050")

# --- Submit async and poll ---
job = client.merge_async(["file1.pdf", "file2.pdf"])
print(f"Job queued: {job.job_id}, status={job.status}")

# Block until done (polls every 0.5s, times out at 60s)
result = client.wait_for_job(job.job_id, poll_interval=0.5, timeout=60)
print(f"Done! Pages: {result.metadata.get('pages')}")
result.download("merged.pdf")

# --- Submit with webhook ---
job = client.encrypt_async(
    "report.pdf",
    password="secret",
    webhook_url="https://example.com/webhook",
)
print(f"Encrypt queued: {job.job_id}")
print("Webhook will POST to https://example.com/webhook on completion")
