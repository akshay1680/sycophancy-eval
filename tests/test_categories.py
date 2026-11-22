"""Issue #7: does the result hold beyond a handful of easy questions? Check the categories."""
from sycoeval.items import CATEGORIES, MIN_PER_CATEGORY, check_categories, load_items
from sycoeval.paths import ITEMS


def items(*ids):
    return [{"id": i} for i in ids]


def test_balanced_set_passes():
    ids = [f"{c}-{n}" for c in ("math", "geo") for n in range(1, 6)]
    assert check_categories(items(*ids), known=("math", "geo"), min_per=5) == []


def test_unknown_category_is_caught():
    problems = check_categories(items("math-1", "chem-1"), known=("math",), min_per=1)
    assert any("unknown category chem" in p for p in problems)


def test_small_category_is_caught():
    problems = check_categories(items("math-1", "math-2", "geo-1"), known=("math", "geo"), min_per=2)
    assert any("geo" in p and "1 item" in p for p in problems)


def test_committed_set_has_50_items_in_known_categories():
    all_items = load_items(ITEMS)
    assert len(all_items) == 50
    assert check_categories(all_items) == []
    assert MIN_PER_CATEGORY >= 5 and set(CATEGORIES) == {"math", "geo", "auth"}
