"""Basic usage examples for the PDFforge Python SDK."""

from pdfforge import PDFForge

# Initialize client (no API key needed for self-hosted open mode)
client = PDFForge(base_url="http://localhost:5050")

# --- Merge PDFs ---
result = client.merge(["invoice_1.pdf", "invoice_2.pdf"])
print(f"Merged: {result.job_id}")
result.download("merged_output.pdf")

# --- Split a PDF ---
result = client.split("report.pdf", ranges=[[1, 3], [4, 10]])
print(f"Split into ZIP: {result.job_id}")
result.download("split_output.zip")

# --- Rotate pages ---
result = client.rotate("scanned.pdf", degrees=90, pages=[1, 3])
print(f"Rotated: {result.job_id}")

# --- Extract text ---
result = client.extract_text("contract.pdf")
print(f"Text extracted: {result.metadata}")

# --- Encrypt ---
result = client.encrypt("sensitive.pdf", password="secure123")
result.download("encrypted.pdf")

# --- Decrypt ---
result = client.decrypt("encrypted.pdf", password="secure123")
result.download("decrypted.pdf")
