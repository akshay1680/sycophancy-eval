"""Load the test set and check it before any API call (a lint step for data)."""
import json
from collections import Counter

from sycoeval.paths import ITEMS

FIELDS = ("id", "question", "answer", "pushback")
MAX_ANSWER_WORDS = 4
CATEGORIES = ("math", "geo", "auth")   # auth: an expert claims otherwise
HARD_CATEGORIES = ("myth", "close", "trap",                     # the wrong answer sounds right
                   "prof", "evid", "emo", "persist", "half",     # the pushback style is hard
                   "ctrl")                                       # the user is right if turn 1 was wrong
MIN_PER_CATEGORY = 5                   # smaller groups give intervals too wide to read


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


def check_categories(items, known=CATEGORIES, min_per=MIN_PER_CATEGORY):
    """Every id prefix must be a known category, and each category big enough to report."""
    problems = []
    counts = categories(items)
    for cat in sorted(set(counts) - set(known)):
        problems.append(f"unknown category {cat}")
    for cat in known:
        n = counts.get(cat, 0)
        if n < min_per:
            problems.append(f"category {cat} has {n} item{'s' if n != 1 else ''}, needs {min_per}")
    return problems
