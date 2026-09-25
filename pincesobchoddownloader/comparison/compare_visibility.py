from compare_utils import get_name


def check_visibility(shared_cs, shared_sk):
    results = []
    for cs, sk in zip(shared_cs, shared_sk):
        cs_vis = cs.get('visibility')
        sk_vis = sk.get('visibility')
        cs_arch = cs.get('archive')
        sk_arch = sk.get('archive')
        if cs_vis != sk_vis or cs_arch != sk_arch:
            results.append({
                'catalogNumber': cs['catalogNumber'],
                'name': get_name(cs),
                'cs_visibility': cs_vis,
                'sk_visibility': sk_vis,
                'cs_archive': cs_arch,
                'sk_archive': sk_arch,
            })
    return results


def _categorize(results):
    cats = {
        'vis_cs_only': [],
        'vis_sk_only': [],
        'arch_cs_only': [],
        'arch_sk_only': [],
        'combined': [],
    }
    for r in results:
        vis_diff = r['cs_visibility'] != r['sk_visibility']
        arch_diff = r['cs_archive'] != r['sk_archive']
        if vis_diff and not arch_diff:
            (cats['vis_cs_only'] if r['cs_visibility'] else cats['vis_sk_only']).append(r)
        elif arch_diff and not vis_diff:
            (cats['arch_cs_only'] if r['cs_archive'] else cats['arch_sk_only']).append(r)
        else:
            cats['combined'].append(r)
    return cats


def print_report(results):
    print("\n" + "="*60)
    print(f"NESOULAD VISIBILITY / ARCHIVE  ({len(results)} produktů)")
    print("="*60)
    cats = _categorize(results)
    labels = [
        ('vis_cs_only',  'Viditelný jen v CS'),
        ('vis_sk_only',  'Viditelný jen v SK'),
        ('arch_cs_only', 'Archivovaný jen v CS'),
        ('arch_sk_only', 'Archivovaný jen v SK'),
        ('combined',     'Kombinovaný rozdíl'),
    ]
    for key, label in labels:
        items = cats[key]
        if not items:
            continue
        print(f"\n{label} ({len(items)} ks):")
        for r in items[:10]:
            print(f"  {r['catalogNumber']:<20s} "
                  f"CS(vis={r['cs_visibility']},arch={r['cs_archive']}) "
                  f"SK(vis={r['sk_visibility']},arch={r['sk_archive']})  "
                  f"{r['name'][:50]}")
        if len(items) > 10:
            print(f"  ... a dalších {len(items) - 10}")