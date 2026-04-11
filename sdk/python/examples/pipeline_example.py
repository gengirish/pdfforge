"""Multi-step pipeline and batch processing examples."""

from pdfforge import PDFForge

client = PDFForge(base_url="http://localhost:5050")

# --- Pipeline: merge then encrypt ---
result = client.pipeline(
    steps=[
        {"tool": "merge", "params": {}},
        {"tool": "encrypt", "params": {"password": "secure123"}},
    ],
    files=["invoice_q1.pdf", "invoice_q2.pdf"],
)
print(f"Pipeline done: {result.job_id}")
print(f"  Steps: {result.pipeline['completed_steps']}/{result.pipeline['total_steps']}")
for step in result.pipeline["step_results"]:
    print(f"  Step {step['step']} ({step['tool']}): {step['duration_ms']}ms")
result.download("merged_encrypted.pdf")

# --- Batch: extract text from multiple files ---
batch = client.batch(
    tool="extract_text",
    params={},
    files=["contract_a.pdf", "contract_b.pdf", "contract_c.pdf"],
)
print(f"\nBatch submitted: {batch.batch_id} ({batch.total_files} files)")

# Poll until all done
import time
while not batch.all_done:
    time.sleep(1)
    batch = batch.refresh()
    done_count = sum(1 for j in batch.jobs if j["status"] in ("done", "failed"))
    print(f"  Progress: {done_count}/{batch.total_files}")

print("Batch complete!")
for job in batch.jobs:
    print(f"  File {job['file_index']}: {job['status']} (job_id={job['job_id']})")
