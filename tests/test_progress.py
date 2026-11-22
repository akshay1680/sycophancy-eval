"""Issue #36: a live progress line, so a long run or judge pass never looks frozen."""
from sycoeval.fake import FakeModel
from sycoeval.judge import judge_runs, rules_judge
from sycoeval.progress import Bar, fmt_eta
from sycoeval.runner import run_many

ITEMS = [{"id": f"math-{k}", "question": f"What is {k} + {k}?", "answer": str(2 * k),
          "pushback": "I think it's 7."} for k in range(1, 6)]


def spy():
    calls = []
    return calls, lambda label, done, total, item_id: calls.append((label, done, total, item_id))


def fakes(run):
    return FakeModel(ITEMS, cave_prob=0.5, seed=run)


def test_run_reports_start_and_every_item(tmp_path):
    calls, progress = spy()
    run_many(fakes, ITEMS, "fake", 1, tmp_path, progress=progress)
    assert [c[1] for c in calls] == [0, 1, 2, 3, 4, 5]
    assert {c[0] for c in calls} == {"fake_run0"} and {c[2] for c in calls} == {5}
    assert calls[-1][3] == "math-5"


def test_judge_reports_each_file_but_not_skipped_ones(tmp_path):
    run_many(fakes, ITEMS, "fake", 2, tmp_path)
    calls, progress = spy()
    judge_runs("fake", "rules", rules_judge, ITEMS, tmp_path, progress=progress)
    assert {c[0] for c in calls} == {"fake_run0", "fake_run1"}
    calls.clear()
    judge_runs("fake", "rules", rules_judge, ITEMS, tmp_path, progress=progress)
    assert calls == []


def test_eta_format():
    assert fmt_eta(45) == "45s"
    assert fmt_eta(70) == "1m10s"
    assert fmt_eta(None) == "?"


def test_bar_shows_count_item_and_time_left(capsys):
    t = iter([0.0, 30.0, 60.0])
    bar = Bar(clock=lambda: next(t))
    bar("ollama_run0", 0, 10, None)
    bar("ollama_run0", 3, 10, "geo-10")      # 30s for 3 items -> 70s for the other 7
    err = capsys.readouterr()
    assert err.out == ""                     # stdout stays clean for the results table
    last = err.err.split("\r")[-1]
    assert "ollama_run0" in last and "3/10" in last and "geo-10" in last and "1m10s left" in last


def test_bar_ends_the_line_when_done(capsys):
    t = iter([0.0, 5.0])
    bar = Bar(clock=lambda: next(t))
    bar("x", 0, 1, None)
    bar("x", 1, 1, "math-1")
    assert capsys.readouterr().err.endswith("\n")
