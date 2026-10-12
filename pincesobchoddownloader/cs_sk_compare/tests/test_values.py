from cssklib.values import (
    deep_diff, fold_text, get_name, get_root_categories, get_translation, image_path, is_active,
    normalize_value, short, strip_shop_domain,
)
from conftest import make_product


def test_normalize_value_empty_and_numbers():
    assert normalize_value("") is None
    assert normalize_value([]) is None
    assert normalize_value({"a": None, "b": ""}) is None
    assert normalize_value(320.0) == 320
    assert normalize_value(6.34) == 6.34
    assert normalize_value(True) is True
    assert normalize_value("  a   b ") == "a b"


def test_normalize_value_strips_domain_and_sorts_lists():
    assert normalize_value("https://www.pincesobchod.sk/x/1.jpg") == "/x/1.jpg"
    assert normalize_value([{"id": 2}, {"id": 1}]) == [{"id": 1}, {"id": 2}]


def test_deep_diff_dict_paths():
    diffs = deep_diff({"a": {"b": 1, "c": 2}}, {"a": {"b": 1, "c": 3}})
    assert diffs == [{"path": "a.c", "cs": 2, "sk": 3}]
    assert deep_diff(1, 1) == []
    assert deep_diff(1, 2) == [{"path": "", "cs": 1, "sk": 2}]


def test_deep_diff_lists():
    diffs = deep_diff([{"id": 1}, {"id": 2}], [{"id": 1}, {"id": 3}])
    assert diffs == [{"path": "[]", "cs": [{"id": 2}], "sk": [{"id": 3}]}]
    diffs = deep_diff([1, 1], [1])
    assert diffs == [{"path": "", "cs": [1, 1], "sk": [1]}]
    assert deep_diff({"t": [1]}, {"t": [2]})[0]["path"] == "t[]"


def test_translation_fallbacks():
    product = {"translations": {"cs": {"name": "CZ"}, "sk": {"name": "SK"}}}
    assert get_translation(product, "name", "sk") == "SK"
    assert get_translation(product, "name", "cs") == "CZ"
    assert get_translation({"translations": {"de": {"name": "DE"}}}, "name", "sk") == "DE"
    assert get_translation({}, "name", "cs") is None
    assert get_name({"translations": {"cs": {"name": " a  b "}}}) == "a b"


def test_root_categories_main_first_and_fallback():
    product = make_product(categories=[
        {"id": 53, "main": False, "path": {"53": "Textil"}},
        {"id": 36, "main": True, "path": {"36": "Dřeva", "54": "Dřeva OFF"}},
    ])
    assert get_root_categories(product) == ["dreva"]
    product["categories"][1]["main"] = False
    assert get_root_categories(product) == ["textil", "dreva"]


def test_misc_helpers():
    assert fold_text("Dřeva ") == "dreva"
    assert image_path("https://www.pincesobchod.cz/files/a.jpg") == "/files/a.jpg"
    assert image_path("https://cdn.example.com/files/a.jpg?x=1") == "/files/a.jpg"
    assert image_path(None) is None
    assert strip_shop_domain(5) == 5
    assert is_active({"visibility": True, "archive": False})
    assert not is_active({"visibility": True, "archive": True})
    assert short(None) == "∅"
    assert short("x" * 200, 10).endswith("…")
    assert short({"a": 1}) == '{"a": 1}'
