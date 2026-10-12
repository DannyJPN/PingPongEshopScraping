"""
Unified report format shared by all CS vs SK scripts.

Every script writes the same three files:
  <name>_<timestamp>.json  machine readable (schema REPORT_SCHEMA)
  <name>_<timestamp>.csv   one finding per row (Excel friendly, ';' separated)
  <name>_<timestamp>.txt   human readable summary + findings grouped by check
"""
import csv
import json
import os
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional

from cssklib.constants import REPORT_SCHEMA, SEVERITY_ERROR
from cssklib.values import short

CSV_COLUMNS = [
    "check", "severity", "side", "product_code", "product_name", "variant_code",
    "variant_options", "property", "cs_value", "sk_value", "expected", "message",
]


@dataclass
class Finding:
    check: str
    property: str
    message: str
    product_code: str = ""
    product_name: str = ""
    severity: str = SEVERITY_ERROR
    side: str = "both"              # cs | sk | both
    variant_code: str = ""
    variant_options: str = ""
    cs_value: Any = None
    sk_value: Any = None
    expected: Any = None
    details: Optional[dict] = None

    def to_dict(self):
        data = asdict(self)
        if data["details"] is None:
            del data["details"]
        return data


@dataclass
class CheckResult:
    check: str
    title: str
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def build_report(results, sources, pairing_summary, options=None, generated_at=None):
    findings = [f for r in results for f in r.findings]
    by_severity = Counter(f.severity for f in findings)
    return {
        "schema": REPORT_SCHEMA,
        "generated_at": (generated_at or datetime.now()).isoformat(timespec="seconds"),
        "checks": [r.check for r in results],
        "sources": sources,
        "pairing": pairing_summary,
        "options": options or {},
        "summary": {
            "total_findings": len(findings),
            "by_severity": dict(sorted(by_severity.items())),
            "by_check": {
                r.check: {"title": r.title, "findings": len(r.findings), **r.stats}
                for r in results
            },
        },
        "findings": [f.to_dict() for f in findings],
    }


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def write_json(report, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, default=str)


def write_csv(report, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(CSV_COLUMNS)
        for finding in report["findings"]:
            writer.writerow([_cell(finding.get(col)) for col in CSV_COLUMNS])


def render_text(report, max_items=0, summary_only=False):
    """Human readable report. max_items limits listed findings per check (0 = all)."""
    lines = []
    summary = report["summary"]
    lines.append("PINCESOBCHOD — POROVNÁNÍ CZ vs SK")
    lines.append(f"Vygenerováno: {report['generated_at']}   (schema {report['schema']})")
    lines.append("")
    for side, info in report["sources"].items():
        lines.append(f"Zdroj {side.upper()}: {info.get('path')}  ({info.get('products')} produktů)")
    pairing = report["pairing"]
    lines.append(
        "Párování (kód + název): "
        f"spárováno {pairing.get('matched', 0)} | jen CZ {pairing.get('cs_only', 0)} | "
        f"jen SK {pairing.get('sk_only', 0)} | stejný kód, jiný název {pairing.get('name_conflicts', 0)}"
    )
    lines.append("")
    lines.append("=" * 100)
    lines.append("SOUHRN")
    lines.append("=" * 100)
    lines.append(f"Celkem nálezů: {summary['total_findings']}   "
                 + "  ".join(f"{k}: {v}" for k, v in summary["by_severity"].items()))
    lines.append("")
    lines.append(f"{'kontrola':<36} {'nálezů':>8} {'kontrolováno':>13}  název")
    lines.append("-" * 100)
    for check, info in summary["by_check"].items():
        checked = info.get("checked", "")
        lines.append(f"{check:<36} {info['findings']:>8} {str(checked):>13}  {info['title']}")
    if summary_only:
        return "\n".join(lines) + "\n"

    by_check = {}
    for finding in report["findings"]:
        by_check.setdefault(finding["check"], []).append(finding)
    for check, info in summary["by_check"].items():
        items = by_check.get(check, [])
        if not items:
            continue
        lines.append("")
        lines.append("=" * 100)
        lines.append(f"{check} — {info['title']}  ({len(items)} nálezů)")
        extra = {k: v for k, v in info.items() if k not in ("title", "findings")}
        if extra:
            lines.append("  " + "  ".join(f"{k}={v}" for k, v in extra.items()))
        lines.append("=" * 100)
        shown = items if not max_items else items[:max_items]
        for f in shown:
            lines.extend(_finding_lines(f))
        if len(shown) < len(items):
            lines.append(f"  … a dalších {len(items) - len(shown)} (kompletní seznam v JSON/CSV)")
    lines.append("")
    return "\n".join(lines)


def _finding_lines(f):
    head = f"[{f['severity'].upper()}] {f['product_code'] or '-'}"
    if f.get("variant_code") or f.get("variant_options"):
        head += f" / varianta {f.get('variant_code') or '-'} ({f.get('variant_options') or ''})"
    if f.get("side") and f["side"] != "both":
        head += f" [{f['side'].upper()}]"
    head += f"  {f['product_name'][:70]}" if f.get("product_name") else ""
    lines = [head, f"    {f['property']}: {f['message']}"]
    if f.get("cs_value") is not None or f.get("sk_value") is not None:
        lines.append(f"    CZ: {short(f.get('cs_value'))}")
        lines.append(f"    SK: {short(f.get('sk_value'))}")
    if f.get("expected") is not None:
        lines.append(f"    očekáváno: {short(f.get('expected'))}")
    return lines


def write_report(report, output_dir, name, max_items=0, timestamp=None):
    """Write JSON, CSV and TXT; return dict of paths and the rendered text."""
    os.makedirs(output_dir, exist_ok=True)
    ts = timestamp or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base = os.path.join(output_dir, f"{name}_{ts}")
    paths = {"json": base + ".json", "csv": base + ".csv", "txt": base + ".txt"}
    text = render_text(report, max_items=max_items)
    write_json(report, paths["json"])
    write_csv(report, paths["csv"])
    with open(paths["txt"], "w", encoding="utf-8") as handle:
        handle.write(text)
    return paths, text
