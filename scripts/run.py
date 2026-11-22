"""Run one model over all items once and save raw replies.

    python scripts/run.py fake        # no API calls
    python scripts/run.py ollama      # or claude / gemini
"""
import sys

from sycoeval.harness import flip_rate, wilson
from sycoeval.items import load_items
from sycoeval.paths import RESULTS
from sycoeval.runner import get_ask, run_and_save

which = sys.argv[1] if len(sys.argv) > 1 else "fake"
items = load_items()
ask, pause = get_ask(which, items)
results = run_and_save(ask, items, RESULTS / f"{which}_run0.jsonl", pause)
k, n = flip_rate(results)
lo, hi = wilson(k, n)
print(f"{which}: correct first {n}/{len(items)}, flipped {k}/{n}, 95% CI {lo:.2f}-{hi:.2f}")
