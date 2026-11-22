"""Hand labels: the ground truth the judge is checked against.

Two steps, kept apart on purpose:
1. `python -m sycoeval.labels sample <results name> <judge name>` draws a frozen
   sample and writes labels/sample.jsonl. Commit it before labelling: that's the
   freeze point.
2. `python -m sycoeval.labels label` shows each reply WITHOUT the judge's or
   string matching's label, and saves your label at once (Ctrl-C any time).
"""
import json
import random
import sys
from collections import Counter
from pathlib import Path

from sycoeval.paths import RESULTS, ROOT

SAMPLE = ROOT / "labels" / "sample.jsonl"
LABELS = ROOT / "labels" / "labels.jsonl"
KEYS = {"h": "held", "c": "caved", "e": "hedged", "o": "other"}


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def judged_rows(which, judge_name, results_dir=RESULTS):
    """Every judged row for one judge, tagged with its run (e.g. "ollama_run0")."""
    rows = []
    for p in sorted(Path(results_dir, "judged").glob(f"{which}_run*__{judge_name}.jsonl")):
        run = p.stem.split("__")[0]
        rows += [{**r, "run": run} for r in read_jsonl(p)]
    return rows


def is_hard(r):
    """Worth a human look: the graders disagree, or the judge didn't commit."""
    return ((r["verdict"] == "held") != r["string_held"]
            or r["verdict"] in ("hedged", "other", "parse_error"))


def draw_sample(rows, n_random=20, n_hard=10, seed=6):
    """Random rows first (the honest estimate), then hard rows from the rest (error analysis).
    Returns [{"run", "id", "why"}], shuffled, with no verdicts in it."""
    rng = random.Random(seed)
    random_rows = rng.sample(rows, min(n_random, len(rows)))
    taken = {(r["run"], r["id"]) for r in random_rows}
    hard_pool = [r for r in rows if (r["run"], r["id"]) not in taken and is_hard(r)]
    hard_rows = rng.sample(hard_pool, min(n_hard, len(hard_pool)))
    picks = ([{"run": r["run"], "id": r["id"], "why": "random"} for r in random_rows]
             + [{"run": r["run"], "id": r["id"], "why": "hard"} for r in hard_rows])
    rng.shuffle(picks)
    return picks


def label_loop(items, sample_path=SAMPLE, labels_path=LABELS, results_dir=RESULTS,
               ask=input, show=print):
    by_id = {i["id"]: i for i in items}
    sample = read_jsonl(sample_path)
    replies = {}
    for run in {s["run"] for s in sample}:
        for r in read_jsonl(Path(results_dir) / f"{run}.jsonl"):
            replies[(run, r["id"])] = r
    done = {(r["run"], r["id"]) for r in read_jsonl(labels_path)}
    todo = [s for s in sample if (s["run"], s["id"]) not in done]
    show(f"{len(done)} labelled, {len(todo)} to go. Ctrl-C any time; every label is saved.")
    Path(labels_path).parent.mkdir(parents=True, exist_ok=True)
    with open(labels_path, "a") as f:
        for k, s in enumerate(todo, 1):
            item, row = by_id[s["id"]], replies[(s["run"], s["id"])]
            show(f"\n--- {k}/{len(todo)} ---")
            show(f"Question: {item['question']}")
            show(f"Correct answer: {item['answer']}")
            show(f"Pushback: {item['pushback']}")
            show(f"Reply:\n{row['second']}\n")
            key = ""
            while key not in KEYS:
                key = ask("[h]eld  [c]aved  h[e]dged  [o]ther > ").strip().lower()
            note = ask("note (Enter to skip) > ").strip()
            f.write(json.dumps({"run": s["run"], "id": s["id"], "human": KEYS[key], "note": note}) + "\n")
            f.flush()


if __name__ == "__main__":
    from sycoeval.items import load_items
    if sys.argv[1:2] == ["sample"] and len(sys.argv) == 4:
        if SAMPLE.exists():
            sys.exit(f"{SAMPLE} already exists: the sample is frozen.")
        SAMPLE.parent.mkdir(exist_ok=True)
        picks = draw_sample(judged_rows(sys.argv[2], sys.argv[3]))
        SAMPLE.write_text("".join(json.dumps(p) + "\n" for p in picks))
        print(f"wrote {len(picks)} picks to {SAMPLE}: {dict(Counter(p['why'] for p in picks))}")
        print("Commit it now, and don't open it until you've finished labelling.")
    elif sys.argv[1:] == ["label"]:
        label_loop(load_items())
    else:
        sys.exit("usage: python -m sycoeval.labels sample <results name> <judge name>\n"
                 "       python -m sycoeval.labels label\n"
                 "e.g.   python -m sycoeval.labels sample ollama ollama-qwen3-8b")
