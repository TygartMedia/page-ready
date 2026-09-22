# PyPI + MCP

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

Tools: `score_page`, `score_site` (≤10 URLs), `explain_gates`.

## PyPI

Package name: **page-ready**.

1. Create https://pypi.org account (Tygart Media) if needed.
2. Add Trusted Publisher: GitHub `TygartMedia/page-ready`, workflow `publish-pypi.yml`, environment `pypi`.
3. Create GitHub Environment `pypi` (optional reviewers).
4. Actions → **Publish to PyPI** → type `publish`.

Until then, install from Git:

```bash
pip install "git+https://github.com/TygartMedia/page-ready.git"
```
