"""Real model adapters. Every one is ask(messages) -> str, like the fake model.

API keys come from environment variables (load them from an env file kept
outside the repo). Errors and refusals come back as marked strings, so one
bad call never crashes a 300-call run.
"""
import json
import os
import urllib.error
import urllib.request

from sycoeval.usage import log_usage

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e2b")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
MAX_TOKENS = 512
TIMEOUT = 120

REFUSED = "[REFUSED]"


class MissingKey(RuntimeError):
    pass


def post_json(url, payload, headers):
    """The one place that talks HTTP. Tests replace it."""
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"content-type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read())


def _key(var):
    value = os.environ.get(var)
    if not value:
        raise MissingKey(f"set {var} in your env file (kept outside the repo)")
    return value


def _safe(call):
    """Run one API call; turn network or format errors into a marked string."""
    try:
        return call()
    except MissingKey:
        raise
    except (urllib.error.URLError, OSError, KeyError, IndexError, ValueError) as e:
        return f"[ERROR] {type(e).__name__}: {e}"


def ollama_ask(messages, model=None):
    def call():
        out = post_json(f"{OLLAMA_URL}/api/chat",
                        {"model": model or OLLAMA_MODEL, "messages": messages, "stream": False}, {})
        log_usage("ollama", model or OLLAMA_MODEL, out.get("prompt_eval_count"), out.get("eval_count"))
        return out["message"]["content"]
    return _safe(call)


def claude_ask(messages, model=None):
    key = _key("ANTHROPIC_API_KEY")

    def call():
        out = post_json("https://api.anthropic.com/v1/messages",
                        {"model": model or CLAUDE_MODEL, "max_tokens": MAX_TOKENS, "messages": messages},
                        {"x-api-key": key, "anthropic-version": "2023-06-01"})
        u = out.get("usage", {})
        log_usage("claude", model or CLAUDE_MODEL, u.get("input_tokens"), u.get("output_tokens"))
        if out.get("stop_reason") == "refusal":
            return REFUSED
        return "".join(b["text"] for b in out["content"] if b.get("type") == "text")
    return _safe(call)


def gemini_ask(messages, model=None):
    key = _key("GEMINI_API_KEY")
    contents = [{"role": "model" if m["role"] == "assistant" else "user",
                 "parts": [{"text": m["content"]}]} for m in messages]

    def call():
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model or GEMINI_MODEL}:generateContent")
        out = post_json(url, {"contents": contents}, {"x-goog-api-key": key})
        u = out.get("usageMetadata", {})
        log_usage("gemini", model or GEMINI_MODEL, u.get("promptTokenCount"), u.get("candidatesTokenCount"))
        if out.get("promptFeedback", {}).get("blockReason") or not out.get("candidates"):
            return REFUSED
        return "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"])
    return _safe(call)
