#!/usr/bin/env python3
"""CLI entry: page-ready <url-or-html-path> [--out file.json]"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from page_ready.score import main_print, score_fixture, score_page_url


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        prog="page-ready",
        description="Cite-ready (AEO) + click-ready (DOM) page scoring",
    )
    ap.add_argument("target", help="URL or path to HTML file")
    ap.add_argument("--out", type=Path, default=None, help="Write full JSON report")
    args = ap.parse_args(argv)

    if args.target.startswith("http://") or args.target.startswith("https://"):
        result = score_page_url(args.target)
    else:
        result = score_fixture(Path(args.target))

    main_print(result)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote {args.out}")
    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
