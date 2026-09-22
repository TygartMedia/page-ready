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

## PyPI Trusted Publisher (pending — project not registered yet)

Package name in `pyproject.toml`: **page-ready**.

Warehouse check (expect 404 until first publish):

- `https://pypi.org/pypi/page-ready/json`
- `https://pypi.org/simple/page-ready/`

### One-time setup (Will)

Project page does **not** exist yet. Register a **pending** publisher at account level; PyPI creates the project on first successful publish.

1. Sign in to https://pypi.org (correct account).  
2. Open **[Account publishing settings](https://pypi.org/manage/account/publishing/)**.  
3. Add a **new pending publisher** with exact values:
   - **PyPI Project Name:** `page-ready`
   - **Owner:** `TygartMedia`
   - **Repository name:** `page-ready`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `release`
4. Save.

Repo side already matches: `.github/workflows/publish.yml` + GitHub Environment `release`.

### First release (D16)

**PARKED PERMANENTLY (Will 2026-09-22 ~3:15 PM PDT).**  
No PyPI account. Do not enable `publish.yml`, do not run Publish, do not ask for credentials.  
Failed run `35790727117` stays as-is — no retries.

Install from Git:

```bash
pip install "git+https://github.com/TygartMedia/page-ready.git"
```
