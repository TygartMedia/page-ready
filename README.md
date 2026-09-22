# PageReady

**Cite-ready + click-ready page scoring** for developers and AI agents.

PageReady runs two binary scorecards on a URL (or local HTML):

1. **AEO (citation readiness)** — H1 integrity, heading hierarchy, JSON-LD schema, table + FAQ signals  
2. **DOM (agent interaction readiness)** — landmarks, named controls, semantic interactive elements, heading outline, form labels  

**Overall PASS** only when both sides clear.

> Measured internally: AEO-only optimization often lifts the shared heading gate, but **does not** fix agent-broken patterns (e.g. clickable `<div>` cards). Score both.

## Install (dev / local)

```bash
pip install -e .
playwright install chromium
```

```bash
page-ready fixtures/01-before-aeo.html
python -m page_ready https://example.com/
```

### MCP

```bash
page-ready-mcp
# or: python -m page_ready.mcp_server
```

See `docs/PUBLISHING.md` for Cursor MCP config + PyPI trusted publishing.

### Hosted API (Cloud Run, uncharged)

```bash
pip install -e ".[host]"
uvicorn host.app:app --reload
# GET /v1/score?url=https://example.com/
```

Deploy: `bash scripts/deploy-cloudrun.sh` (project `plucky-agent-313422`).  
`PAGE_READY_ACCEPT_PAID=0` — no x402/Stripe charging until product decision D10/D11.

## Scorecard shape

```json
{
  "product": "page-ready",
  "overall": "FAIL",
  "aeo": { "status": "PASS", "passed_checks": 5, "total_checks": 5 },
  "dom": { "overall": "FAIL", "gates_passed": 4, "gates_total": 5 },
  "fix_hints": ["Replace clickable div/span with <a>/<button> or add role + name."]
}
```

## Fixtures

| Fixture | Expected |
|---|---|
| `fixtures/01-before-aeo.html` | AEO FAIL · DOM FAIL (headings) |
| `fixtures/02-after-aeo-only.html` | AEO PASS · DOM PASS |
| `fixtures/03-after-aeo-still-agent-broken.html` | AEO PASS · DOM FAIL (semantic) |

## Roadmap (public)

- [x] Unified CLI scorecard (alpha)
- [x] Local MCP server (`score_page`, `score_site`, `explain_gates`)
- [x] Hosted API scaffold + SSRF guards (Cloud Run)
- [ ] PyPI `page-ready` release (Trusted Publisher workflow ready)
- [ ] Agent pay: x402 per-URL · Stripe site packs ($4.99 / $9.99) — HOLD until enabled

Agent-oriented pricing target: stay inside a **$10–20 task budget** (packs ≤ $9.99). Micropayments via x402; card checkout only at pack floor (Stripe fees).

## License

MIT © Tygart Media

## Security

Do not point a hosted scorer at private IPs. SSRF controls are mandatory before any public API. See `SECURITY.md`.
