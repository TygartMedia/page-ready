"""Unified PageReady scorecard: AEO technical + DOM agent gates."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from page_ready.aeo import evaluate_technical_health
from page_ready._dom_legacy import score_html, score_url

_UA = "PageReady/0.1 (+https://tygartmedia.com)"
_FETCH_RETRIES = 3
# Ask caches/CDNs for a fresh copy: a live score must reflect the page as it is
# now, not a stale cached render (seen 2026-09-23: first fetch showed the
# pre-refresh page, cache-busted fetch showed the new one).
_NO_CACHE_HEADERS = {"User-Agent": _UA, "Cache-Control": "no-cache", "Pragma": "no-cache"}


def _fetch_urllib(url: str, timeout: int) -> str:
    req = Request(url, headers=_NO_CACHE_HEADERS)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _fetch_curl(url: str, timeout: int) -> str:
    # curl has proven far more reliable than urllib through this egress path
    # (urllib hits IncompleteRead/RemoteDisconnected on endpoints curl reads clean).
    out = subprocess.run(
        ["curl", "-sSL", "--max-time", str(timeout), "-A", _UA,
         "-H", "Cache-Control: no-cache", "-H", "Pragma: no-cache", url],
        capture_output=True,
        timeout=timeout + 10,
    )
    out.check_returncode()
    return out.stdout.decode("utf-8", "replace")


def _fetch(url: str, timeout: int = 30) -> str:
    last: Exception | None = None
    for attempt in range(_FETCH_RETRIES):
        try:
            return _fetch_urllib(url, timeout)
        except Exception as exc:  # IncompleteRead, RemoteDisconnected, timeouts
            last = exc
            time.sleep(2**attempt)
    try:
        return _fetch_curl(url, timeout)
    except Exception as exc:
        raise RuntimeError(f"fetch failed for {url}: urllib gave {last!r}, curl gave {exc!r}") from exc


def combine(aeo: dict[str, Any], dom: dict[str, Any], url: str) -> dict[str, Any]:
    aeo_ok = aeo["passed_checks"] >= 4
    dom_ok = dom["overall"] == "PASS"
    overall = "PASS" if aeo_ok and dom_ok else "FAIL"
    hints: list[str] = []
    if aeo.get("heading_issues"):
        hints.append("Fix heading outline (exactly one H1; no level skips).")
    if aeo.get("schema_count", 0) < 1:
        hints.append("Add valid JSON-LD (Article/FAQPage) for citation extractability.")
    for g in dom.get("gates", []):
        if g["status"] == "FAIL":
            if g["gate"] == "SEMANTIC_INTERACTIVE":
                hints.append("Replace clickable div/span with <a>/<button> or add role + name.")
            elif g["gate"] == "NAMED_CONTROLS":
                hints.append("Give interactive controls accessible names (text, aria-label, or label).")
            elif g["gate"] == "LANDMARKS":
                hints.append("Wrap primary content in <main>.")
            elif g["gate"] == "FORM_LABELS":
                hints.append("Label every form control.")
            elif g["gate"] == "HEADING_ORDER":
                hints.append("Align DOM heading outline with AEO heading rules.")
    return {
        "product": "page-ready",
        "version": "0.1.0a0",
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "overall": overall,
        "aeo": aeo,
        "dom": {
            "overall": dom["overall"],
            "gates_passed": dom["gates_passed"],
            "gates_total": dom["gates_total"],
            "gates": dom["gates"],
        },
        "overlap_note": "HEADING_ORDER / H1+hierarchy is the shared signal between AEO and DOM.",
        "fix_hints": hints,
    }


def score_page_url(url: str) -> dict[str, Any]:
    html = _fetch(url)
    aeo = evaluate_technical_health(html)
    dom = score_url(url)
    return combine(aeo, dom, url)


def score_page_html(html: str, source: str = "inline.html") -> dict[str, Any]:
    aeo = evaluate_technical_health(html)
    dom = score_html(html, source=source)
    return combine(aeo, dom, source)


def score_fixture(path: Path) -> dict[str, Any]:
    html = path.read_text(encoding="utf-8")
    return score_page_html(html, source=str(path))


def main_print(result: dict[str, Any]) -> None:
    print(f"OVERALL  {result['overall']}")
    print(f"URL      {result['url']}")
    a = result["aeo"]
    print(f"AEO      {a['status']}  {a['passed_checks']}/{a['total_checks']}")
    d = result["dom"]
    print(f"DOM      {d['overall']}  {d['gates_passed']}/{d['gates_total']}")
    for g in d["gates"]:
        print(f"  [{g['status']}] {g['gate']}: {g['detail']}")
    if result.get("fix_hints"):
        print("HINTS")
        for h in result["fix_hints"]:
            print(f"  - {h}")


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="PageReady unified scorer")
    ap.add_argument("target", help="URL or path to HTML fixture")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if args.target.startswith("http://") or args.target.startswith("https://"):
        result = score_page_url(args.target)
    else:
        result = score_fixture(Path(args.target))

    main_print(result)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote {args.out}")
    sys.exit(0 if result["overall"] == "PASS" else 1)
