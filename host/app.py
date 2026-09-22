"""Uncharged hosted API — rate-limited score endpoint for Cloud Run.

Payments (x402 / Stripe) are stubbed behind PAGE_READY_ACCEPT_PAID=0 (default).
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from page_ready.score import score_page_url
from page_ready.ssrf import UnsafeURLError, assert_public_http_url

app = FastAPI(
    title="PageReady API",
    version="0.1.0a0",
    description="Cite-ready + click-ready scoring. Uncharged alpha — payments HOLD.",
)

ACCEPT_PAID = os.getenv("PAGE_READY_ACCEPT_PAID", "0") == "1"
RATE_LIMIT = int(os.getenv("PAGE_READY_RATE_PER_MIN", "10"))
_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit(ip: str) -> None:
    now = time.time()
    with _lock:
        q = _hits[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        q.append(now)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "product": "page-ready", "accept_paid": ACCEPT_PAID}


@app.get("/v1/score")
def score(request: Request, url: str = Query(..., min_length=8)) -> JSONResponse:
    """Score one URL. Uncharged while PAGE_READY_ACCEPT_PAID=0."""
    _rate_limit(_client_ip(request))
    try:
        safe = assert_public_http_url(url)
    except UnsafeURLError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Payment rail placeholder — live charging requires D10/D11 YES
    if ACCEPT_PAID:
        raise HTTPException(
            status_code=501,
            detail="Paid mode enabled but payment adapters not wired yet",
        )

    try:
        result = score_page_url(safe)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Score failed: {exc}") from exc

    result["billing"] = {"charged": False, "mode": "uncharged_alpha"}
    return JSONResponse(result)


@app.get("/")
def root() -> dict:
    return {
        "product": "page-ready",
        "docs": "/docs",
        "score": "/v1/score?url=https://example.com/",
        "payments": "HOLD — x402 + Stripe packs not live",
    }
