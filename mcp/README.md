# PDFforge MCP Server

MCP (Model Context Protocol) server that exposes PDFforge tools to AI agents like Claude Desktop.

## Tools

| Tool | Description |
|------|-------------|
| `merge_pdfs` | Combine multiple PDFs into one |
| `split_pdf` | Split a PDF by page ranges |
| `rotate_pdf` | Rotate pages by 90/180/270 degrees |
| `extract_text` | Extract text content from a PDF |
| `encrypt_pdf` | Password-protect a PDF |
| `decrypt_pdf` | Remove password from an encrypted PDF |
| `run_pipeline` | Chain multiple operations together |
| `batch_process` | Apply same operation to multiple files |

## Claude Desktop Setup

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pdfforge": {
      "command": "npx",
      "args": ["-y", "@intelliforge/pdfforge-mcp"],
      "env": {
        "PDFFORGE_API_URL": "http://localhost:5050"
      }
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PDFFORGE_API_URL` | `http://localhost:5000` | PDFforge API base URL |
| `PDFFORGE_API_KEY` | *(empty)* | Optional API key for authenticated access |

## Development

```bash
npm install
npm run build
npm start
```

## License

MIT
