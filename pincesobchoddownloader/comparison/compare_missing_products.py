from compare_utils import get_name, is_active


def check_missing_products(cs_only, sk_only):
    def split(products):
        active = [p for p in products if is_active(p)]
        inactive = [p for p in products if not is_active(p)]
        return active, inactive

    cs_active, cs_inactive = split(cs_only)
    sk_active, sk_inactive = split(sk_only)
    return {
        'cs_only_active': cs_active,
        'cs_only_inactive': cs_inactive,
        'sk_only_active': sk_active,
        'sk_only_inactive': sk_inactive,
    }


def print_report(results):
    print("\n" + "="*60)
    print("CHYBĚJÍCÍ PRODUKTY (pouze na jedné straně)")
    print("="*60)
    cs_a = results['cs_only_active']
    cs_i = results['cs_only_inactive']
    sk_a = results['sk_only_active']
    sk_i = results['sk_only_inactive']
    print(f"Pouze v CS: {len(cs_a)} aktivních, {len(cs_i)} neaktivních")
    print(f"Pouze v SK: {len(sk_a)} aktivních, {len(sk_i)} neaktivních")

    for label, items in [
        ("Aktivní pouze v CS:", cs_a),
        ("Aktivní pouze v SK:", sk_a),
    ]:
        if items:
            print(f"\n{label}")
            for p in items:
                print(f"  {p['catalogNumber']:<20s} vis={p['visibility']} arch={p['archive']}  {get_name(p)[:70]}")

    for label, items in [
        ("Neaktivní pouze v CS (prvních 10):", cs_i),
        ("Neaktivní pouze v SK (prvních 10):", sk_i),
    ]:
        if items:
            print(f"\n{label}")
            for p in items[:10]:
                print(f"  {p['catalogNumber']:<20s} vis={p['visibility']} arch={p['archive']}  {get_name(p)[:70]}")
            if len(items) > 10:
                print(f"  ... a dalších {len(items) - 10}")