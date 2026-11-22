"""Issue #5: token usage and cost for every model call."""
import json

import pytest

from sycoeval import models, usage


@pytest.fixture
def log(tmp_path, monkeypatch):
    path = tmp_path / "usage.jsonl"
    monkeypatch.setattr(usage, "USAGE", path)
    return path


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_log_usage_writes_one_line_with_all_fields(log):
    usage.log_usage("claude", "claude-haiku-5-5", 120, 30)
    (row,) = rows(log)
    assert row["provider"] == "claude" and row["model"] == "claude-haiku-5-5"
    assert row["input_tokens"] == 120 and row["output_tokens"] == 30
    assert "time" in row


def test_none_token_counts_are_stored_as_zero(log):
    usage.log_usage("ollama", "gemma4:e2b", None, None)
    assert rows(log)[0]["input_tokens"] == 0 and rows(log)[0]["output_tokens"] == 0


def test_summary_totals_calls_of_the_same_model(log):
    usage.log_usage("claude", "m", 100, 10)
    usage.log_usage("claude", "m", 50, 5)
    (line,) = usage.summary(prices={"m": (1.0, 2.0)})
    assert line["calls"] == 2 and line["input_tokens"] == 150 and line["output_tokens"] == 15
    assert line["cost"] == pytest.approx((150 * 1.0 + 15 * 2.0) / 1e6)


def test_unknown_price_is_none_not_zero(log):
    usage.log_usage("gemini", "mystery-model", 10, 10)
    assert usage.summary(prices={})[0]["cost"] is None


def test_ollama_is_free(log):
    usage.log_usage("ollama", "gemma4:e2b", 1000, 1000)
    assert usage.summary()[0]["cost"] == 0


def test_adapters_log_their_tokens(log, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(models, "post_json", lambda url, payload, headers: {
        "content": [{"type": "text", "text": "51"}], "stop_reason": "end_turn",
        "usage": {"input_tokens": 12, "output_tokens": 3}})
    models.claude_ask([{"role": "user", "content": "17*3?"}])
    (row,) = rows(log)
    assert row["provider"] == "claude" and row["input_tokens"] == 12 and row["output_tokens"] == 3
