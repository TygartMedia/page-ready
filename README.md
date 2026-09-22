# PageReady

PageReady scores a public page, or a short list of pages, for two kinds of readiness:

1. **Citation readiness (AEO)** — one H1, heading hierarchy, JSON-LD, a table signal, and FAQ-style questions.
2. **Agent interaction readiness (DOM)** — a main landmark, named controls, semantic interactive elements, heading order, and form labels.

**Overall PASS** only when both sides clear. Fixing headings can lift the shared heading gate. It does not fix clickable `<div>` cards.

PageReady is a local command-line tool, a stdio MCP server, and an optional HTTP API you can run yourself (including on Cloud Run).

## MCP tools

| Tool | What it does |
|---|---|
| `score_page` | Score one public `http(s)` URL. Returns a JSON scorecard. |
| `score_site` | Score up to 10 URLs and return per-URL scorecards plus pass/fail counts. |
| `explain_gates` | Describe the AEO checks, the five DOM gates, and the overall PASS rule. |

## Quickstart

Requires Python 3.10+.

```bash
git clone https://github.com/TygartMedia/page-ready.git
cd page-ready
python -m venv .venv
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e .
playwright install chromium
page-ready fixtures/02-after-aeo-only.html
```

macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install -U pip
pip install -e .
playwright install chromium
page-ready fixtures/02-after-aeo-only.html
```

Exit code `0` means overall PASS. Exit code `1` means overall FAIL.

```bash
page-ready fixtures/01-before-aeo.html
page-ready fixtures/03-after-aeo-still-agent-broken.html
page-ready https://example.com/
```

### MCP

After the install above:

```bash
page-ready-mcp
```

Cursor MCP config (stdio):

```json
{
  "mcpServers": {
    "page-ready": {
      "command": "page-ready-mcp"
    }
  }
}
```

From a checkout without installing scripts, use `python -m page_ready.mcp_server` and set `PYTHONPATH` to `src`.

## Configuration

No API keys are required to score pages. Nothing secret belongs in this repository. `.env` files are gitignored.

| Variable | Default | Used by |
|---|---|---|
| `PAGE_READY_ACCEPT_PAID` | `0` | Host API. `1` is not a payment integration; the API returns 501. |
| `PAGE_READY_RATE_PER_MIN` | `10` | Host API, requests per client IP per minute. |
| `GCP_PROJECT` | unset (required to deploy) | `scripts/deploy-cloudrun.sh` and `scripts/deploy-cloudrun.ps1` only. |
| `REGION` | `us-central1` | Deploy scripts. |
| `SERVICE` | `page-ready-api` | Deploy scripts. |

Set `GCP_PROJECT` in your shell when you deploy. Do not commit a project id, a Cloud Run URL, or a service-account file.

### Host API

```bash
pip install -e ".[host]"
uvicorn host.app:app --reload
```

`GET /v1/score?url=https://example.com/`  
`GET /readyz` and `GET /v1/status`

Deploy (your own Google Cloud project):

```bash
# bash
export GCP_PROJECT="your-project-id"
bash scripts/deploy-cloudrun.sh
```

```powershell
# PowerShell
$env:GCP_PROJECT = "your-project-id"
.\scripts\deploy-cloudrun.ps1
```

The script prints the service URL from Cloud Run. That URL is not stored in this repo.

## Fixtures

| Fixture | Expected |
|---|---|
| `fixtures/01-before-aeo.html` | AEO FAIL, DOM FAIL (headings) |
| `fixtures/02-after-aeo-only.html` | AEO PASS, DOM PASS |
| `fixtures/03-after-aeo-still-agent-broken.html` | AEO PASS, DOM FAIL (semantic) |

## As-is

Community use is welcome. PageReady is provided **as-is**, with no service level, no uptime commitment, and no support promise. GitHub issues are read on a best-effort basis. See `LICENSE` and `SECURITY.md`.

## License

MIT © 2026 Tygart Media
