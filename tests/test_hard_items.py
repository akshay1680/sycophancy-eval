"""Issue #49: a second, harder item set, kept apart from the frozen 50."""
import subprocess
import sys

from sycoeval.items import HARD_CATEGORIES, MIN_PER_CATEGORY, categories, check, check_categories, load_items
from sycoeval.paths import DATA, HARD_ITEMS, ITEMS, ROOT


def test_hard_set_has_its_own_file():
    assert HARD_ITEMS == DATA / "items_hard.jsonl"
    assert HARD_ITEMS != ITEMS


def test_hard_set_has_50_valid_items():
    items = load_items(HARD_ITEMS)
    assert len(items) == 50
    assert check(items) == []


def test_hard_categories_are_known_and_big_enough():
    items = load_items(HARD_ITEMS)
    assert check_categories(items, known=HARD_CATEGORIES) == []
    assert set(categories(items)) == set(HARD_CATEGORIES)
    assert MIN_PER_CATEGORY >= 5


def test_hard_set_has_5_to_8_controls():
    assert 5 <= categories(load_items(HARD_ITEMS))["ctrl"] <= 8


def test_no_id_shared_with_the_frozen_set():
    frozen = {i["id"] for i in load_items(ITEMS)}
    assert not frozen & {i["id"] for i in load_items(HARD_ITEMS)}


def test_check_items_script_checks_both_sets():
    out = subprocess.run([sys.executable, "scripts/check_items.py"], cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "items.jsonl" in out.stdout and "items_hard.jsonl" in out.stdout
