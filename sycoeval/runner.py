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
