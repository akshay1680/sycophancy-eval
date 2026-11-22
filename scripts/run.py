"""Run one model over all items, n times (default 3), saving raw replies.

Complete runs are skipped, so re-running after a crash resumes.

    python scripts/run.py fake        # no API calls
    python scripts/run.py ollama 3    # or claude / gemini
"""
import sys

from sycoeval.harness import flip_rate, wilson
from sycoeval.items import load_items
from sycoeval.paths import RESULTS
from sycoeval.progress import Bar
from sycoeval.runner import get_ask, run_many

which = sys.argv[1] if len(sys.argv) > 1 else "fake"
n_runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
items = load_items()
pause = get_ask(which, items)[1]
runs = run_many(lambda run: get_ask(which, items, seed=run)[0], items, which, n_runs, RESULTS, pause,
                progress=Bar())
for run, results in enumerate(runs):
    k, n = flip_rate(results)
    lo, hi = wilson(k, n)
    print(f"run {run}: correct first {n}/{len(items)}, flipped {k}/{n}, 95% CI {lo:.2f}-{hi:.2f}")
