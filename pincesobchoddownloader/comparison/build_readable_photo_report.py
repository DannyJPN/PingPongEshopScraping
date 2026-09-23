"""Build human-readable photo issue reports from Pincesobchod JSON exports."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse


def load_products(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle).get("data", [])


def product_map(products: list[dict]) -> dict[str, dict]:
    # Keep the same duplicate-code behavior as the original comparison script.
    return {p["catalogNumber"]: p for p in products if p.get("catalogNumber")}


def name(product: dict | None) -> str:
    if not product:
        return ""
    translations = product.get("translations") or {}
    for language in ("cs", "sk"):
        value = (translations.get(language) or {}).get("name")
        if value:
            return value
    return ""


def state(product: dict | None) -> str:
    if product is None:
        return "produkt neexistuje"
    if product.get("archive"):
        return "archivovaný"
    if product.get("visibility"):
        return "aktivní a viditelný"
    return "skrytý"


def image_paths(product: dict) -> set[str]:
    return {
        urlparse(image.get("url") or "").path
        for image in product.get("images") or []
    }


def issue_row(code: str, cs: dict | None, sk: dict | None, problem: str,
              assessment: str, action: str) -> dict[str, str | int]:
    cs_images = (cs or {}).get("images") or []
    sk_images = (sk or {}).get("images") or []
    return {
        "kód": code,
        "název": name(cs) or name(sk),
        "problém": problem,
        "hodnocení": assessment,
        "CZ stav": state(cs),
        "SK stav": state(sk),
        "CZ fotek": len(cs_images),
        "SK fotek": len(sk_images),
        "doporučený krok": action,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cs-json", type=Path, required=True)
    parser.add_argument("--sk-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    cs_map = product_map(load_products(args.cs_json))
    sk_map = product_map(load_products(args.sk_json))
    all_codes = sorted(set(cs_map) | set(sk_map))

    confirmed: list[dict] = []
    url_only: list[dict] = []
    no_default: list[dict] = []

    for code in all_codes:
        cs = cs_map.get(code)
        sk = sk_map.get(code)
        cs_images = (cs or {}).get("images") or []
        sk_images = (sk or {}).get("images") or []

        for shop, product, images in (("CZ", cs, cs_images), ("SK", sk, sk_images)):
            if product and images and not any(image.get("default") for image in images):
                no_default.append(issue_row(
                    code, cs, sk,
                    f"{shop}: produkt má {len(images)} fotografií, ale žádná není hlavní",
                    "potvrzený problém v metadatech",
                    f"Na {shop} označit správnou hlavní fotografii.",
                ))

        if cs is None or sk is None:
            # A missing product is not itself a photo problem. Still report a
            # photo-less existing product because the single-shop scan did so.
            existing = cs or sk
            shop = "CZ" if cs else "SK"
            if existing is not None and not (existing.get("images") or []):
                confirmed.append(issue_row(
                    code, cs, sk,
                    f"{shop}: produkt nemá žádnou fotografii; na druhém e-shopu produkt neexistuje",
                    "potvrzený problém" if state(existing) == "aktivní a viditelný" else "informativní - produkt není aktivní",
                    f"Doplnit fotografie na {shop}, pokud má být produkt znovu aktivován.",
                ))
            continue

        cs_count = len(cs_images)
        sk_count = len(sk_images)
        if cs_count == 0 and sk_count == 0:
            active_without_photos = (
                state(cs) == "aktivní a viditelný"
                or state(sk) == "aktivní a viditelný"
            )
            confirmed.append(issue_row(
                code, cs, sk,
                "CZ i SK: produkt nemá žádnou fotografii",
                "potvrzený problém" if active_without_photos else "informativní - oba produkty nejsou aktivní",
                "Doplnit fotografie na aktivní e-shop; u skrytých rozhodnout před aktivací.",
            ))
        elif cs_count == 0:
            confirmed.append(issue_row(
                code, cs, sk,
                f"CZ nemá žádnou fotografii, SK má {sk_count}",
                "potvrzený problém" if state(cs) == "aktivní a viditelný" else "informativní - CZ produkt není aktivní",
                "Prověřit a případně převzít správné fotografie ze SK na CZ.",
            ))
        elif sk_count == 0:
            confirmed.append(issue_row(
                code, cs, sk,
                f"SK nemá žádnou fotografii, CZ má {cs_count}",
                "potvrzený problém" if state(sk) == "aktivní a viditelný" else "informativní - SK produkt není aktivní",
                "Prověřit a případně převzít správné fotografie z CZ na SK.",
            ))
        elif cs_count != sk_count:
            fewer = "CZ" if cs_count < sk_count else "SK"
            confirmed.append(issue_row(
                code, cs, sk,
                f"Rozdílný počet fotografií: CZ {cs_count}, SK {sk_count}; méně má {fewer}",
                "rozdíl vyžaduje obsahovou kontrolu",
                "Porovnat obsah sad; samotný počet neurčuje, která sada je správná.",
            ))
        elif image_paths(cs) != image_paths(sk):
            url_only.append(issue_row(
                code, cs, sk,
                f"Stejný počet ({cs_count}), ale odlišná interní URL/ID fotografií",
                "není prokázána chyba fotografie",
                "Porovnat obrazový obsah nebo hashe; podle URL nelze rozhodnout.",
            ))

    confirmed.extend(no_default)
    confirmed.sort(key=lambda row: (str(row["kód"]), str(row["problém"])))
    url_only.sort(key=lambda row: str(row["kód"]))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fields = ["kód", "název", "problém", "hodnocení", "CZ stav", "SK stav",
              "CZ fotek", "SK fotek", "doporučený krok"]
    for filename, rows in (
        ("fotografie_problemy.csv", confirmed),
        ("fotografie_rozdilne_url_k_overeni.csv", url_only),
    ):
        with (args.output_dir / filename).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in confirmed:
        problem = str(row["problém"])
        if "žádnou fotografii" in problem or "nemá žádnou" in problem:
            group = "A. PRODUKT BEZ FOTOGRAFIÍ"
        elif "Rozdílný počet" in problem:
            group = "B. ROZDÍLNÝ POČET FOTOGRAFIÍ"
        else:
            group = "C. NENÍ URČENA HLAVNÍ FOTOGRAFIE"
        grouped[group].append(row)

    lines = [
        "PŘEHLED PROBLÉMŮ S FOTOGRAFIEMI - PINCESOBCHOD CZ A SK",
        "=" * 78,
        f"Zdroj CZ: {args.cs_json}",
        f"Zdroj SK: {args.sk_json}",
        "",
        "Jak přehled číst:",
        "- Bez fotografií je konkrétní, potvrzený stav.",
        "- Rozdílný počet fotografií je skutečný rozdíl, ale bez kontroly obsahu",
        "  nelze určit, který e-shop je správně.",
        "- Odlišné URL při stejném počtu nejsou v tomto souboru. Jsou v samostatném",
        "  přehledu a samy o sobě neprokazují chybu fotografie.",
        "",
        f"Položek v tomto přehledu: {len(confirmed)}",
        f"Pouhých rozdílů URL k dalšímu ověření: {len(url_only)}",
    ]

    for heading in (
        "A. PRODUKT BEZ FOTOGRAFIÍ",
        "B. ROZDÍLNÝ POČET FOTOGRAFIÍ",
        "C. NENÍ URČENA HLAVNÍ FOTOGRAFIE",
    ):
        rows = grouped.get(heading, [])
        lines.extend(["", heading + f" ({len(rows)})", "-" * 78])
        if not rows:
            lines.append("Žádné položky.")
            continue
        for row in rows:
            lines.extend([
                f"{row['kód']} : {row['název']}",
                f"  Problém: {row['problém']}",
                f"  Stav: CZ {row['CZ stav']}; SK {row['SK stav']}",
                f"  Hodnocení: {row['hodnocení']}",
                f"  Co udělat: {row['doporučený krok']}",
            ])

    (args.output_dir / "fotografie_problemy_srozumitelne.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8-sig"
    )

    url_lines = [
        "ROZDÍLNÁ URL FOTOGRAFIÍ - NEPOTVRZENÉ PROBLÉMY",
        "=" * 78,
        "Produkty mají na CZ a SK stejný počet fotografií, ale obrázky mají jiná",
        "interní ID/URL. To je běžné při samostatném nahrání stejného souboru a",
        "neprokazuje, že jsou fotografie vizuálně rozdílné nebo chybné.",
        "",
        f"Celkem položek k případnému porovnání obsahu: {len(url_only)}",
        "",
    ]
    url_lines.extend(
        f"{row['kód']} : {row['název']} : {row['CZ fotek']} fotografií : "
        f"CZ {row['CZ stav']} : SK {row['SK stav']}"
        for row in url_only
    )
    (args.output_dir / "fotografie_rozdilne_url_k_overeni.txt").write_text(
        "\n".join(url_lines) + "\n", encoding="utf-8-sig"
    )

    active_missing = [
        row for row in confirmed
        if (
            int(row["CZ fotek"]) == 0
            and row["CZ stav"] == "aktivní a viditelný"
        ) or (
            int(row["SK fotek"]) == 0
            and row["SK stav"] == "aktivní a viditelný"
        )
    ]
    active_count_diffs = [
        row for row in confirmed
        if str(row["problém"]).startswith("Rozdílný počet")
        and "aktivní a viditelný" in (row["CZ stav"], row["SK stav"])
    ]
    priority_lines = [
        "FOTOGRAFIE - PRIORITA PRO AKTIVNÍ PRODUKTY",
        "=" * 78,
        "",
        f"1. AKTIVNÍ PRODUKT BEZ FOTOGRAFIÍ ({len(active_missing)})",
        "Toto jsou potvrzené závady, které mají přímý dopad na aktivní nabídku.",
        "-" * 78,
    ]
    for row in active_missing:
        priority_lines.extend([
            f"{row['kód']} : {row['název']}",
            f"  {row['problém']}",
            f"  Stav: CZ {row['CZ stav']}; SK {row['SK stav']}",
        ])
    priority_lines.extend([
        "",
        f"2. AKTIVNÍ PRODUKT S ROZDÍLNÝM POČTEM FOTOGRAFIÍ ({len(active_count_diffs)})",
        "Jde o skutečný rozdíl, ale před opravou je nutné vizuálně určit správnou sadu.",
        "-" * 78,
    ])
    for row in active_count_diffs:
        priority_lines.append(
            f"{row['kód']} : {row['název']} : "
            f"CZ {row['CZ fotek']} / SK {row['SK fotek']} : "
            f"CZ {row['CZ stav']} / SK {row['SK stav']}"
        )
    (args.output_dir / "fotografie_aktivni_priorita.txt").write_text(
        "\n".join(priority_lines) + "\n", encoding="utf-8-sig"
    )

    # CZ-only view. SK is used solely as evidence that the CZ photo set may be
    # incomplete; SK-side defects and URL-only differences are excluded.
    cz_rows: list[dict] = []
    for code in sorted(cs_map):
        cs = cs_map[code]
        sk = sk_map.get(code)
        cs_images = cs.get("images") or []
        sk_images = (sk or {}).get("images") or []
        if not cs_images:
            sk_note = (
                f"SK má {len(sk_images)} fotografií"
                if sk_images
                else "na SK není dostupná použitelná srovnávací sada"
            )
            cz_rows.append(issue_row(
                code, cs, sk,
                f"CZ produkt nemá žádnou fotografii; {sk_note}",
                "potvrzený problém" if state(cs) == "aktivní a viditelný" else "informativní - CZ produkt není aktivní",
                "Doplnit fotografie před případnou aktivací produktu na CZ.",
            ))
        elif not any(image.get("default") for image in cs_images):
            cz_rows.append(issue_row(
                code, cs, sk,
                f"CZ produkt má {len(cs_images)} fotografií, ale žádná není hlavní",
                "potvrzený problém v metadatech",
                "Na CZ označit správnou hlavní fotografii.",
            ))
        elif sk is not None and len(cs_images) < len(sk_images):
            cz_rows.append(issue_row(
                code, cs, sk,
                f"CZ má {len(cs_images)} fotografií, SK má {len(sk_images)}",
                "podezření na neúplnou českou sadu",
                "Vizuálně porovnat sadu se SK; vyšší počet na SK sám neurčuje správnost.",
            ))

    cz_rows.sort(key=lambda row: str(row["kód"]))
    with (args.output_dir / "fotografie_CZ.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(cz_rows)

    cz_no_images = [row for row in cz_rows if int(row["CZ fotek"]) == 0]
    cz_no_default = [row for row in cz_rows if "žádná není hlavní" in str(row["problém"])]
    cz_fewer = [row for row in cz_rows if row["hodnocení"] == "podezření na neúplnou českou sadu"]
    cz_active_no_images = [
        row for row in cz_no_images if row["CZ stav"] == "aktivní a viditelný"
    ]
    cz_lines = [
        "KONTROLA FOTOGRAFIÍ - POUZE ČESKÝ PINCESOBCHOD",
        "=" * 78,
        f"Zdroj CZ: {args.cs_json}",
        f"Srovnávací zdroj SK: {args.sk_json}",
        "SK je použito pouze jako vodítko pro českou sadu fotografií.",
        "Závady slovenských produktů ani pouhé rozdíly URL zde nejsou.",
        "",
        "SOUHRN",
        f"- CZ produkt bez fotografií: {len(cz_no_images)}",
        f"- Z toho aktivní a viditelný na CZ: {len(cz_active_no_images)}",
        f"- CZ produkt bez určené hlavní fotografie: {len(cz_no_default)}",
        f"- CZ má méně fotografií než SK: {len(cz_fewer)} (nutná vizuální kontrola)",
        "",
        f"A. CZ PRODUKT BEZ FOTOGRAFIÍ ({len(cz_no_images)})",
        "-" * 78,
    ]
    for row in cz_no_images:
        cz_lines.extend([
            f"{row['kód']} : {row['název']}",
            f"  Problém: {row['problém']}",
            f"  Stav CZ: {row['CZ stav']}",
        ])
    cz_lines.extend([
        "",
        f"B. CZ NEMÁ URČENOU HLAVNÍ FOTOGRAFII ({len(cz_no_default)})",
        "-" * 78,
    ])
    if not cz_no_default:
        cz_lines.append("Žádné produkty.")
    for row in cz_no_default:
        cz_lines.extend([
            f"{row['kód']} : {row['název']}",
            f"  Problém: {row['problém']}",
            f"  Stav CZ: {row['CZ stav']}",
        ])
    cz_lines.extend([
        "",
        f"C. CZ MÁ MÉNĚ FOTOGRAFIÍ NEŽ SK ({len(cz_fewer)})",
        "Toto není potvrzená chyba. Vyšší počet na SK pouze určuje, co ověřit.",
        "-" * 78,
    ])
    for row in cz_fewer:
        cz_lines.append(
            f"{row['kód']} : {row['název']} : "
            f"CZ {row['CZ fotek']} / SK {row['SK fotek']} : CZ {row['CZ stav']}"
        )
    (args.output_dir / "fotografie_CZ_srozumitelne.txt").write_text(
        "\n".join(cz_lines) + "\n", encoding="utf-8-sig"
    )

    print(f"Confirmed/determinate rows: {len(confirmed)}")
    print(f"Active products without photos: {len(active_missing)}")
    print(f"Active products with count differences: {len(active_count_diffs)}")
    print(f"URL-only rows: {len(url_only)}")
    print(f"CZ-only rows: {len(cz_rows)}")
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
