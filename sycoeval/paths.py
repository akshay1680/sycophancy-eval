"""Every file path in one place, built from the repo root.

Paths are worked out from this file's location, not from the folder a
command is run in, so scripts and tests work from anywhere.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # sycoeval/ sits one level below the root
DATA = ROOT / "data"
ITEMS = DATA / "items.jsonl"
RESULTS = ROOT / "results"
