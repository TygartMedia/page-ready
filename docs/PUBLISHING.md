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

Tools: `score_page`, `score_site`, `explain_gates`.

## PyPI Trusted Publisher

Package name in `pyproject.toml`: **page-ready** (must match PyPI).

### One-time setup (Will / Glint)

1. PyPI account for Tygart Media if needed: https://pypi.org  
2. Create project **page-ready** (or first publish will).  
3. **Publishing** → Add Trusted Publisher:
   - Owner: `TygartMedia`
   - Repository: `page-ready`
   - Workflow: `publish.yml`
   - Environment: `release`
4. GitHub repo → Settings → Environments → create **`release`** (optional protection rules).

### Release

Actions → **Publish to PyPI** → type `publish` in the confirm box → Run.

Until published:

```bash
pip install "git+https://github.com/TygartMedia/page-ready.git"
```
