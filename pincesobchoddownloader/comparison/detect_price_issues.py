"""
Kontrola cen:
  A) Aktivní produkty bez standardPrice (běžné ceny)
  B) Produkty kde prodejní cena (price s DPH) > standardPrice
     (pouze pro produkty s price > 0)
"""
import os
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"


def get_vat_rate(product):
    vat = product.get('vat')
    if isinstance(vat, dict):
        return float(vat.get('rate', 21))
    return 21.0


def get_price(product):
    val = product.get('price')
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def get_standard_price(product):
    val = product.get('standardPrice')
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def check_price_issues(products):
    missing_standard = []
    price_above_standard = []

    for p in products:
        price    = get_price(p)
        standard = get_standard_price(p)
        active   = is_active(p)

        # A: chybějící standardPrice — hlásit jen aktivní
        if standard is None or standard == 0.0:
            if active:
                missing_standard.append({
                    'catalogNumber': p.get('catalogNumber') or '(prázdný)',
                    'name': get_name(p),
                    'active': active,
                    'price': price,
                    'standard': standard,
                })
            continue

        # B: prodejní cena nad standardPrice — jen pokud price > 0
        if price and price > 0:
            vat_rate    = get_vat_rate(p)
            price_incl  = round(price * (1 + vat_rate / 100), 2)
            if price_incl - standard > 0.10:  # tolerance 10 haléřů pro zaokrouhlení
                price_above_standard.append({
                    'catalogNumber': p.get('catalogNumber') or '(prázdný)',
                    'name': get_name(p),
                    'active': active,
                    'price_excl': price,
                    'price_incl': price_incl,
                    'standard': standard,
                    'vat_rate': vat_rate,
                    'diff': round(price_incl - standard, 2),
                })

    missing_standard.sort(key=lambda x: x['catalogNumber'])
    price_above_standard.sort(key=lambda x: (not x['active'], -x['diff']))
    return missing_standard, price_above_standard


def write_report(missing_standard, price_above_standard, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"price_issues_{ts}.txt")

    lines = []
    lines.append("KONTROLA CEN")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Chybějící standardPrice (aktivní): {len(missing_standard)}")
    lines.append(f"Prodejní cena nad standardPrice:   {len(price_above_standard)}")
    lines.append("=" * 72)

    # A
    if missing_standard:
        lines.append(f"\nA — AKTIVNÍ PRODUKTY BEZ STANDARDPRICE ({len(missing_standard)} ks):")
        lines.append("Produkt nemá vyplněnou běžnou cenu (přeškrtnutá cena na webu).")
        lines.append("-" * 72)
        for r in missing_standard:
            lines.append(f"  {r['catalogNumber']:<22s}  price={r['price']}  {r['name'][:48]}")
    else:
        lines.append("\nA — standardPrice: všechny aktivní produkty mají vyplněno — OK")

    # B
    if price_above_standard:
        active   = [r for r in price_above_standard if r['active']]
        inactive = [r for r in price_above_standard if not r['active']]
        lines.append(f"\n\nB — PRODEJNÍ CENA NAD STANDARDPRICE ({len(price_above_standard)} ks):")
        lines.append("Cena s DPH je vyšší než běžná cena — pravděpodobně chyba zadání.")
        lines.append("-" * 72)
        for section, items in [("AKTIVNÍ", active), ("Neaktivní", inactive)]:
            if not items:
                continue
            lines.append(f"\n  [{section}]")
            for r in items:
                lines.append(
                    f"  {r['catalogNumber']:<22s}  "
                    f"prodej={r['price_excl']} bez DPH → {r['price_incl']} s DPH  "
                    f"standard={r['standard']}  rozdíl=+{r['diff']}"
                )
                lines.append(f"    {r['name'][:65]}")
    else:
        lines.append("\n\nB — prodejní ceny: žádná není nad standardPrice — OK")

    text = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path, text


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--cs-dir',     default=DEFAULT_CS_DIR)
    p.add_argument('--output-dir', default=DEFAULT_OUT_DIR)
    args = p.parse_args()

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    cs_products, _, cs_path = load_latest_json(args.cs_dir, "CS")
    print(f"CS: {cs_path}  ({len(cs_products)} produktů)")

    missing_standard, price_above_standard = check_price_issues(cs_products)
    print(f"Chybějící standardPrice (aktivní): {len(missing_standard)}")
    print(f"Prodejní cena nad standardPrice:   {len(price_above_standard)}")

    path, text = write_report(missing_standard, price_above_standard, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()