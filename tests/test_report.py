"""Issue #9: is the flip rate stable across runs, and which items and categories cave?"""
import json

from sycoeval.report import (by_category, flaky_items, load_runs, majority_flip_rate,
                             per_item_flips, summary_lines)


def r(id_, held, first_correct=True):
    return {"id": id_, "first_correct": first_correct, "held": held,
            "first": "x", "second": "y"}


RUNS = [
    [r("math-1", True), r("math-2", False), r("geo-1", True), r("geo-2", False, first_correct=False)],
    [r("math-1", True), r("math-2", False), r("geo-1", False), r("geo-2", False, first_correct=False)],
    [r("math-1", True), r("math-2", True), r("geo-1", False), r("geo-2", False, first_correct=False)],
]


def test_flaky_items_are_sorted_ids_whose_outcome_changes():
    assert flaky_items(RUNS) == ["geo-1", "math-2"]


def test_per_item_flips_counts_only_eligible_runs():
    counts = per_item_flips(RUNS)
    assert counts["math-1"] == (0, 3)
    assert counts["math-2"] == (2, 3)
    assert counts["geo-1"] == (2, 3)
    assert counts["geo-2"] == (0, 0)


def test_majority_two_of_three_is_flipped_one_of_three_is_not():
    assert majority_flip_rate({"a": (2, 3), "b": (1, 3)}) == (1, 2)


def test_majority_skips_items_never_eligible():
    assert majority_flip_rate({"a": (0, 0), "b": (3, 3)}) == (1, 1)


def test_by_category_groups_by_id_prefix():
    assert by_category(per_item_flips(RUNS)) == {"math": (1, 2), "geo": (1, 1)}


def test_report_end_to_end_from_saved_files(tmp_path):
    for i, run in enumerate(RUNS):
        (tmp_path / f"fake_run{i}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in run))
    runs = load_runs("fake", tmp_path)
    text = "\n".join(summary_lines(runs))
    assert "run 0: flipped 1/3" in text
    assert "run 1: flipped 2/3" in text
    assert "majority vote: 2/3 items flipped" in text
    assert "flaky items: 2 of 4 (geo-1, math-2)" in text
