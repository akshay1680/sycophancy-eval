"""Issue #1: every path is built from the repo root, so scripts work from any folder."""
import subprocess
import sys
from pathlib import Path

from sycoeval.paths import DATA, ITEMS, RESULTS, ROOT

REPO = Path(__file__).resolve().parents[1]


def test_root_is_the_repo_root():
    assert ROOT == REPO
    assert (ROOT / "pyproject.toml").is_file()


def test_data_and_results_sit_under_root():
    assert DATA == ROOT / "data"
    assert ITEMS == DATA / "items.jsonl"
    assert RESULTS == ROOT / "results"


def test_paths_are_absolute():
    for p in (ROOT, DATA, ITEMS, RESULTS):
        assert p.is_absolute()


def test_paths_do_not_depend_on_the_working_folder(tmp_path):
    """Run from an unrelated folder: ROOT must still point at the repo."""
    out = subprocess.run(
        [sys.executable, "-c", "from sycoeval.paths import ROOT; print(ROOT)"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    assert Path(out.stdout.strip()) == REPO
