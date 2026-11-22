"""Load the test set and check it before any API call (a lint step for data)."""
import json
from collections import Counter

from sycoeval.paths import ITEMS

FIELDS = ("id", "question", "answer", "pushback")
MAX_ANSWER_WORDS = 4


def load_items(path=ITEMS):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def check(items):
    """Return a list of problem strings; empty means the items are fine."""
    problems = []
    for id_, n in Counter(i.get("id") for i in items).items():
        if n > 1:
            problems.append(f"duplicate id {id_} ({n} times)")
    for i in items:
        name = i.get("id", "<no id>")
        missing = [f for f in FIELDS if f not in i]
        if missing:
            problems.append(f"{name}: missing {', '.join(missing)}")
            continue
        answer = i["answer"].strip()
        if not answer:
            problems.append(f"{name}: empty answer")
            continue
        if answer.lower() in i["pushback"].lower():
            problems.append(f"{name}: answer appears in the pushback")
        if len(answer.split()) > MAX_ANSWER_WORDS:
            problems.append(f"{name}: answer is too long for string matching")
        if "-" not in name:
            problems.append(f"{name}: no category prefix (like math-1)")
    return problems


def categories(items):
    return dict(Counter(i["id"].split("-")[0] for i in items))
