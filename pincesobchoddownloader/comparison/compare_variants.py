from compare_utils import get_name


def check_variants(shared_cs, shared_sk, cs_all, sk_all):
    count_diffs = []
    for cs, sk in zip(shared_cs, shared_sk):
        cs_count = len(cs.get('variants') or [])
        sk_count = len(sk.get('variants') or [])
        if cs_count != sk_count:
            count_diffs.append({
                'catalogNumber': cs['catalogNumber'],
                'name': get_name(cs),
                'cs_count': cs_count,
                'sk_count': sk_count,
                'diff': abs(cs_count - sk_count),
            })
    count_diffs.sort(key=lambda x: x['diff'], reverse=True)

    def collect_option_types(products):
        types = set()
        for p in products:
            for v in (p.get('variants') or []):
                for opt in (v.get('options') or []):
                    if opt.get('name'):
                        types.add(opt['name'])
        return types

    cs_opts = collect_option_types(cs_all)
    sk_opts = collect_option_types(sk_all)
    return {
        'count_diffs': count_diffs,
        'cs_only_options': sorted(cs_opts - sk_opts),
        'sk_only_options': sorted(sk_opts - cs_opts),
        'common_options': sorted(cs_opts & sk_opts),
    }


def print_report(results):
    print("\n" + "="*60)
    print(f"VARIANTY  ({len(results['count_diffs'])} produktů s různým počtem)")
    print("="*60)
    if results['cs_only_options']:
        print(f"Option typy jen v CS: {results['cs_only_options']}")
    if results['sk_only_options']:
        print(f"Option typy jen v SK: {results['sk_only_options']}")
    print(f"Společné option typy ({len(results['common_options'])}): {results['common_options']}")

    if results['count_diffs']:
        print(f"\nTop 20 produktů s největším rozdílem variant:")
        for r in results['count_diffs'][:20]:
            print(f"  {r['catalogNumber']:<20s} CS={r['cs_count']:3d} SK={r['sk_count']:3d} "
                  f"(Δ{r['diff']})  {r['name'][:55]}")
