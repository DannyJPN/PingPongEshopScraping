"""Command line handling shared by all CS vs SK scripts."""
import argparse
import logging
import os
import sys

from cssklib.checks import CHECKS, Context, run_check
from cssklib.constants import (
    CZK_PER_EUR, DEFAULT_CS_DIR, DEFAULT_IMAGE_CACHE_DIR, DEFAULT_REPORT_DIR, DEFAULT_SK_DIR,
    PRICE_TOLERANCE, VAT_RATES,
)
from cssklib.loader import resolve_source
from cssklib.pairing import pair_products
from cssklib.pricing import PriceConfig
from cssklib.report import build_report, render_text, write_report
from cssklib.values import is_active

EXIT_OK, EXIT_FINDINGS, EXIT_ERROR = 0, 1, 2


def add_common_arguments(parser):
    src = parser.add_argument_group("zdroje")
    src.add_argument("--cs-dir", default=DEFAULT_CS_DIR, help="Složka CZ downloaderu (obsahuje Full_*)")
    src.add_argument("--sk-dir", default=DEFAULT_SK_DIR, help="Složka SK downloaderu (obsahuje Full_*)")
    src.add_argument("--cs-json", help="Konkrétní CZ JSON (přebije --cs-dir)")
    src.add_argument("--sk-json", help="Konkrétní SK JSON (přebije --sk-dir)")
    src.add_argument("--pullnewest", action="store_true",
                     help="Stáhnout nejnovější JSONy mechanismem pincesobchod downloaderu "
                          "(potřebuje JZ_BEARER_TOKEN_CS / JZ_BEARER_TOKEN_SK)")
    src.add_argument("--sides", choices=["cs", "sk", "both"], default="both",
                     help="Které e-shopy kontrolovat u kontrol v rámci jednoho e-shopu (výchozí oba)")
    src.add_argument("--active-only", action="store_true",
                     help="Porovnávat jen produkty aktivní (viditelné a nearchivované) aspoň na jedné straně")

    out = parser.add_argument_group("report")
    out.add_argument("--output-dir", default=DEFAULT_REPORT_DIR, help="Složka pro reporty")
    out.add_argument("--report-name", help="Základ názvu souborů reportu")
    out.add_argument("--max-text-items", type=int, default=0,
                     help="Max. vypsaných nálezů na kontrolu v TXT/konzoli (0 = vše)")
    out.add_argument("--quiet", action="store_true", help="Na konzoli vypsat jen souhrn")
    out.add_argument("--debug", action="store_true", help="Debug logování")

    price = parser.add_argument_group("ceny")
    price.add_argument("--tolerance", type=float, default=PRICE_TOLERANCE, help="Tolerance přepočtů")
    price.add_argument("--vat-cs", type=float, default=VAT_RATES["cs"], help="DPH CZ v %%")
    price.add_argument("--vat-sk", type=float, default=VAT_RATES["sk"], help="DPH SK v %%")
    price.add_argument("--czk-per-eur", type=float, default=CZK_PER_EUR, help="Kurz pro přepočet CZK → EUR")


def add_image_arguments(parser):
    group = parser.add_argument_group("fotky")
    group.add_argument("--image-cache-dir", default=DEFAULT_IMAGE_CACHE_DIR,
                       help="Cache stažených fotek (pro hash a vision)")
    group.add_argument("--workers", type=int, default=8, help="Počet paralelních stahování fotek")


def add_vision_arguments(parser, prefix=""):
    group = parser.add_argument_group("OpenAI vision")
    group.add_argument(f"--{prefix}model", dest="vision_model", help="Model (výchozí env PINCESOBCHOD_VISION_MODEL nebo gpt-4o)")
    group.add_argument(f"--{prefix}side", dest="vision_side", choices=["cs", "sk", "both"], default="cs",
                       help="Které JSONy kontrolovat (výchozí cs)")
    group.add_argument(f"--{prefix}codes", dest="vision_codes", nargs="*", default=[], help="Jen tyto kódy produktů")
    group.add_argument(f"--{prefix}brands", dest="vision_brands", nargs="*", default=[], help="Jen tyto značky")
    group.add_argument(f"--{prefix}limit", dest="vision_limit", type=int, default=0, help="Max. počet produktů (0 = vše)")
    group.add_argument(f"--{prefix}max-images", dest="vision_max_images", type=int, default=0,
                       help="Max. fotek na produkt (0 = vše)")
    group.add_argument(f"--{prefix}detail", dest="vision_detail", choices=["low", "high", "auto"], default="low",
                       help="Detail obrázku pro OpenAI (low je nejlevnější)")
    group.add_argument(f"--{prefix}cache", dest="vision_cache",
                       help="JSONL cache výsledků (výchozí <output-dir>/vision_cache.jsonl)")
    group.add_argument(f"--{prefix}refresh", dest="vision_refresh", action="store_true",
                       help="Ignorovat cache a vyhodnotit znovu")
    group.add_argument(f"--{prefix}embed-images", dest="vision_embed", action="store_true",
                       help="Posílat obrázky jako base64 (stažené do cache) místo URL")
    group.add_argument(f"--{prefix}dry-run", dest="vision_dry_run", action="store_true",
                       help="Jen spočítat, kolik fotek by se poslalo do OpenAI")


def setup_logging(debug):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", force=True)


def _filter_active(pairing):
    pairing.matched = [(c, s) for c, s in pairing.matched if is_active(c) or is_active(s)]
    pairing.name_conflicts = [(c, s) for c, s in pairing.name_conflicts if is_active(c) or is_active(s)]
    pairing.cs_only = [p for p in pairing.cs_only if is_active(p)]
    pairing.sk_only = [p for p in pairing.sk_only if is_active(p)]
    return pairing


def build_context(args, checks, image_store_factory=None, vision_checker_factory=None):
    cs_path, cs_products = resolve_source("cs", args.cs_dir, args.cs_json, args.pullnewest)
    sk_path, sk_products = resolve_source("sk", args.sk_dir, args.sk_json, args.pullnewest)
    logging.info(f"CZ: {cs_path} ({len(cs_products)} produktů)")
    logging.info(f"SK: {sk_path} ({len(sk_products)} produktů)")
    pairing = pair_products(cs_products, sk_products)
    if args.active_only:
        _filter_active(pairing)
    price_config = PriceConfig(vat_rates={"cs": args.vat_cs, "sk": args.vat_sk},
                               czk_per_eur=args.czk_per_eur, tolerance=args.tolerance)
    ctx = Context(cs_products=cs_products, sk_products=sk_products, pairing=pairing,
                  price_config=price_config, active_only=args.active_only,
                  shop_sides=("cs", "sk") if args.sides == "both" else (args.sides,))
    ids = {c.id for c in checks}
    needs_images = "images_hash" in ids or ("vision" in ids and getattr(args, "vision_embed", False))
    if needs_images:
        if image_store_factory is None:
            from cssklib.images import ImageStore
            image_store_factory = lambda: ImageStore(args.image_cache_dir, workers=args.workers)  # noqa: E731
        ctx.image_store = image_store_factory()
    if "vision" in ids:
        if vision_checker_factory is None:
            from cssklib.vision import VisionChecker
            vision_checker_factory = VisionChecker
        cache = args.vision_cache or os.path.join(args.output_dir, "vision_cache.jsonl")
        checker = vision_checker_factory(
            model=args.vision_model, cache_path=cache, detail=args.vision_detail,
            max_images=args.vision_max_images, embed_images=args.vision_embed,
            image_store=ctx.image_store, refresh=args.vision_refresh)
        ctx.vision = {"checker": checker, "side": args.vision_side, "codes": args.vision_codes,
                      "brands": args.vision_brands, "limit": args.vision_limit,
                      "dry_run": args.vision_dry_run}
    sources = {"cs": {"path": cs_path, "products": len(cs_products)},
               "sk": {"path": sk_path, "products": len(sk_products)}}
    return ctx, sources


def execute(args, checks, report_name, **factories):
    """Run checks, write report, print it; return exit code."""
    setup_logging(args.debug)
    try:
        ctx, sources = build_context(args, checks, **factories)
        results = []
        for check in checks:
            logging.info(f"Kontrola: {check.id} — {check.title}")
            results.append(run_check(check, ctx))
    except Exception as exc:
        logging.error(f"Chyba: {exc}", exc_info=args.debug)
        return EXIT_ERROR
    options = {"active_only": args.active_only, "sides": args.sides, "tolerance": args.tolerance,
               "vat": {"cs": args.vat_cs, "sk": args.vat_sk}, "czk_per_eur": args.czk_per_eur}
    report = build_report(results, sources, ctx.pairing.summary(), options=options)
    paths, text = write_report(report, args.output_dir, args.report_name or report_name,
                               max_items=args.max_text_items)
    _print(render_text(report, summary_only=True) if args.quiet else text)
    print(f"\nReport: {paths['txt']}\n        {paths['json']}\n        {paths['csv']}")
    return EXIT_FINDINGS if report["summary"]["total_findings"] else EXIT_OK


def _print(text):
    stream = sys.stdout
    try:
        stream.write(text + "\n")
    except UnicodeEncodeError:
        stream.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def run_single_check(check_id, argv=None, **factories):
    """Entry point of check_<id>.py scripts."""
    check = CHECKS[check_id]
    parser = argparse.ArgumentParser(description=f"Pincesobchod CZ vs SK — {check.title}")
    add_common_arguments(parser)
    if check.group in ("images", "vision"):
        add_image_arguments(parser)
    if check.id == "vision":
        add_vision_arguments(parser)
    args = parser.parse_args(argv)
    return execute(args, [check], f"cs_sk_{check_id}", **factories)


def build_all_parser():
    parser = argparse.ArgumentParser(
        description="Pincesobchod CZ vs SK — hromadná kontrola (libovolný rozdíl CZ vs SK)",
        allow_abbrev=False)
    add_common_arguments(parser)
    add_image_arguments(parser)
    add_vision_arguments(parser, prefix="vision-")
    sel = parser.add_argument_group("výběr kontrol",
                                    "Každou kontrolu lze zapnout/vypnout přepínačem --<id> / --no-<id>. "
                                    "Výchozí: vše kromě 'vision' (drahé OpenAI volání).")
    sel.add_argument("--only", nargs="+", metavar="ID", help="Spustit jen tyto kontroly")
    sel.add_argument("--skip", nargs="+", metavar="ID", default=[], help="Vynechat tyto kontroly")
    sel.add_argument("--group", nargs="+", choices=sorted({c.group for c in CHECKS.values()}),
                     help="Spustit jen kontroly z těchto skupin")
    sel.add_argument("--list-checks", action="store_true", help="Vypsat dostupné kontroly a skončit")
    for check in CHECKS.values():
        sel.add_argument(f"--{check.id}", dest=f"check__{check.id}", action=argparse.BooleanOptionalAction,
                         default=None, help=check.title.replace("%", "%%"))
    return parser


def select_checks(args):
    unknown = [c for c in (args.only or []) + args.skip if c not in CHECKS]
    if unknown:
        raise SystemExit(f"Neznámé kontroly: {', '.join(unknown)} (viz --list-checks)")
    selected = []
    for check in CHECKS.values():
        explicit = getattr(args, f"check__{check.id}")
        if args.only is not None:
            enabled = check.id in args.only
        elif args.group is not None:
            enabled = check.group in args.group and (check.default_enabled or explicit is True)
        else:
            enabled = check.default_enabled
        if explicit is not None:
            enabled = explicit
        if check.id in args.skip:
            enabled = False
        if enabled:
            selected.append(check)
    return selected


def run_all(argv=None, default_groups=None, report_name="cs_sk_all", **factories):
    """Entry point of check_all.py (and check_shop_all.py with default_groups=['shop'])."""
    parser = build_all_parser()
    if default_groups:
        parser.set_defaults(group=list(default_groups))
    args = parser.parse_args(argv)
    if args.list_checks:
        for check in CHECKS.values():
            flag = "" if check.default_enabled else "  [výchozí vypnuto]"
            print(f"{check.id:<28} {check.group:<9} {check.title}{flag}")
        return EXIT_OK
    checks = select_checks(args)
    if not checks:
        print("Žádná kontrola není vybrána.")
        return EXIT_ERROR
    return execute(args, checks, report_name, **factories)


def run_vision(argv=None, require_codes=False, **factories):
    """Entry point of check_photos_vision*.py scripts."""
    parser = argparse.ArgumentParser(
        description="Pincesobchod — OpenAI vizuální kontrola, zda fotky zobrazují produkt "
                    "(nebo s ním souvisí, např. velikostní tabulka)", allow_abbrev=False)
    add_common_arguments(parser)
    add_image_arguments(parser)
    add_vision_arguments(parser)
    args = parser.parse_args(argv)
    if require_codes and not args.vision_codes:
        parser.error("zadejte --codes KÓD [KÓD ...] (pro všechny produkty použijte check_photos_vision_all.py)")
    name = "cs_sk_vision" if not require_codes else "cs_sk_vision_" + "_".join(args.vision_codes[:3])
    return execute(args, [CHECKS["vision"]], name, **factories)
