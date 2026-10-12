import os

import pytest

from cssklib import loader
from cssklib.pairing import format_variant_key, pair_products, pair_variants, variant_key
from conftest import make_product, make_variant


def _make_full(base, folder, lang, products, write_json):
    path = os.path.join(base, folder)
    os.makedirs(path, exist_ok=True)
    target = os.path.join(path, f"Pincesobchod_{lang}.json")
    os.replace(write_json(products, f"{folder}_{lang}.json"), target)
    return target


def test_find_latest_json_by_folder_date(tmp_path, write_json):
    base = str(tmp_path / "Pincesobchod_CS")
    _make_full(base, "Full_31.12.2025", "CS", [], write_json)
    newest = _make_full(base, "Full_02.01.2026", "CS", [make_product()], write_json)
    os.makedirs(os.path.join(base, "Full_05.01.2026"))  # folder without JSON is ignored
    os.makedirs(os.path.join(base, "Other"))
    assert loader.find_latest_json(base, "CS") == newest
    path, products = loader.resolve_source("cs", base)
    assert path == newest and len(products) == 1


def test_find_latest_json_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        loader.find_latest_json(str(tmp_path / "missing"), "CS")
    with pytest.raises(FileNotFoundError):
        loader.find_latest_json(str(tmp_path), "CS")


def test_pull_newest_uses_downloader_mechanism(tmp_path, write_json):
    calls = []
    source = write_json([make_product()], "remote.json")

    def fake_download(url, path, lang, overwrite=False):
        calls.append((url, path, lang, overwrite))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(source, encoding="utf-8") as src, open(path, "w", encoding="utf-8") as dst:
            dst.write(src.read())

    fake = ("https://www.pincesobchod.{COUNTRY_CODE}/api/v1/products?page=1", fake_download,
            lambda root: f"{root}/Full_01.01.2026")
    path, products = loader.resolve_source("sk", str(tmp_path / "SK"), pull_newest=True, downloader=fake)
    assert calls == [("https://www.pincesobchod.sk/api/v1/products?page=1", path, "SK", True)]
    assert path.endswith("Full_01.01.2026/Pincesobchod_SK.json")
    assert len(products) == 1


def test_real_downloader_modules_are_importable():
    pattern, download, day_folder = loader._import_downloader()
    assert "{COUNTRY_CODE}" in pattern and callable(download)
    assert day_folder("X").startswith("X/Full_")


def test_load_products_formats(tmp_path):
    (tmp_path / "list.json").write_text("[{\"catalogNumber\": \"A\"}]", encoding="utf-8")
    assert loader.load_products(str(tmp_path / "list.json")) == [{"catalogNumber": "A"}]
    (tmp_path / "bad.json").write_text("{\"data\": 5}", encoding="utf-8")
    with pytest.raises(ValueError):
        loader.load_products(str(tmp_path / "bad.json"))


def test_explicit_json_has_priority(write_json):
    path = write_json([make_product()], "x.json")
    assert loader.resolve_source("cs", "/nonexistent", explicit_json=path)[0] == path


def test_pair_products_identity_is_code_plus_name():
    cs = [make_product("A", "Name A"), make_product("B", "Name B"), make_product("C", "Only CZ"),
          make_product("D", "Dup"), make_product("D", "Dup")]
    sk = [make_product("A", "Name  A ", side="sk"), make_product("B", "Name b", side="sk"),
          make_product("E", "Only SK", side="sk"), make_product("D", "Dup", side="sk")]
    pairing = pair_products(cs, sk)
    assert [c["catalogNumber"] for c, _ in pairing.matched] == ["A", "D"]
    assert [(c["catalogNumber"], s["catalogNumber"]) for c, s in pairing.name_conflicts] == [("B", "B")]
    assert [p["catalogNumber"] for p in pairing.cs_only] == ["C", "D"]
    assert [p["catalogNumber"] for p in pairing.sk_only] == ["E"]
    assert pairing.duplicates == {"cs": ["D"], "sk": []}
    assert pairing.summary()["name_conflicts"] == 1


def test_pair_variants_all_cases():
    cs = make_product(variants=[
        make_variant("P-01", [("Barva", "černá"), ("Velikost", "XL")]),
        make_variant("P-02", [("Barva", "černá"), ("Velikost", "L")]),
        make_variant("P-03", [("Barva", "modrá")]),
        make_variant("P-04", [("Barva", "zelená")]),
        make_variant("P-05", [("Barva", "bílá")]),
    ])
    sk = make_product(side="sk", variants=[
        make_variant("P-01", [("Velikost", "XL"), ("Barva", "černá")]),   # same identity, other order
        make_variant("P-09", [("Barva", "černá"), ("Velikost", "L")]),   # same options, other code
        make_variant("P-03", [("Barva", "Modrá")]),                       # same code, other options
        make_variant("P-07", [("Barva", "žlutá")]),                       # only SK
    ])
    vp = pair_variants(cs, sk)
    assert [c["catalogNumber"] for _, c, _ in vp.matched] == ["P-01"]
    assert [(c["catalogNumber"], s["catalogNumber"]) for _, c, s in vp.code_mismatch] == [("P-02", "P-09")]
    assert [(c["catalogNumber"], s["catalogNumber"]) for c, s in vp.option_mismatch] == [("P-03", "P-03")]
    assert sorted(v["catalogNumber"] for _, v in vp.cs_only) == ["P-04", "P-05"]
    assert [v["catalogNumber"] for _, v in vp.sk_only] == ["P-07"]


def test_pair_variants_duplicate_option_sets():
    cs = make_product(variants=[make_variant("P-01", [("Barva", "černá")]), make_variant("P-02", [("Barva", "černá")])])
    sk = make_product(side="sk", variants=[make_variant("P-02", [("Barva", "černá")])])
    vp = pair_variants(cs, sk)
    assert vp.duplicate_keys["cs"] == [(("Barva", "černá"),)]
    assert [c["catalogNumber"] for _, c, _ in vp.matched] == ["P-02"]
    assert [v["catalogNumber"] for _, v in vp.cs_only] == ["P-01"]


def test_variant_key_format():
    variant = make_variant("X", [("Velikost", " XL "), ("Barva", "černá")])
    assert variant_key(variant) == (("Barva", "černá"), ("Velikost", "XL"))
    assert format_variant_key(variant_key(variant)) == "Barva=černá, Velikost=XL"
    assert format_variant_key(()) == "(bez parametrů)"


def test_unparsable_full_folder_is_oldest(tmp_path, write_json):
    base = str(tmp_path / "SK")
    _make_full(base, "Full_backup", "SK", [], write_json)
    dated = _make_full(base, "Full_01.01.2020", "SK", [], write_json)
    assert loader.find_latest_json(base, "SK") == dated


def test_default_fetch_uses_downloader_http(monkeypatch):
    from types import SimpleNamespace
    from cssklib import images
    loader._import_downloader()
    import shared.http_downloader as http
    monkeypatch.setattr(http, "download_with_retry", lambda url: SimpleNamespace(content=b"ok") if "a" in url else None)
    assert images.default_fetch("https://x/a.jpg") == b"ok"
    assert images.default_fetch("https://x/b.jpg") is None
