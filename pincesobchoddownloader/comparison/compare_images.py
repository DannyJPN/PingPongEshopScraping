from compare_utils import get_name, normalize_image_url


def check_images(shared_cs, shared_sk):
    no_images_cs = []
    no_images_sk = []
    count_diffs = []
    file_diffs = []

    for cs, sk in zip(shared_cs, shared_sk):
        cs_imgs = cs.get('images') or []
        sk_imgs = sk.get('images') or []
        cs_count = len(cs_imgs)
        sk_count = len(sk_imgs)
        cat = cs['catalogNumber']
        name = get_name(cs)

        if cs_count == 0 and sk_count > 0:
            no_images_cs.append({'catalogNumber': cat, 'name': name, 'sk_count': sk_count})
        elif sk_count == 0 and cs_count > 0:
            no_images_sk.append({'catalogNumber': cat, 'name': name, 'cs_count': cs_count})
        elif cs_count != sk_count:
            count_diffs.append({
                'catalogNumber': cat, 'name': name,
                'cs_count': cs_count, 'sk_count': sk_count,
                'diff': abs(cs_count - sk_count),
            })
        else:
            cs_paths = {normalize_image_url(img.get('url', '')) for img in cs_imgs}
            sk_paths = {normalize_image_url(img.get('url', '')) for img in sk_imgs}
            if cs_paths != sk_paths:
                file_diffs.append({
                    'catalogNumber': cat, 'name': name, 'count': cs_count,
                    'cs_only': sorted(cs_paths - sk_paths),
                    'sk_only': sorted(sk_paths - cs_paths),
                })

    count_diffs.sort(key=lambda x: x['diff'], reverse=True)
    return {
        'no_images_cs': no_images_cs,
        'no_images_sk': no_images_sk,
        'count_diffs': count_diffs,
        'file_diffs': file_diffs,
    }


def print_report(results):
    print("\n" + "="*60)
    print("OBRÁZKY")
    print("="*60)
    print(f"Bez obrázků v CS, má je SK:     {len(results['no_images_cs'])}")
    print(f"Bez obrázků v SK, má je CS:     {len(results['no_images_sk'])}")
    print(f"Různý počet obrázků:            {len(results['count_diffs'])}")
    print(f"Stejný počet, různé soubory:    {len(results['file_diffs'])}")

    for label, items, other_key in [
        ("Bez obrázků v CS (SK má):", results['no_images_cs'], 'sk_count'),
        ("Bez obrázků v SK (CS má):", results['no_images_sk'], 'cs_count'),
    ]:
        if items:
            print(f"\n{label}")
            for r in items[:15]:
                print(f"  {r['catalogNumber']:<20s} druhá strana má {r[other_key]} fotek  {r['name'][:55]}")
            if len(items) > 15:
                print(f"  ... a dalších {len(items) - 15}")

    if results['count_diffs']:
        print(f"\nRůzný počet obrázků (prvních 15):")
        for r in results['count_diffs'][:15]:
            print(f"  {r['catalogNumber']:<20s} CS={r['cs_count']} SK={r['sk_count']} (Δ{r['diff']})  {r['name'][:55]}")

    if results['file_diffs']:
        print(f"\nStejný počet, různé soubory (prvních 10):")
        for r in results['file_diffs'][:10]:
            print(f"  {r['catalogNumber']:<20s} ({r['count']} fotek)  {r['name'][:45]}")
            for path in r['cs_only'][:2]:
                print(f"    jen CS: {path}")
            for path in r['sk_only'][:2]:
                print(f"    jen SK: {path}")
