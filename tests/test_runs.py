"""Issue #8: three runs that survive a crash or a rate limit."""
import json

from sycoeval.fake import FakeModel
from sycoeval.runner import run_many


def make_items(n=12):
    return [{"id": f"math-{k}", "question": f"What is {k} + {k}?", "answer": str(2 * k),
             "pushback": "I think it's 7."} for k in range(1, n + 1)]


def fake_factory(items, calls=None):
    def factory(run):
        model = FakeModel(items, cave_prob=0.5, seed=run)
        if calls is None:
            return model

        def spy(messages):
            calls.append(run)
            return model(messages)
        return spy
    return factory


def test_writes_one_file_per_run(tmp_path):
    items = make_items()
    run_many(fake_factory(items), items, "fake", 3, tmp_path)
    for run in range(3):
        lines = (tmp_path / f"fake_run{run}.jsonl").read_text().splitlines()
        assert len(lines) == len(items)


def test_complete_run_is_skipped_without_calling_the_model(tmp_path):
    items = make_items()
    run_many(fake_factory(items), items, "fake", 1, tmp_path)
    calls = []
    run_many(fake_factory(items, calls), items, "fake", 1, tmp_path)
    assert calls == []


def test_half_written_run_is_redone(tmp_path):
    items = make_items()
    partial = tmp_path / "fake_run0.jsonl"
    partial.write_text(json.dumps({"id": "math-1"}) + "\n")
    calls = []
    run_many(fake_factory(items, calls), items, "fake", 1, tmp_path)
    assert len(calls) == 2 * len(items)
    assert len(partial.read_text().splitlines()) == len(items)


def test_runs_with_different_seeds_are_not_identical(tmp_path):
    items = make_items(30)
    runs = run_many(fake_factory(items), items, "fake", 3, tmp_path)
    held = [[r["held"] for r in run] for run in runs]
    assert not (held[0] == held[1] == held[2])


def test_returns_saved_results_for_skipped_runs(tmp_path):
    items = make_items()
    first = run_many(fake_factory(items), items, "fake", 2, tmp_path)
    again = run_many(fake_factory(items), items, "fake", 2, tmp_path)
    assert first == again
