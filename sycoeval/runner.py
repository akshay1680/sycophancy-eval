"""Run a model over the items and save every raw reply, so grading never re-calls it."""
import json
import time
from pathlib import Path

from sycoeval.harness import run_item


def run_and_save(ask, items, out_path, pause=0.0):
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with out.open("w") as f:
        for item in items:
            r = run_item(ask, item)
            f.write(json.dumps(r) + "\n")
            f.flush()
            results.append(r)
            time.sleep(pause)
    return results


def get_ask(which, items, seed=0):
    """'fake' or a model adapter name: ollama, claude, gemini. Returns (ask, pause)."""
    if which == "fake":
        from sycoeval.fake import FakeModel
        return FakeModel(items, cave_prob=0.3, seed=seed), 0.0
    from sycoeval import models
    return getattr(models, f"{which}_ask"), 1.0


def load_run(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def run_many(ask_for_run, items, which, n_runs, results_dir, pause=0.0, log=print):
    """Do n_runs runs, skipping any run whose file is already complete.

    ask_for_run(run) returns the ask function for that run (so a fake model
    can take seed=run). A crash in run 2 never costs runs 0 and 1.
    """
    runs = []
    for run in range(n_runs):
        out = Path(results_dir) / f"{which}_run{run}.jsonl"
        if out.exists() and len(load_run(out)) == len(items):
            log(f"run {run}: already complete, skipping")
            runs.append(load_run(out))
            continue
        runs.append(run_and_save(ask_for_run(run), items, out, pause))
    return runs
