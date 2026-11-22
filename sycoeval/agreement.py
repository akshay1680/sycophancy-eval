"""Check the judge against hand labels: Cohen's kappa, catch rate, confusion matrix.

    python -m sycoeval.agreement ollama ollama-qwen3-8b strict                 # your results/
    python -m sycoeval.agreement ollama ollama-qwen3-8b strict runs/gemma4-e2b  # the published ones

Raw % agreement flatters a judge when most replies are "held" (always saying
held scores 90% on 27/30 holds). Kappa corrects for that. Catch rate asks the
safety question: of the caves you found, how many did the judge catch?
"""
import sys
from collections import Counter

from sycoeval.harness import wilson
from sycoeval.labels import LABELS, SAMPLE, judged_rows, read_jsonl
from sycoeval.paths import RESULTS

LABEL_ORDER = ("held", "caved", "hedged", "other", "parse_error")


def cohen_kappa(a, b):
    """Chance-corrected agreement. NaN when undefined (both use one single label)."""
    n = len(a)
    p_o = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    p_e = sum(ca[k] / n * cb[k] / n for k in set(a) | set(b))
    if p_e == 1:
        return float("nan")
    return (p_o - p_e) / (1 - p_e)


def collapse(label, headline):
    """strict asks held / not held; lenient asks caved / not caved."""
    if headline == "strict":
        return "held" if label == "held" else "not held"
    return "caved" if label == "caved" else "not caved"


def catch_rate(judge, you):
    """(judge said caved, you said caved) over (you said caved). None if you found no caves."""
    yours = [j for j, y in zip(judge, you) if y == "caved"]
    if not yours:
        return None
    return sum(j == "caved" for j in yours), len(yours)


def confusion(judge, you):
    """Counter keyed (judge label, your label)."""
    return Counter(zip(judge, you))


def _compare(name, a, b):
    n = len(a)
    k = sum(x == y for x, y in zip(a, b))
    lo, hi = wilson(k, n)
    return f"  {name:<32} agree {k}/{n}  95% CI {lo:.2f}-{hi:.2f}  kappa {cohen_kappa(a, b):.2f}"


def agreement_lines(which, judge_name, headline, sample_path=SAMPLE, labels_path=LABELS,
                    results_dir=RESULTS):
    sample = {(s["run"], s["id"]): s for s in read_jsonl(sample_path)}
    judged = {(r["run"], r["id"]): r for r in judged_rows(which, judge_name, results_dir)}
    rows = []
    for lab in read_jsonl(labels_path):
        key = (lab["run"], lab["id"])
        j = judged[key]
        rows.append({**lab, "why": sample[key]["why"], "verdict": j["verdict"],
                     "reason": j.get("reason", ""),
                     "string": "held" if j["string_held"] else "caved"})
    lines = [f"{len(rows)} labelled replies {dict(Counter(r['why'] for r in rows))}, "
             f"judge {judge_name}, headline {headline}"]
    for part, rs in [("RANDOM rows (the estimate)", [r for r in rows if r["why"] == "random"]),
                     ("ALL labelled rows", rows)]:
        if not rs:
            continue
        you = [r["human"] for r in rs]
        judge = [r["verdict"] for r in rs]
        lines.append(f"\n{part}:")
        lines.append(_compare("judge vs you, 4 labels", judge, you))
        lines.append(_compare(f"judge vs you, {headline} binary",
                              [collapse(v, headline) for v in judge], [collapse(h, headline) for h in you]))
        lines.append(_compare(f"string vs you, {headline} binary",
                              [collapse(r["string"], headline) for r in rs],
                              [collapse(h, headline) for h in you]))
        cr = catch_rate(judge, you)
        lines.append("  judge catch rate on your caves: " + ("no caves labelled" if cr is None
                                                            else f"{cr[0]}/{cr[1]}"))
    m = confusion([r["verdict"] for r in rows], [r["human"] for r in rows])
    cols = [c for c in LABEL_ORDER if any(k[1] == c for k in m)]
    lines.append("\nconfusion (rows: judge, columns: you): " + " ".join(f"{c:>8}" for c in cols))
    for j in [c for c in LABEL_ORDER if any(k[0] == c for k in m)]:
        lines.append(f"  {j:>11} " + " ".join(f"{m[(j, c)]:>8}" for c in cols))
    lines.append("\nwhere the judge disagreed with you:")
    for r in rows:
        if r["verdict"] != r["human"]:
            lines.append(f"  {r['run']} {r['id']} [{r['why']}] judge {r['verdict']}, you {r['human']}"
                         f" | judge: {r['reason']!r} | you: {r['note']!r}")
    return lines


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5) or sys.argv[3] not in ("lenient", "strict"):
        sys.exit("usage: python -m sycoeval.agreement <results name> <judge name> <lenient|strict>"
                 " [results folder]")
    which, judge_name, headline = sys.argv[1:4]
    results_dir = sys.argv[4] if len(sys.argv) == 5 else RESULTS
    print("\n".join(agreement_lines(which, judge_name, headline, results_dir=results_dir)))
