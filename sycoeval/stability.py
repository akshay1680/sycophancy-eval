"""Judge the frozen sample k times and see whether the label moves.

    python -m sycoeval.stability ollama qwen3:8b 5     # reads results/, writes results/stability/

If the judge changes its mind on the same reply, part of the run-to-run noise
in a judged flip rate belongs to the grader, not the model.
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

from sycoeval.judge import judge_one
from sycoeval.labels import LABELS, SAMPLE, read_jsonl
from sycoeval.paths import RESULTS


def changed(labels):
    return len(set(labels)) > 1


def repeat_judge(judge_ask, items, sample, results_dir, out_dir, k=5, pause=0.0, progress=None):
    """Judge every sample row k times; rep r goes to out_dir/rep{r}.jsonl.
    A complete rep with no errors is skipped, so a crash resumes. Returns k lists of rows."""
    by_id = {i["id"]: i for i in items}
    replies = {}
    for run in {s["run"] for s in sample}:
        for r in read_jsonl(Path(results_dir) / f"{run}.jsonl"):
            replies[(run, r["id"])] = r
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    reps = []
    for rep in range(k):
        out = out_dir / f"rep{rep}.jsonl"
        done = read_jsonl(out)
        if len(done) == len(sample) and not any(d["verdict"] == "error" for d in done):
            reps.append(done)
            continue
        rows = []
        if progress:
            progress(out.stem, 0, len(sample), None)
        with out.open("w") as f:
            for n, s in enumerate(sample, 1):
                row = {"run": s["run"], **judge_one(judge_ask, by_id[s["id"]], replies[(s["run"], s["id"])])}
                f.write(json.dumps(row) + "\n")
                f.flush()
                rows.append(row)
                if progress:
                    progress(out.stem, n, len(sample), s["id"])
                time.sleep(pause)
        reps.append(rows)
    return reps


def load_reps(out_dir):
    """Saved repeats, rep0 first, read without calling any judge."""
    paths = sorted(Path(out_dir).glob("rep*.jsonl"), key=lambda p: int(p.stem[3:]))
    return [read_jsonl(p) for p in paths]


def stability_rows(reps, labels):
    """One row per sample reply: its k verdicts, the hand label, and whether it changed."""
    human = {(l["run"], l["id"]): l["human"] for l in labels}
    verdicts = {}
    for rows in reps:
        for r in rows:
            verdicts.setdefault((r["run"], r["id"]), []).append(r["verdict"])
    return [{"run": run, "id": id_, "verdicts": v, "human": human.get((run, id_)),
             "changed": changed(v)} for (run, id_), v in verdicts.items()]


def by_hand_label(rows):
    """{hand label: (rows that changed, rows)}."""
    out = {}
    for r in rows:
        c, n = out.get(r["human"], (0, 0))
        out[r["human"]] = (c + r["changed"], n + 1)
    return out


def plot_svg(breakdown, path):
    """One horizontal bar per hand label: share of replies whose judge label changed."""
    order = [l for l in ("held", "caved", "hedged", "other") if l in breakdown]
    order += sorted(set(breakdown) - set(order), key=str)
    w, bar, top = 520, 26, 40
    h = top + len(order) * (bar + 12) + 30
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
             f'font-family="sans-serif" font-size="13">',
             f'<rect width="{w}" height="{h}" fill="white"/>',
             '<text x="10" y="22" font-weight="bold">Judge label changed across repeats, '
             'by hand label</text>']
    for i, label in enumerate(order):
        c, n = breakdown[label]
        y = top + i * (bar + 12)
        width = 300 * c / n if n else 0
        parts += [f'<text x="10" y="{y + 18}">{label}</text>',
                  f'<rect x="90" y="{y}" width="300" height="{bar}" fill="#eee"/>',
                  f'<rect x="90" y="{y}" width="{width:.1f}" height="{bar}" fill="#3b6ea5"/>',
                  f'<text x="400" y="{y + 18}">{c}/{n}</text>']
    parts.append("</svg>")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts) + "\n")
    return path


def summary_lines(rows):
    n = len(rows)
    lines = [f"{sum(r['changed'] for r in rows)}/{n} replies got more than one label "
             f"over {len(rows[0]['verdicts']) if rows else 0} repeats"]
    for label, (c, m) in sorted(by_hand_label(rows).items(), key=lambda kv: str(kv[0])):
        lines.append(f"  hand label {label!s:7} {c}/{m} changed")
    for r in rows:
        if r["changed"]:
            lines.append(f"  {r['run']} {r['id']} (you: {r['human']}): "
                         + ", ".join(f"{v} x{c}" for v, c in Counter(r["verdicts"]).most_common()))
    return lines


if __name__ == "__main__":
    from functools import partial

    from sycoeval import models
    from sycoeval.items import load_items
    from sycoeval.progress import Bar
    if len(sys.argv) not in (3, 4, 5):
        sys.exit("usage: python -m sycoeval.stability <adapter> <model> [k=5] [results folder]")
    adapter, model_id = sys.argv[1], sys.argv[2]
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    results_dir = Path(sys.argv[4]) if len(sys.argv) > 4 else RESULTS
    name = f"{adapter}-{model_id.replace(':', '-').replace('/', '-')}"
    out_dir = results_dir / "stability" / name
    ask = partial(getattr(models, f"{adapter}_ask"), model=model_id)
    reps = repeat_judge(ask, load_items(), read_jsonl(SAMPLE), results_dir, out_dir, k,
                        pause=1.0, progress=Bar())
    rows = stability_rows(reps, read_jsonl(LABELS))
    print("\n".join(summary_lines(rows)))
    print("plot:", plot_svg(by_hand_label(rows), out_dir / "stability.svg"))
