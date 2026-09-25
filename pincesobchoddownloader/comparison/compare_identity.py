import difflib
from compare_utils import get_name, normalize_name


def check_identity(shared_cs, shared_sk):
    manufacturer_mismatch = []
    name_mismatch = []
    name_suspicious = []

    for cs, sk in zip(shared_cs, shared_sk):
        cat = cs['catalogNumber']
        cs_name = get_name(cs)
        sk_name = get_name(sk)

        cs_mfr = (cs.get('manufacturer') or {}).get('id')
        sk_mfr = (sk.get('manufacturer') or {}).get('id')
        if cs_mfr and sk_mfr and cs_mfr != sk_mfr:
            manufacturer_mismatch.append({
                'catalogNumber': cat,
                'name_cs': cs_name,
                'name_sk': sk_name,
                'cs_manufacturer': cs_mfr,
                'sk_manufacturer': sk_mfr,
            })

        cs_norm = normalize_name(cs_name)
        sk_norm = normalize_name(sk_name)
        if cs_norm != sk_norm:
            ratio = difflib.SequenceMatcher(None, cs_norm, sk_norm).ratio()
            entry = {
                'catalogNumber': cat,
                'name_cs': cs_name,
                'name_sk': sk_name,
                'similarity': ratio,
            }
            if ratio < 0.85:
                name_mismatch.append(entry)
            else:
                name_suspicious.append(entry)

    name_mismatch.sort(key=lambda x: x['similarity'])
    name_suspicious.sort(key=lambda x: x['similarity'])
    return {
        'manufacturer_mismatch': manufacturer_mismatch,
        'name_mismatch': name_mismatch,
        'name_suspicious': name_suspicious,
    }


def print_report(results):
    print("\n" + "="*60)
    print("IDENTITA PRODUKTŮ (stejný kód, jiný produkt?)")
    print("="*60)
    print(f"Různý manufacturer:           {len(results['manufacturer_mismatch'])}")
    print(f"Různý název (<85 % shoda):    {len(results['name_mismatch'])}")
    print(f"Podezřelý název (85–99 %):    {len(results['name_suspicious'])}")

    if results['manufacturer_mismatch']:
        print("\nRůzný manufacturer:")
        for r in results['manufacturer_mismatch']:
            print(f"  {r['catalogNumber']:<20s} CS_mfr={r['cs_manufacturer']} SK_mfr={r['sk_manufacturer']}  {r['name_cs'][:50]}")

    if results['name_mismatch']:
        print("\nRůzný název (nejhorší případy):")
        for r in results['name_mismatch'][:30]:
            print(f"  {r['catalogNumber']:<20s} [{r['similarity']:.0%}]")
            print(f"    CS: {r['name_cs'][:80]}")
            print(f"    SK: {r['name_sk'][:80]}")

    if results['name_suspicious']:
        print(f"\nPodezřelý název (prvních 15):")
        for r in results['name_suspicious'][:15]:
            print(f"  {r['catalogNumber']:<20s} [{r['similarity']:.0%}]  "
                  f"CS: {r['name_cs'][:40]}  SK: {r['name_sk'][:40]}")
