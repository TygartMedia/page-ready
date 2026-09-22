"""AEO technical health gates (ported from aeo-fleet v2). Citation readiness."""

from __future__ import annotations

import json
import re
from typing import Any


def strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "")


def extract_headings(raw_content: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    cleaned = re.sub(
        r"<script[\s\S]*?</script>|<style[\s\S]*?</style>",
        "",
        raw_content,
        flags=re.IGNORECASE,
    )
    for m in re.finditer(
        r"<h([1-6])\b[^>]*>([\s\S]*?)</h\1>", cleaned, flags=re.IGNORECASE
    ):
        headings.append((int(m.group(1)), strip_html_tags(m.group(2)).strip()))
    for m_md in re.finditer(r"^(#{1,6})\s+(.+)$", cleaned, flags=re.MULTILINE):
        headings.append((len(m_md.group(1)), m_md.group(2).strip()))
    return headings


def extract_embedded_schemas(raw_content: str) -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',
        raw_content,
        flags=re.IGNORECASE,
    ):
        try:
            parsed = json.loads(m.group(1).strip())
            if isinstance(parsed, dict):
                schemas.append(parsed)
            elif isinstance(parsed, list):
                schemas.extend([p for p in parsed if isinstance(p, dict)])
        except json.JSONDecodeError:
            continue
    return schemas


def _type_tokens(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for v in value:
            out.extend(_type_tokens(v))
        return out
    return []


def evaluate_technical_health(raw_content: str) -> dict[str, Any]:
    headings = extract_headings(raw_content)
    h1s = [h[1] for h in headings if h[0] == 1]
    h2s = [h[1] for h in headings if h[0] == 2]

    heading_issues: list[str] = []
    if len(h1s) == 0:
        heading_issues.append("Missing primary H1 tag. Every page must have exactly one H1.")
    elif len(h1s) > 1:
        heading_issues.append(
            f"Multiple H1 tags found ({len(h1s)}). Ensure only one primary H1 exists."
        )

    for i in range(len(headings) - 1):
        curr_lvl, next_lvl = headings[i][0], headings[i + 1][0]
        if next_lvl > curr_lvl + 1:
            heading_issues.append(
                f"Heading level skipped: H{curr_lvl} ('{headings[i][1][:25]}...') "
                f"jumps to H{next_lvl} ('{headings[i+1][1][:25]}...')."
            )

    schemas = extract_embedded_schemas(raw_content)
    schema_types: list[str] = []
    for s in schemas:
        if "@type" in s:
            schema_types.extend(_type_tokens(s["@type"]))
        graph = s.get("@graph")
        if isinstance(graph, list):
            for node in graph:
                if isinstance(node, dict) and "@type" in node:
                    schema_types.extend(_type_tokens(node["@type"]))

    has_table = bool(re.search(r"<table\b|\|.*\|.*\|", raw_content, re.IGNORECASE))
    has_faq = bool(
        re.search(
            r"\b(?:What|How|Why|Which|When|Where|Can|Does|Is)\b.*\?",
            raw_content,
            re.IGNORECASE,
        )
    )

    passed_checks = 0
    total_checks = 5
    if len(h1s) == 1 and not heading_issues:
        passed_checks += 1
    if len(h2s) >= 2:
        passed_checks += 1
    if len(schemas) >= 1:
        passed_checks += 1
    if has_table:
        passed_checks += 1
    if has_faq:
        passed_checks += 1

    status = (
        "PASS"
        if passed_checks >= 4
        else ("WARN" if passed_checks >= 2 else "FAIL")
    )

    return {
        "status": status,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "h1_count": len(h1s),
        "h2_count": len(h2s),
        "heading_issues": heading_issues,
        "schema_count": len(schemas),
        "detected_schema_types": sorted(set(schema_types)),
        "has_structured_table": has_table,
        "has_faq_questions": has_faq,
    }
