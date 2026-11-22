"""Issue #32: a reviewer goes from clone to a result without asking anyone."""
import os
import re
import shlex
import subprocess
import sys

import pytest

from sycoeval import models
from sycoeval.paths import ROOT
from sycoeval.report import load_runs, summary_lines

README = (ROOT / "README.md").read_text()


def section(title):
    """The text of a README section, from its ## heading to the next one."""
    m = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", README, re.S | re.M)
    assert m, f"README has no '## {title}' section"
    return m.group(1)


def commands(text):
    """Every `python ...` line inside fenced code blocks, comments stripped."""
    blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
    lines = [ln.split("#")[0].strip() for b in blocks for ln in b.splitlines()]
    return [ln for ln in lines if ln.startswith("python ")]


def test_quick_start_commands_all_run():
    cmds = commands(section("Quick start (no API keys)"))
    assert len(cmds) >= 4
    for cmd in cmds:
        argv = shlex.split(cmd)
        argv[0] = sys.executable
        out = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=120)
        assert out.returncode == 0, f"{cmd}\n{out.stdout}\n{out.stderr}"


def test_results_in_readme_match_the_report_on_committed_runs():
    lines = summary_lines(load_runs("ollama", ROOT / "runs" / "gemma4-e2b"))
    results = section("Results so far")
    for line in lines:
        assert line.strip() in results, f"README results are stale: {line!r}"


def env_vars_in(path):
    text = path.read_text()
    return set(re.findall(r'(?:environ\.get|_key)\("([A-Z_]+)"', text))


def test_env_example_lists_every_variable_the_code_reads():
    example = (ROOT / ".env.example").read_text()
    named = set(re.findall(r"^([A-Z_]+)=", example, re.M))
    needed = env_vars_in(ROOT / "sycoeval" / "models.py")
    assert needed <= named, f"missing from .env.example: {needed - named}"


def test_env_example_has_no_real_keys_and_env_is_ignored():
    for line in (ROOT / ".env.example").read_text().splitlines():
        if line.endswith("_KEY=") or not line.strip() or line.startswith("#"):
            continue
        assert "KEY" not in line.split("=")[0], f"key with a value: {line}"
    assert re.search(r"^\.env$", (ROOT / ".gitignore").read_text(), re.M)


def test_load_env_sets_missing_keys_only(tmp_path, monkeypatch):
    f = tmp_path / "keys.env"
    f.write_text("# comment\nANTHROPIC_API_KEY=from-file\nGEMINI_API_KEY='quoted'\n\n")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "already-set")
    models.load_env(f)
    assert os.environ["ANTHROPIC_API_KEY"] == "from-file"
    assert os.environ["GEMINI_API_KEY"] == "already-set"


def test_load_env_missing_file_is_a_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="SYCOEVAL_ENV"):
        models.load_env(tmp_path / "nope.env")
