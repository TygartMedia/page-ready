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
python -m page_ready.score https://example.com/
```

Requires Python 3.11+ and Playwright Chromium.

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
- [ ] PyPI `page-ready` release
- [ ] Local MCP server (`score_page`, `score_site`)
- [ ] Hosted API on Cloud Run (rate-limited; payments later)
- [ ] Agent pay: x402 per-URL · Stripe site packs ($4.99 / $9.99)

Agent-oriented pricing target: stay inside a **$10–20 task budget** (packs ≤ $9.99). Micropayments via x402; card checkout only at pack floor (Stripe fees).

## License

MIT © Tygart Media

## Security

Do not point a hosted scorer at private IPs. SSRF controls are mandatory before any public API. See `SECURITY.md`.
