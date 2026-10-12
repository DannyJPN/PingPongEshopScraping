import csv
import json
import os
from types import SimpleNamespace

import pytest

from cssklib.images import ImageStore, sorted_images
from cssklib.report import CSV_COLUMNS, CheckResult, Finding, build_report, render_text, write_report
from cssklib.vision import (
    VisionCache, VisionChecker, build_user_content, create_openai_client, default_model, parse_response,
)
from conftest import make_product


def _report():
    results = [
        CheckResult("visibility", "Vlastnost produktu 'visibility'", [
            Finding("visibility", "visibility", "Hodnota se v CZ a SK liší", "A", "Produkt A", cs_value=True,
                    sk_value=False),
            Finding("visibility", "visibility", "x", "B", "Produkt B", severity="warning", side="sk",
                    variant_code="B-01", variant_options="Barva=černá", expected=1, details={"k": 1}),
        ], {"checked": 2}),
        CheckResult("ean", "Vlastnost produktu 'ean'", [], {"checked": 2}),
    ]
    return build_report(results, {"cs": {"path": "cs.json", "products": 2}, "sk": {"path": "sk.json", "products": 2}},
                        {"matched": 2, "cs_only": 0, "sk_only": 0, "name_conflicts": 0})


def test_build_report_structure():
    report = _report()
    assert report["schema"] == "pincesobchod-cs-sk-report/1"
    assert report["checks"] == ["visibility", "ean"]
    assert report["summary"]["total_findings"] == 2
    assert report["summary"]["by_severity"] == {"error": 1, "warning": 1}
    assert report["summary"]["by_check"]["ean"] == {"title": "Vlastnost produktu 'ean'", "findings": 0, "checked": 2}
    assert "details" not in report["findings"][0] and report["findings"][1]["details"] == {"k": 1}


def test_render_text():
    text = render_text(_report())
    assert "SOUHRN" in text and "visibility — Vlastnost produktu 'visibility'  (2 nálezů)" in text
    assert "[WARNING] B / varianta B-01 (Barva=černá) [SK]" in text
    assert "očekáváno: 1" in text and "CZ: true" in text
    assert "… a dalších 1" in render_text(_report(), max_items=1)
    report = _report()
    report["findings"][1]["variant_options"] = ""
    assert "/ varianta B-01 [SK]" in render_text(report)
    summary = render_text(_report(), summary_only=True)
    assert "SOUHRN" in summary and "[ERROR]" not in summary


def test_write_report_files(tmp_path):
    paths, text = write_report(_report(), str(tmp_path / "out"), "cs_sk_test", timestamp="T")
    assert paths["json"].endswith("cs_sk_test_T.json")
    with open(paths["json"], encoding="utf-8") as handle:
        assert json.load(handle)["summary"]["total_findings"] == 2
    with open(paths["csv"], encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))
    assert rows[0] == CSV_COLUMNS and len(rows) == 3 and rows[1][9] == "False"
    with open(paths["txt"], encoding="utf-8") as handle:
        assert handle.read() == text


def test_image_store_caches_downloads(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        return b"data"

    store = ImageStore(str(tmp_path), fetch=fetch, workers=3)
    url = "https://www.pincesobchod.cz/files/1.jpg"
    first = store.get_hash(url)
    assert store.get_hash(url) == first and calls == [url]
    assert os.path.isfile(store.cache_path(url)) and store.cache_path(url).endswith(".jpg")
    assert ImageStore(str(tmp_path), fetch=fetch).get_bytes(url) == b"data" and calls == [url]
    assert store.cache_path("https://x/noext").endswith(".img")
    assert store.hash_many([url, None, url]) == {url: first}


def test_image_store_failures(tmp_path):
    def boom(url):
        raise OSError("network")
    assert ImageStore(str(tmp_path), fetch=boom).get_hash("https://x/a.jpg") is None
    assert ImageStore(str(tmp_path), fetch=lambda u: None).get_bytes("https://x/b.jpg") is None


def test_sorted_images():
    product = {"images": [{"id": 2, "position": 2}, {"id": 1, "position": 1}]}
    assert [i["id"] for i in sorted_images(product)] == [1, 2]
    assert sorted_images({"images": None}) == []


def test_parse_response():
    verdicts = parse_response('{"images": [{"index": 1, "verdict": "PRODUCT", "reason": "ok"},'
                              '{"index": 2, "verdict": "weird"}, {"index": 9, "verdict": "product"},'
                              '{"index": "x"}]}', 3)
    assert verdicts[1] == ("product", "ok")
    assert verdicts[2][0] == "unclear"
    assert verdicts[3][0] == "unclear"
    assert parse_response('text {"images": [{"index": 1, "verdict": "related"}]} end', 1)[1][0] == "related"
    assert parse_response("garbage", 1)[1][0] == "unclear"
    assert parse_response("[]", 1)[1][0] == "unclear"


class FakeClient:
    def __init__(self, answer):
        self.answer = answer
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.answer))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=10))


def test_vision_checker_uses_cache(tmp_path):
    answer = json.dumps({"images": [{"index": 1, "verdict": "product", "reason": "a"},
                                    {"index": 2, "verdict": "unrelated", "reason": "b"}]})
    client = FakeClient(answer)
    cache = str(tmp_path / "cache.jsonl")
    checker = VisionChecker(model="m", client=client, cache_path=cache)
    product = make_product()
    results = checker.check_product(product)
    assert [r["verdict"] for r in results] == ["product", "unrelated"]
    request = client.requests[0]
    assert request["model"] == "m" and request["response_format"] == {"type": "json_object"}
    content = request["messages"][1]["content"]
    assert content[1] == {"type": "image_url", "image_url": {"url": product["images"][0]["url"], "detail": "low"}}
    assert "Potah BUTTERFLY Tenergy 05" in content[0]["text"] and "BTY01000001" in content[0]["text"]
    assert checker.usage["prompt_tokens"] == 100

    again = VisionChecker(model="m", client=FakeClient("{}"), cache_path=cache)
    assert [r["cached"] for r in again.check_product(product)] == [True, True]
    assert again.usage["requests"] == 0
    refreshed = VisionChecker(model="m", client=FakeClient(answer), cache_path=cache, refresh=True, max_images=1)
    assert len(refreshed.check_product(product)) == 1 and refreshed.usage["requests"] == 1


def test_vision_checker_embeds_images(tmp_path):
    store = ImageStore(str(tmp_path), fetch=lambda url: b"img" if url.endswith("1.jpg") else None)
    client = FakeClient('{"images": []}')
    checker = VisionChecker(model="m", client=client, embed_images=True, image_store=store, detail="high")
    checker.check_product(make_product())
    images = [c["image_url"]["url"] for c in client.requests[0]["messages"][1]["content"][1:]]
    assert images[0] == "data:image/jpeg;base64,aW1n"
    assert images[1].startswith("https://")  # download failed -> URL fallback


def test_build_user_content_categories():
    product = make_product(manufacturer=None, categories=[{"path": {"53": "Textil", "85": "Polokošile"}}])
    text = build_user_content(product, "cs", [1], [], "low")[0]["text"]
    assert "Textil > Polokošile" in text and "Brand: -" in text


def test_vision_cache_roundtrip(tmp_path):
    path = str(tmp_path / "sub" / "c.jsonl")
    cache = VisionCache(path)
    key = VisionCache.key("m", "A", "n", "u")
    cache.put({"key": key, "verdict": "product"})
    assert VisionCache(path).get(key)["verdict"] == "product"
    assert VisionCache(None).get(key) is None


def test_default_model_and_client(monkeypatch):
    monkeypatch.delenv("PINCESOBCHOD_VISION_MODEL", raising=False)
    assert default_model() == "gpt-4o"
    monkeypatch.setenv("PINCESOBCHOD_VISION_MODEL", "gpt-x")
    assert default_model() == "gpt-x"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_openai_client()
    with pytest.raises(RuntimeError):
        VisionChecker().client
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    pytest.importorskip("openai")
    assert create_openai_client() is not None
