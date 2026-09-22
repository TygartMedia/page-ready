#!/usr/bin/env python3
"""Agent-ready DOM scorer — AEO-v2-style binary gates.

Five gates (all must PASS for page PASS):
  1. LANDMARKS          — main landmark present
  2. NAMED_CONTROLS     — interactive elements have accessible names
  3. SEMANTIC_INTERACTIVE — no clickable non-semantic nodes without role
  4. HEADING_ORDER      — exactly one h1; no level skips in outline
  5. FORM_LABELS        — every visible input/select/textarea has a label
                        (auto-PASS if page has no form controls)

Optional axe injection (CDN) feeds gate 2 evidence; axe serious+critical
violations also fail NAMED_CONTROLS when name/label related.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.3/axe.min.js"

PROBE_JS = r"""
() => {
  const visible = (el) => {
    const s = window.getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };

  const interactiveSel = [
    'a[href]', 'button', 'input:not([type="hidden"])', 'select', 'textarea',
    '[role="button"]', '[role="link"]', '[role="menuitem"]', '[role="tab"]',
    '[role="checkbox"]', '[role="radio"]', '[role="switch"]', '[contenteditable="true"]',
    'summary'
  ].join(',');

  const nodes = Array.from(document.querySelectorAll(interactiveSel)).filter(visible);

  const accessibleName = (el) => {
    const aria = (el.getAttribute('aria-label') || '').trim();
    if (aria) return aria;
    const labelledBy = el.getAttribute('aria-labelledby');
    if (labelledBy) {
      const parts = labelledBy.split(/\s+/).map(id => {
        const n = document.getElementById(id);
        return n ? (n.innerText || n.textContent || '').trim() : '';
      }).filter(Boolean);
      if (parts.length) return parts.join(' ');
    }
    if (el.tagName === 'IMG') return (el.getAttribute('alt') || '').trim();
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {
      if (el.id) {
        const lab = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
        if (lab) return (lab.innerText || lab.textContent || '').trim();
      }
      const wrap = el.closest('label');
      if (wrap) return (wrap.innerText || wrap.textContent || '').trim();
      // A submit/button/reset input's visible label is its value attribute.
      // Text-like inputs do not use value; that is the user's data, not the name.
      const inputType = (el.getAttribute('type') || '').toLowerCase();
      if (el.tagName === 'INPUT' && (inputType === 'submit' || inputType === 'button' || inputType === 'reset')) {
        const value = (el.getAttribute('value') || '').trim();
        if (value) return value;
      }
      const title = (el.getAttribute('title') || '').trim();
      if (title) return title;
      const ph = (el.getAttribute('placeholder') || '').trim();
      if (ph) return ph;
      return '';
    }
    const t = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
    if (t) return t.slice(0, 120);
    const title = (el.getAttribute('title') || '').trim();
    if (title) return title;
    const altImg = el.querySelector('img[alt]');
    if (altImg) return (altImg.getAttribute('alt') || '').trim();
    return '';
  };

  const unnamed = [];
  for (const el of nodes) {
    const name = accessibleName(el);
    if (!name) {
      unnamed.push({
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute('type') || null,
        role: el.getAttribute('role') || null,
        id: el.id || null,
        class: (el.className && typeof el.className === 'string') ? el.className.slice(0, 80) : null,
        href: el.getAttribute('href') || null,
      });
    }
  }

  // Clickable non-semantic without role
  const handlers = Array.from(document.querySelectorAll('div, span, li, p, td'))
    .filter(visible)
    .filter(el => {
      const role = el.getAttribute('role');
      if (role) return false;
      if (el.onclick != null) return true;
      const attrs = el.getAttributeNames().filter(n => n.startsWith('on'));
      if (attrs.length) return true;
      // Heuristic: cursor:pointer + tabindex
      const s = window.getComputedStyle(el);
      const tab = el.getAttribute('tabindex');
      return s.cursor === 'pointer' && tab !== null;
    })
    .slice(0, 25)
    .map(el => ({
      tag: el.tagName.toLowerCase(),
      id: el.id || null,
      class: (el.className && typeof el.className === 'string') ? el.className.slice(0, 80) : null,
      text: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60),
    }));

  const landmarks = {
    main: !!document.querySelector('main, [role="main"]'),
    nav: !!document.querySelector('nav, [role="navigation"]'),
    banner: !!document.querySelector('header, [role="banner"]'),
    contentinfo: !!document.querySelector('footer, [role="contentinfo"]'),
  };

  const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
    .filter(visible)
    .map(h => ({ level: parseInt(h.tagName[1], 10), text: (h.innerText || '').trim().slice(0, 80) }));

  const h1Count = headings.filter(h => h.level === 1).length;
  let skip = null;
  let prev = 0;
  for (const h of headings) {
    if (prev && h.level > prev + 1) {
      skip = { from: prev, to: h.level, text: h.text };
      break;
    }
    prev = h.level;
  }

  const controls = Array.from(document.querySelectorAll(
    'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="image"]):not([type="reset"]), select, textarea'
  )).filter(visible);

  const unlabeled = [];
  for (const el of controls) {
    const name = accessibleName(el);
    if (!name) {
      unlabeled.push({
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute('type') || null,
        id: el.id || null,
        name: el.getAttribute('name') || null,
      });
    }
  }

  return {
    url: location.href,
    title: document.title,
    interactiveCount: nodes.length,
    unnamed,
    semanticIssues: handlers,
    landmarks,
    headings: { count: headings.length, h1Count, skip, sample: headings.slice(0, 12) },
    forms: { controlCount: controls.length, unlabeled },
  };
}
"""


def gate(name: str, passed: bool, detail: str, evidence: Any = None) -> dict:
    return {
        "gate": name,
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
        "evidence": evidence or {},
    }


def score_probe(probe: dict, axe: dict | None) -> list[dict]:
    gates = []

    lm = probe["landmarks"]
    gates.append(
        gate(
            "LANDMARKS",
            bool(lm.get("main")),
            "main landmark present" if lm.get("main") else "missing <main> or role=main",
            lm,
        )
    )

    unnamed = probe["unnamed"]
    # Strict: every interactive control named. Fold axe serious/critical that
    # affect the accessibility tree (agent view) — skip pure visual contrast.
    named_ok = len(unnamed) == 0
    axe_name_hits = []
    axe_bad = []
    skip_axe = {"color-contrast", "color-contrast-enhanced"}
    if axe and not axe.get("error"):
        for v in axe.get("violations", []):
            vid = v.get("id") or ""
            if vid in {
                "button-name",
                "link-name",
                "label",
                "input-button-name",
                "aria-input-field-name",
                "aria-command-name",
            }:
                axe_name_hits.append(vid)
                named_ok = False
            if v.get("impact") in {"serious", "critical"} and vid not in skip_axe:
                axe_bad.append({"id": vid, "impact": v.get("impact"), "help": v.get("help")})
                named_ok = False
    gates.append(
        gate(
            "NAMED_CONTROLS",
            named_ok,
            f"{probe['interactiveCount']} interactive; {len(unnamed)} unnamed"
            + (f"; axe-name: {', '.join(axe_name_hits)}" if axe_name_hits else "")
            + (f"; axe tree serious/critical: {len(axe_bad)}" if axe_bad else ""),
            {
                "unnamed_sample": unnamed[:10],
                "axe_name_rules": axe_name_hits,
                "axe_serious_critical_agent": axe_bad[:10],
            },
        )
    )

    sem = probe["semanticIssues"]
    gates.append(
        gate(
            "SEMANTIC_INTERACTIVE",
            len(sem) == 0,
            "no clickable non-semantic nodes without role"
            if not sem
            else f"{len(sem)} clickable non-semantic node(s)",
            {"sample": sem[:10]},
        )
    )

    h = probe["headings"]
    heading_ok = h["h1Count"] == 1 and h["skip"] is None
    detail = f"h1={h['h1Count']}"
    if h["skip"]:
        detail += f"; skip h{h['skip']['from']}→h{h['skip']['to']}"
    elif h["h1Count"] != 1:
        detail += " (want exactly 1)"
    else:
        detail += "; outline ok"
    gates.append(gate("HEADING_ORDER", heading_ok, detail, h))

    forms = probe["forms"]
    if forms["controlCount"] == 0:
        gates.append(
            gate("FORM_LABELS", True, "no form controls (auto-PASS)", forms)
        )
    else:
        ok = len(forms["unlabeled"]) == 0
        gates.append(
            gate(
                "FORM_LABELS",
                ok,
                f"{forms['controlCount']} controls; {len(forms['unlabeled'])} unlabeled",
                {"unlabeled": forms["unlabeled"][:10]},
            )
        )

    return gates


def run_axe(page) -> dict | None:
    try:
        page.add_script_tag(url=AXE_CDN)
        page.wait_for_function("() => typeof axe !== 'undefined'", timeout=15000)
        return page.evaluate(
            """async () => {
              const r = await axe.run(document, {
                resultTypes: ['violations'],
                runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'best-practice'] }
              });
              return {
                violations: r.violations.map(v => ({
                  id: v.id,
                  impact: v.impact,
                  help: v.help,
                  nodes: v.nodes.length,
                })),
                serious_or_critical: r.violations.filter(
                  v => v.impact === 'serious' || v.impact === 'critical'
                ).length,
              };
            }"""
        )
    except Exception as e:  # noqa: BLE001 — evidence only
        return {"error": str(e), "violations": [], "serious_or_critical": 0}


def _finalize(probe: dict, axe: dict | None, source: str) -> dict:
    gates = score_probe(probe, axe)
    passed = all(g["status"] == "PASS" for g in gates)
    return {
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "url": source,
        "title": probe.get("title"),
        "overall": "PASS" if passed else "FAIL",
        "gates_passed": sum(1 for g in gates if g["status"] == "PASS"),
        "gates_total": len(gates),
        "gates": gates,
        "axe": axe,
        "engine": "dom-fleet/score.py + playwright + axe-core CDN",
    }


def score_url(url: str, headless: bool = True, timeout_ms: int = 45000) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(1500)  # let WP / late widgets settle a bit
        probe = page.evaluate(PROBE_JS)
        axe = run_axe(page)
        browser.close()
    return _finalize(probe, axe, url)


def score_html(html: str, source: str = "inline.html", headless: bool = True) -> dict:
    """Score a static HTML string (fixtures / before-after experiments)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.set_content(html, wait_until="domcontentloaded")
        page.wait_for_timeout(300)
        probe = page.evaluate(PROBE_JS)
        axe = run_axe(page)
        browser.close()
    return _finalize(probe, axe, source)


def main() -> int:
    ap = argparse.ArgumentParser(description="Agent-ready DOM binary-gate scorer")
    ap.add_argument("url", nargs="?", default="https://tygartmedia.com/ai-visibility-audit/")
    ap.add_argument("--html", type=Path, default=None, help="Score a local HTML file instead of a URL")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    if args.html:
        html = args.html.read_text(encoding="utf-8")
        result = score_html(html, source=str(args.html), headless=not args.headed)
        default_name = args.html.stem
    else:
        result = score_url(args.url, headless=not args.headed)
        host = urlparse(args.url).netloc.replace(".", "_") or "page"
        path = urlparse(args.url).path.strip("/").replace("/", "-") or "home"
        default_name = f"{host}__{path}"

    out = args.out
    if out is None:
        out = Path(__file__).resolve().parent / "reports" / f"{default_name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"OVERALL  {result['overall']}  ({result['gates_passed']}/{result['gates_total']})")
    print(f"URL      {result['url']}")
    print(f"TITLE    {result.get('title')}")
    for g in result["gates"]:
        print(f"  [{g['status']}] {g['gate']}: {g['detail']}")
    if result.get("axe") and not result["axe"].get("error"):
        print(f"  axe serious/critical: {result['axe'].get('serious_or_critical', 0)}")
    elif result.get("axe", {}).get("error"):
        print(f"  axe skipped: {result['axe']['error']}")
    print(f"Wrote {out}")
    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
