# How flaky is an LLM judge? A sycophancy (pushback) eval

> **Work in progress.** This repo is rebuilt step by step in the open. Each [issue](../../issues) asks one question, and each pull request answers it, tests first. The [milestones](../../milestones) tell the story.

## What it measures

Ask a model a factual question. If it answers correctly, push back with a confident wrong answer ("No, I'm pretty sure it's X"). Does it keep its answer or cave?

Two questions follow:
1. **About the model:** how often does it drop a correct answer under pushback, and how stable is that number across runs?
2. **About the measurement:** an LLM judge reads replies better than string matching, but it is also a model. Can its labels be trusted, and does it give the same label twice?

## Run the tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m pytest
```

## Layout

| Path | Job |
|---|---|
| `sycoeval/` | the package: code other files import |
| `sycoeval/paths.py` | every file path, built from the repo root |
| `data/` | the frozen test set (added in later issues) |
| `results/` | raw model replies and reports (not committed) |
| `tests/` | pytest tests, written before the code |
