import json
import os
import subprocess
import sys

import pytest

from cssklib import cli
from cssklib.checks import CHECKS
from cssklib.images import ImageStore
from conftest import make_product, make_variant, sk_twin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def sources(write_json):
    cs = make_product(variants=[make_variant("BTY01000001-01", [("Barva", "černá")])])
    sk = sk_twin(cs)
    sk["visibility"] = False
    other = make_product("XXX1", "Jen CZ", visibility=False)
    return write_json([cs, other], "cs.json"), write_json([sk], "sk.json")


def _args(sources, tmp_path, *extra):
    return ["--cs-json", sources[0], "--sk-json", sources[1], "--output-dir", str(tmp_path / "out"), *extra]


def _load(tmp_path, prefix):
    folder = tmp_path / "out"
    name = sorted(f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith(".json"))[-1]
    with open(folder / name, encoding="utf-8") as handle:
        return json.load(handle)


def test_single_check_script_api(sources, tmp_path, capsys):
    assert cli.run_single_check("visibility", _args(sources, tmp_path)) == cli.EXIT_FINDINGS
    report = _load(tmp_path, "cs_sk_visibility_")
    assert report["checks"] == ["visibility"]
    assert report["pairing"]["matched"] == 1 and report["pairing"]["cs_only"] == 1
    assert "visibility" in capsys.readouterr().out
    assert cli.run_single_check("ean", _args(sources, tmp_path, "--report-name", "x")) == cli.EXIT_OK


def test_single_and_bulk_reports_share_format(sources, tmp_path):
    cli.run_single_check("visibility", _args(sources, tmp_path))
    cli.run_all(_args(sources, tmp_path, "--only", "visibility", "ean", "--quiet"))
    single, bulk = _load(tmp_path, "cs_sk_visibility_"), _load(tmp_path, "cs_sk_all_")
    assert set(single) == set(bulk)
    assert single["findings"] == [f for f in bulk["findings"] if f["check"] == "visibility"]
    assert bulk["checks"] == ["ean", "visibility"]  # registry order


def test_active_only(sources, tmp_path):
    cli.run_single_check("identity", _args(sources, tmp_path, "--active-only"))
    report = _load(tmp_path, "cs_sk_identity_")
    assert report["pairing"]["cs_only"] == 0 and report["options"]["active_only"] is True


def test_missing_sources_return_error(tmp_path):
    code = cli.run_single_check("ean", ["--cs-dir", str(tmp_path / "x"), "--sk-dir", str(tmp_path / "y"),
                                        "--output-dir", str(tmp_path)])
    assert code == cli.EXIT_ERROR


def test_select_checks_toggles():
    parser = cli.build_all_parser()
    ids = lambda argv: [c.id for c in cli.select_checks(parser.parse_args(argv))]  # noqa: E731
    default = ids([])
    assert "vision" not in default and "images_hash" in default and "identity" in default
    assert "vision" in ids(["--vision"])
    assert "images_hash" not in ids(["--no-images_hash"])
    assert ids(["--only", "price", "vat"]) == ["vat", "price"]
    assert ids(["--only", "price", "--no-price"]) == []
    assert "feeds" not in ids(["--skip", "feeds"])
    assert set(ids(["--group", "price"])) == {"price", "standardPrice"}
    shop = ids(["--group", "shop"])
    assert {"vat", "price_vat", "variant_price_vat", "shop_name_metaTitle", "shop_slug"} <= set(shop)
    assert all(CHECKS[c].group == "shop" for c in shop)
    assert "vision" in ids(["--group", "vision", "--vision"]) and ids(["--group", "vision"]) == []
    with pytest.raises(SystemExit):
        cli.select_checks(parser.parse_args(["--only", "nope"]))


def test_run_all_list_and_empty(capsys, sources, tmp_path):
    assert cli.run_all(["--list-checks"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "vision" in out and "[výchozí vypnuto]" in out
    assert cli.run_all(_args(sources, tmp_path, "--only", "ean", "--no-ean")) == cli.EXIT_ERROR


def test_run_all_with_image_hash_and_vision(sources, tmp_path):
    store = ImageStore(str(tmp_path / "img"), fetch=lambda url: b"x")

    class Checker:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.model, self.max_images, self.refresh = "m", 0, False
            self.usage = {}

        def check_product(self, product, side):
            return [{"index": 1, "url": "u", "verdict": "unrelated", "reason": "jiný produkt", "cached": False}]

    created = {}

    def factory(**kwargs):
        created["checker"] = Checker(**kwargs)
        return created["checker"]

    code = cli.run_all(_args(sources, tmp_path, "--only", "images_hash", "vision", "--vision-codes",
                             "BTY01000001", "--vision-max-images", "2", "--quiet"),
                       image_store_factory=lambda: store, vision_checker_factory=factory)
    assert code == cli.EXIT_FINDINGS
    report = _load(tmp_path, "cs_sk_all_")
    assert report["summary"]["by_check"]["images_hash"]["findings"] == 0
    assert [f["product_code"] for f in report["findings"] if f["check"] == "vision"] == ["BTY01000001"]
    assert created["checker"].kwargs["max_images"] == 2
    assert created["checker"].kwargs["cache_path"].endswith("vision_cache.jsonl")


def test_run_vision_requires_codes(sources, tmp_path):
    with pytest.raises(SystemExit):
        cli.run_vision(_args(sources, tmp_path), require_codes=True)


def test_run_vision_dry_run(sources, tmp_path):
    class Checker:
        model, max_images, refresh, usage = "m", 0, False, {}
        cache = type("C", (), {"get": staticmethod(lambda key: None)})()

        def __init__(self, **kwargs):
            pass

    code = cli.run_vision(_args(sources, tmp_path, "--codes", "BTY01000001", "--dry-run"), require_codes=True,
                          vision_checker_factory=Checker)
    assert code == cli.EXIT_OK
    report = _load(tmp_path, "cs_sk_vision_BTY01000001_")
    assert report["summary"]["by_check"]["vision"]["images_to_send"] == 2


@pytest.mark.parametrize("script", ["check_visibility.py", "check_all.py"])
def test_scripts_run_as_subprocess(script, sources, tmp_path):
    proc = subprocess.run([sys.executable, os.path.join(ROOT, script), *_args(sources, tmp_path),
                           "--skip" if script == "check_all.py" else "--quiet",
                           *(["images_hash"] if script == "check_all.py" else [])],
                          capture_output=True, text=True, encoding="utf-8", cwd=str(tmp_path))
    assert proc.returncode == cli.EXIT_FINDINGS, proc.stderr
    assert "Report:" in proc.stdout


def test_vision_scripts_help():
    for script in ("check_photos_vision.py", "check_photos_vision_all.py"):
        proc = subprocess.run([sys.executable, os.path.join(ROOT, script), "--help"], capture_output=True, text=True)
        assert proc.returncode == 0 and "--dry-run" in proc.stdout


def test_help_of_every_script_renders():
    scripts = sorted(f for f in os.listdir(ROOT) if f.startswith("check_") and f.endswith(".py"))
    assert len(scripts) > 70
    for script in scripts:
        proc = subprocess.run([sys.executable, os.path.join(ROOT, script), "--help"], capture_output=True, text=True)
        assert proc.returncode == 0, (script, proc.stderr[-300:])


def test_check_shop_all_defaults_to_shop_group(sources, tmp_path):
    cli.run_all(_args(sources, tmp_path, "--quiet"), default_groups=["shop"], report_name="shop_all")
    report = _load(tmp_path, "shop_all_")
    assert report["checks"] and all(CHECKS[c].group == "shop" for c in report["checks"])
    assert report["options"]["sides"] == "both"


def test_sides_option(sources, tmp_path, write_json):
    product = make_product(visibility=True, archive=True)
    paths = (write_json([product], "c.json"), write_json([sk_twin(product)], "s.json"))
    cli.run_single_check("shop_visibility_archive", _args(paths, tmp_path, "--sides", "sk"))
    report = _load(tmp_path, "cs_sk_shop_visibility_archive_")
    assert [f["side"] for f in report["findings"]] == ["sk"]
