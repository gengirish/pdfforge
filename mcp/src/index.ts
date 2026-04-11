#!/usr/bin/env node
/**
 * PDFforge MCP Server — exposes PDF tools as MCP tools for AI agents.
 *
 * Connects to the PDFforge REST API and wraps each operation as an MCP tool
 * with typed Zod input schemas and human-readable descriptions.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const API_URL = process.env.PDFFORGE_API_URL || "http://localhost:5000";
const API_KEY = process.env.PDFFORGE_API_KEY || "";

// ── HTTP helper ──────────────────────────────────────────────────────────

async function apiCall(
  method: string,
  path: string,
  body?: Record<string, unknown> | FormData,
  contentType?: string
): Promise<Record<string, unknown>> {
  const headers: Record<string, string> = {};
  if (API_KEY) headers["Authorization"] = `Bearer ${API_KEY}`;

  let fetchBody: string | FormData | undefined;
  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = contentType || "application/json";
    fetchBody = JSON.stringify(body);
  } else {
    fetchBody = body as FormData | undefined;
  }

  const resp = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: fetchBody,
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API ${method} ${path} returned ${resp.status}: ${text}`);
  }
  return (await resp.json()) as Record<string, unknown>;
}

async function toolUpload(
  path: string,
  files: string[],
  fieldName: string,
  extraFields?: Record<string, string>
): Promise<Record<string, unknown>> {
  const formData = new FormData();
  for (const b64 of files) {
    const bytes = Buffer.from(b64, "base64");
    const blob = new Blob([bytes], { type: "application/pdf" });
    formData.append(fieldName, blob, "input.pdf");
  }
  if (extraFields) {
    for (const [k, v] of Object.entries(extraFields)) {
      formData.append(k, v);
    }
  }

  const headers: Record<string, string> = {};
  if (API_KEY) headers["Authorization"] = `Bearer ${API_KEY}`;

  const resp = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Upload to ${path} returned ${resp.status}: ${text}`);
  }
  return (await resp.json()) as Record<string, unknown>;
}

// ── MCP Server ───────────────────────────────────────────────────────────

const server = new McpServer({
  name: "pdfforge",
  version: "0.1.0",
});

// ── merge_pdfs ───────────────────────────────────────────────────────────

server.tool(
  "merge_pdfs",
  `Merge two or more PDF files into a single document.
Use this when the user wants to combine multiple PDF files into one.
Input: An array of PDF files as base64-encoded strings.
Output: A job result with a download URL for the merged PDF.`,
  {
    files: z.array(z.string()).min(2).describe("Array of base64-encoded PDF files to merge"),
    output_name: z.string().optional().describe("Optional filename for the merged output"),
  },
  async ({ files, output_name }) => {
    const extra: Record<string, string> = {};
    if (output_name) extra["output_name"] = output_name;
    const result = await toolUpload("/api/v1/merge", files, "files", extra);
    return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
  }
);

// ── split_pdf ────────────────────────────────────────────────────────────

server.tool(
  "split_pdf",
  `Split a PDF into separate files by page ranges.
Use when a user wants to extract specific pages from a PDF.
Input: A single PDF file and page ranges like "1-3,5,7-10".
Output: A job result with a download URL for a ZIP of the split PDFs.`,
  {
    file: z.string().describe("Base64-encoded PDF file"),
    ranges: z.string().describe("Comma-separated page ranges, e.g. '1-3,5,7-10'"),
  },
  async ({ file, ranges }) => {
    const result = await toolUpload("/api/v1/split", [file], "file", { ranges });
    return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
  }
);

// ── rotate_pdf ───────────────────────────────────────────────────────────

server.tool(
  "rotate_pdf",
  `Rotate pages of a PDF by 90, 180, or 270 degrees.
Use when a user has scanned pages in wrong orientation.
Input: A PDF file, rotation angle, and optional page selection.
Output: A job result with the rotated PDF.`,
  {
    file: z.string().describe("Base64-encoded PDF file"),
    degrees: z.enum(["90", "180", "270"]).describe("Rotation angle in degrees"),
    pages: z.string().optional().describe("Optional page selection, e.g. '1,3-5'. Omit for all pages."),
  },
  async ({ file, degrees, pages }) => {
    const extra: Record<string, string> = { angle: degrees };
    if (pages) extra["pages"] = pages;
    const result = await toolUpload("/api/v1/rotate", [file], "file", extra);
    return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
  }
);

// ── extract_text ─────────────────────────────────────────────────────────

server.tool(
  "extract_text",
  `Extract machine-readable text from a PDF document.
Use when a user needs the text content of a PDF for search, analysis, or processing.
Input: A PDF file.
Output: A job result with a download URL for the extracted text file.`,
  {
    file: z.string().describe("Base64-encoded PDF file"),
  },
  async ({ file }) => {
    const result = await toolUpload("/api/v1/extract_text", [file], "file");
    return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
  }
);

// ── encrypt_pdf ──────────────────────────────────────────────────────────

server.tool(
  "encrypt_pdf",
  `Encrypt a PDF with a password so it requires the password to open.
Use when a user wants to protect a PDF before sharing.
Input: A PDF file and a password.
Output: A job result with the password-protected PDF.`,
  {
    file: z.string().describe("Base64-encoded PDF file"),
    password: z.string().min(1).describe("Password to set on the PDF"),
  },
  async ({ file, password }) => {
    const result = await toolUpload("/api/v1/encrypt", [file], "file", { password });
    return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
  }
);

// ── decrypt_pdf ──────────────────────────────────────────────────────────

server.tool(
  "decrypt_pdf",
  `Remove password protection from an encrypted PDF.
Use when a user has the password for an encrypted PDF and wants to unlock it.
Input: An encrypted PDF file and its current password.
Output: A job result with the decrypted PDF.`,
  {
    file: z.string().describe("Base64-encoded encrypted PDF file"),
    password: z.string().min(1).describe("Current password of the encrypted PDF"),
  },
  async ({ file, password }) => {
    const result = await toolUpload("/api/v1/decrypt", [file], "file", { password });
    return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
  }
);

// ── run_pipeline ─────────────────────────────────────────────────────────

server.tool(
  "run_pipeline",
  `Execute a multi-step PDF processing pipeline.
Use when a user needs to chain multiple PDF operations together, e.g. merge then encrypt.
Each step's output feeds into the next step as input.
Input: An array of steps (each with a tool name and params) and initial PDF files.
Output: A single job result for the entire pipeline with per-step timing.`,
  {
    steps: z.array(z.object({
      tool: z.enum(["merge", "split", "rotate", "extract_text", "encrypt", "decrypt"]),
      params: z.record(z.unknown()).optional().default({}),
    })).min(1).max(10).describe("Ordered array of pipeline steps"),
    files: z.array(z.string()).min(1).describe("Array of base64-encoded PDF files as initial input"),
  },
  async ({ steps, files }) => {
    const result = await apiCall("POST", "/api/v1/pipeline", { steps, files });
    return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
  }
);

// ── batch_process ────────────────────────────────────────────────────────

server.tool(
  "batch_process",
  `Process the same PDF operation on multiple files in parallel.
Use when a user wants to apply the same tool (e.g. extract_text) to many PDF files at once.
Input: A tool name, parameters, and an array of PDF files.
Output: A batch result with individual job IDs for each file.`,
  {
    tool: z.enum(["merge", "split", "rotate", "extract_text", "encrypt", "decrypt"]),
    params: z.record(z.unknown()).optional().default({}).describe("Tool-specific parameters"),
    files: z.array(z.string()).min(1).max(50).describe("Array of base64-encoded PDF files"),
  },
  async ({ tool, params, files }) => {
    const result = await apiCall("POST", "/api/v1/batch", {
      tool,
      params,
      files,
      async: true,
    });
    return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
  }
);

// ── Start ────────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("MCP server failed:", err);
  process.exit(1);
});
