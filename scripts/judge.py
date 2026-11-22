"""Re-grade saved runs with an LLM judge, then compare it with string matching.

    python scripts/judge.py fake rules              # rules judge: must agree on every row
    python scripts/judge.py ollama ollama qwen3:8b  # a judge from a different model family
"""
import sys
from functools import partial

from sycoeval.harness import wilson
from sycoeval.items import load_items
from sycoeval.judge import judge_runs, judge_summary, rules_judge
from sycoeval.paths import RESULTS
from sycoeval.progress import Bar

if len(sys.argv) < 3:
    sys.exit(__doc__)
which, adapter = sys.argv[1], sys.argv[2]
if adapter == "rules":
    judge_ask, judge_name, pause = rules_judge, "rules", 0.0
else:
    from sycoeval import models
    model_id = sys.argv[3]
    judge_ask = partial(getattr(models, f"{adapter}_ask"), model=model_id)
    judge_name = f"{adapter}-{model_id.replace(':', '-').replace('/', '-')}"
    pause = 1.0

print("run | string flipped | judge caved (lenient) | caved+hedged (strict) | agree | parse_error | error")
for path in judge_runs(which, judge_name, judge_ask, load_items(), RESULTS, pause,
                        progress=Bar()):
    s = judge_summary(path)
    n = s["n"]
    lo, hi = wilson(s["lenient"], n)
    slo, shi = wilson(s["strict"], n)
    print(f"{path.stem} | {s['string_flipped']}/{n} | {s['lenient']}/{n} ({lo:.2f}-{hi:.2f}) | "
          f"{s['strict']}/{n} ({slo:.2f}-{shi:.2f}) | {s['agree']}/{n} | {s['parse_error']} | {s['error']}")
    if s["disagreements"]:
        print("   disagreements:", ", ".join(s["disagreements"]))
