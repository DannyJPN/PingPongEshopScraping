"""Create a CZ-only, readable report from the existing photo audit outputs."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ITEM_RE = re.compile(r"^\s{2}(\S+)\s{2,}(.+?)\s*$")


def load_map(path: Path) -> dict[str, dict]:
    with path.open("r", encoding="utf-8") as handle:
        products = json.load(handle).get("data", [])
    return {p["catalogNumber"]: p for p in products if p.get("catalogNumber")}


def product_name(product: dict) -> str:
    translations = product.get("translations") or {}
    return (
        (translations.get("cs") or {}).get("name")
        or (translations.get("sk") or {}).get("name")
        or ""
    )


def normalize_name(value: str) -> str:
    return " ".join(value.casefold().split())


def state(product: dict | None) -> str:
    if not product:
        return "nenalezen v referenčním JSONu"
    if product.get("archive"):
        return "archivovaný"
    if product.get("visibility"):
        return "aktivní a viditelný"
    return "skrytý"


def parse_no_image_report(path: Path) -> list[tuple[str, str]]:
    rows = []
    in_inactive_section = False
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if "Neaktivní bez obrázku" in line:
            in_inactive_section = True
            continue
        if in_inactive_section and line.startswith("B "):
            break
        if in_inactive_section:
            match = ITEM_RE.match(line)
            if match:
                rows.append((match.group(1), match.group(2)))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-image-report", type=Path, required=True)
    parser.add_argument("--comparison-cs-json", type=Path, required=True)
    parser.add_argument("--comparison-sk-json", type=Path, required=True)
    parser.add_argument("--reference-cs-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    no_images = parse_no_image_report(args.no_image_report)
    comparison_cs = load_map(args.comparison_cs_json)
    comparison_sk = load_map(args.comparison_sk_json)
    reference_cs = load_map(args.reference_cs_json)
    reference_by_name = {
        normalize_name(product_name(product)): product
        for product in reference_cs.values()
        if product_name(product)
    }

    rows: list[dict[str, str | int]] = []
    for reported_code, reported_name in no_images:
        exact = reference_cs.get(reported_code)
        by_name = reference_by_name.get(normalize_name(reported_name))
        reference = exact or by_name
        actual_code = reference.get("catalogNumber", "") if reference else ""
        code_note = ""
        if actual_code and actual_code != reported_code:
            code_note = f"Report uvádí {reported_code}, referenční JSON podle přesného názvu uvádí {actual_code}."
        sk = comparison_sk.get(reported_code) or comparison_sk.get(actual_code)
        sk_count = len((sk or {}).get("images") or [])
        rows.append({
            "kód z reportu": reported_code,
            "kód v referenčním CZ JSONu": actual_code,
            "název": reported_name,
            "problém": "CZ produkt nemá žádnou fotografii",
            "stav CZ": state(reference),
            "srovnání SK": f"SK má {sk_count} fotografií" if sk_count else "SK neposkytuje fotografii ke převzetí",
            "poznámka ke kódu": code_note,
        })

    fewer: list[dict[str, str | int]] = []
    for code in sorted(set(comparison_cs) & set(comparison_sk)):
        cs = comparison_cs[code]
        sk = comparison_sk[code]
        cs_count = len(cs.get("images") or [])
        sk_count = len(sk.get("images") or [])
        if 0 < cs_count < sk_count:
            fewer.append({
                "kód": code,
                "název": product_name(cs),
                "CZ fotek": cs_count,
                "SK fotek": sk_count,
                "stav CZ": state(cs),
            })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "fotografie_CZ_pouze.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fields = ["kód z reportu", "kód v referenčním CZ JSONu", "název",
                  "problém", "stav CZ", "srovnání SK", "poznámka ke kódu"]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    with (args.output_dir / "fotografie_CZ_k_vizualni_kontrole.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fields = ["kód", "název", "CZ fotek", "SK fotek", "stav CZ"]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(fewer)

    active_missing = sum(row["stav CZ"] == "aktivní a viditelný" for row in rows)
    lines = [
        "FOTOGRAFIE - POUZE ČESKÝ PINCESOBCHOD",
        "=" * 78,
        f"Zdroj kontroly: {args.no_image_report}",
        "",
        "VÝSLEDEK ČESKÉ KONTROLY",
        f"- Produkty bez fotografie: {len(rows)}",
        f"- Z toho aktivní a viditelné: {active_missing}",
        "- Produkty s fotografiemi, ale bez určené hlavní fotografie: 0",
        "",
        "A. POTVRZENÉ ČESKÉ NÁLEZY",
        "-" * 78,
    ]
    for row in rows:
        lines.extend([
            f"{row['kód z reportu']} : {row['název']}",
            f"  Problém: {row['problém']}",
            f"  Stav CZ: {row['stav CZ']}",
            f"  Pomoc ze SK: {row['srovnání SK']}",
        ])
        if row["poznámka ke kódu"]:
            lines.append(f"  POZOR: {row['poznámka ke kódu']}")

    lines.extend([
        "",
        f"B. PODEZŘENÍ NA NEÚPLNOU ČESKOU SADU ({len(fewer)})",
        "CZ má méně fotografií než SK. Nejde o potvrzenou chybu; obsah je nutné",
        "vizuálně porovnat. Případy, kdy má méně fotografií SK, zde nejsou.",
        "-" * 78,
    ])
    for row in fewer:
        lines.append(
            f"{row['kód']} : {row['název']} : CZ {row['CZ fotek']} / "
            f"SK {row['SK fotek']} : {row['stav CZ']}"
        )

    (args.output_dir / "fotografie_CZ_pouze.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8-sig"
    )
    print(f"CZ without photos: {len(rows)} (active: {active_missing})")
    print(f"CZ fewer photos than SK: {len(fewer)}")
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
