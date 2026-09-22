# Install and MCP

PageReady is installed from this Git repository. It is not a PyPI release channel. Do not publish this package, and do not enable or run `.github/workflows/publish.yml`.

```bash
pip install "git+https://github.com/TygartMedia/page-ready.git"
```

For a checkout, use the quickstart in `README.md` (`pip install -e .`).

## Local MCP (Cursor)

```json
{
  "mcpServers": {
    "page-ready": {
      "command": "python",
      "args": ["-m", "page_ready.mcp_server"],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

Or after install: `"command": "page-ready-mcp"`.

Tools: `score_page`, `score_site`, `explain_gates`.
