#!/usr/bin/env python3
"""PageReady MCP server — score_page / score_site / explain_gates (stdio JSON-RPC)."""

from __future__ import annotations

import json
import sys
from typing import Any

from page_ready.score import score_page_url

PROTOCOL_VERSION = "2024-11-05"
SUPPORTED = {PROTOCOL_VERSION}
SERVER_NAME = "page-ready"
SERVER_VERSION = "0.1.0a0"


def log(msg: str) -> None:
    sys.stderr.write(f"[page-ready] {msg}\n")
    sys.stderr.flush()


def send(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def send_result(req_id: Any, result: dict) -> None:
    send({"jsonrpc": "2.0", "id": req_id, "result": result})


def send_error(req_id: Any, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def text_result(text: str, is_error: bool = False) -> dict:
    payload = {"content": [{"type": "text", "text": text}]}
    if is_error:
        payload["isError"] = True
    return payload


TOOLS = [
    {
        "name": "score_page",
        "description": "Run PageReady AEO (cite-ready) + DOM (click-ready) binary gates on one URL. Returns JSON scorecard.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Public http(s) URL to score"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "score_site",
        "description": "Score up to 10 URLs (site pack preview). Returns per-URL scorecards + rollup counts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of public http(s) URLs (max 10)",
                },
            },
            "required": ["urls"],
        },
    },
    {
        "name": "explain_gates",
        "description": "Explain PageReady AEO and DOM gates and overall PASS policy.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def handle_tool(name: str, args: dict) -> tuple[str, bool]:
    if name == "explain_gates":
        return (
            "\n".join(
                [
                    "### PageReady gates",
                    "",
                    "**AEO (citation / answer-engine structure)** — technical health checks:",
                    "- Exactly one H1 + no heading level skips",
                    "- At least two H2s",
                    "- JSON-LD schema present",
                    "- Structured table signal",
                    "- FAQ-style questions present",
                    "- PASS when passed_checks >= 4 / 5",
                    "",
                    "**DOM (agent interaction)** — five binary gates:",
                    "- LANDMARKS — main landmark",
                    "- NAMED_CONTROLS — interactive elements named (+ agent-relevant axe)",
                    "- SEMANTIC_INTERACTIVE — no clickable div/span without role",
                    "- HEADING_ORDER — one H1, no skips",
                    "- FORM_LABELS — labeled controls (or auto-PASS if none)",
                    "",
                    "**Overall PASS** only if AEO passed_checks >= 4 AND DOM overall PASS.",
                    "AEO heading fixes can lift DOM HEADING_ORDER; they do not fix clickable non-semantic cards.",
                ]
            ),
            False,
        )

    if name == "score_page":
        url = (args.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            return ("url must be http(s)", True)
        result = score_page_url(url)
        return (json.dumps(result, indent=2), False)

    if name == "score_site":
        urls = args.get("urls") or []
        if not isinstance(urls, list) or not urls:
            return ("urls must be a non-empty array", True)
        urls = [u.strip() for u in urls if isinstance(u, str)][:10]
        rows = []
        for u in urls:
            if not u.startswith(("http://", "https://")):
                rows.append({"url": u, "error": "not http(s)"})
                continue
            try:
                rows.append(score_page_url(u))
            except Exception as exc:  # noqa: BLE001
                rows.append({"url": u, "error": str(exc)})
        passed = sum(1 for r in rows if r.get("overall") == "PASS")
        rollup = {
            "product": "page-ready",
            "scored": len(rows),
            "passed": passed,
            "failed": len(rows) - passed,
            "results": rows,
        }
        return (json.dumps(rollup, indent=2), False)

    return (f"Unknown tool: {name}", True)


def main() -> None:
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace", newline="")
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n", line_buffering=True)
    except Exception:
        pass

    log(f"Starting {SERVER_NAME} MCP {SERVER_VERSION}")
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        raw = line.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            try:
                req = json.loads(raw.encode("utf-8").decode("utf-8-sig"))
            except json.JSONDecodeError as exc:
                send_error(None, -32700, f"Parse error: {exc}")
                continue

        req_id = req.get("id")
        is_notification = "id" not in req
        method = req.get("method")
        params = req.get("params") or {}

        try:
            if method == "initialize":
                requested = params.get("protocolVersion") or PROTOCOL_VERSION
                negotiated = requested if requested in SUPPORTED else PROTOCOL_VERSION
                send_result(
                    req_id,
                    {
                        "protocolVersion": negotiated,
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    },
                )
            elif method == "notifications/initialized":
                pass
            elif method == "ping":
                if not is_notification:
                    send_result(req_id, {})
            elif method == "tools/list":
                send_result(req_id, {"tools": TOOLS})
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments") or {}
                text, err = handle_tool(tool_name, tool_args if isinstance(tool_args, dict) else {})
                send_result(req_id, text_result(text, err))
            else:
                if not is_notification:
                    send_error(req_id, -32601, f"Method {method} not found")
        except Exception as exc:  # noqa: BLE001
            log(f"error: {exc}")
            if not is_notification:
                send_error(req_id, -32603, f"Internal error: {exc}")


if __name__ == "__main__":
    main()
