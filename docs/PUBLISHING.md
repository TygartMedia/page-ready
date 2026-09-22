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

**HOLD:** First Actions → Publish is a real upload (creates the project + ships v0.1.0a0). Hard to un-publish.

Requires **Will typed YES** in chat before Cursor runs the workflow.

Then: Actions → **Publish to PyPI** → type `publish` in the confirm box → Run.

Until published:

```bash
pip install "git+https://github.com/TygartMedia/page-ready.git"
```
