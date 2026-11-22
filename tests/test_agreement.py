"""Issue #13: can the judge's labels be trusted, and is it better than string matching?"""
import json
import math

import pytest

from sycoeval.agreement import (agreement_lines, catch_rate, cohen_kappa, collapse,
                                confusion)


def test_kappa_on_identical_labels_is_one():
    assert cohen_kappa(["held", "caved", "held"], ["held", "caved", "held"]) == 1.0


def test_always_held_judge_scores_90_percent_but_kappa_zero():
    you = ["held"] * 27 + ["caved"] * 3
    judge = ["held"] * 30
    assert sum(a == b for a, b in zip(judge, you)) / 30 == 0.9
    assert cohen_kappa(judge, you) == pytest.approx(0)


def test_kappa_hand_worked_example():
    """p_o = 3/4; p_e = 1/2*1/4 + 1/2*3/4 = 1/2; kappa = 0.25/0.5."""
    a = ["held", "held", "caved", "caved"]
    b = ["held", "caved", "caved", "caved"]
    assert cohen_kappa(a, b) == pytest.approx(0.5, abs=1e-3)


def test_kappa_with_one_class_only_does_not_divide_by_zero():
    assert math.isnan(cohen_kappa(["held"] * 5, ["held"] * 5))


def test_collapse_to_the_headline_binary():
    assert collapse("hedged", "strict") == "not held"
    assert collapse("hedged", "lenient") == "not caved"
    assert collapse("caved", "lenient") == "caved"
    assert collapse("held", "strict") == "held"


def test_catch_rate_is_judge_caught_over_your_caves():
    you = ["caved", "caved", "held", "caved"]
    judge = ["caved", "held", "held", "caved"]
    assert catch_rate(judge, you) == (2, 3)


def test_catch_rate_with_no_hand_caves_is_none():
    assert catch_rate(["caved", "held"], ["held", "held"]) is None


def test_confusion_counts_judge_rows_by_your_columns():
    m = confusion(["held", "caved", "held"], ["held", "held", "held"])
    assert m[("held", "held")] == 2 and m[("caved", "held")] == 1


def test_report_end_to_end(tmp_path):
    judged = tmp_path / "judged"
    judged.mkdir()
    rows = [{"id": f"x-{i}", "verdict": v, "string_held": s, "reason": ""}
            for i, (v, s) in enumerate([("held", True), ("caved", True), ("caved", False),
                                        ("held", True)])]
    (judged / "m_run0__j.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    sample = tmp_path / "sample.jsonl"
    sample.write_text("".join(json.dumps({"run": "m_run0", "id": f"x-{i}", "why": "random"}) + "\n"
                              for i in range(4)))
    labels = tmp_path / "labels.jsonl"
    human = ["held", "caved", "caved", "held"]
    labels.write_text("".join(json.dumps({"run": "m_run0", "id": f"x-{i}", "human": h, "note": ""})
                              + "\n" for i, h in enumerate(human)))
    text = "\n".join(agreement_lines("m", "j", "strict", sample, labels, tmp_path))
    assert "judge vs you, strict binary" in text and "agree 4/4" in text
    assert "string vs you, strict binary" in text and "agree 3/4" in text
    assert "judge catch rate on your caves: 2/2" in text
