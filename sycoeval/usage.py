"""Token usage and cost for every model call, whatever the provider.

Adapters in models.py call log_usage(...) after each request.
`python -m sycoeval.usage` prints calls, tokens and cost per provider and model.
"""
import json
import time
from collections import defaultdict

from sycoeval.paths import USAGE

# USD per 1 million tokens: (input, output), keyed by model or provider.
# Fill in from each provider's pricing page. Missing means cost unknown, shown as "?".
PRICES = {
    "ollama": (0.0, 0.0),   # local models are free
}


def log_usage(provider, model, input_tokens, output_tokens):
    """Append one call's token counts to the usage log."""
    USAGE.parent.mkdir(parents=True, exist_ok=True)
    row = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "provider": provider, "model": model,
           "input_tokens": int(input_tokens or 0), "output_tokens": int(output_tokens or 0)}
    with USAGE.open("a") as f:
        f.write(json.dumps(row) + "\n")


def summary(prices=PRICES):
    """One dict per (provider, model): calls, tokens, and cost in USD (None if unknown)."""
    totals = defaultdict(lambda: [0, 0, 0])
    if USAGE.exists():
        for line in USAGE.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                t = totals[(r["provider"], r["model"])]
                t[0] += 1
                t[1] += r["input_tokens"]
                t[2] += r["output_tokens"]
    out = []
    for (provider, model), (calls, tin, tout) in sorted(totals.items()):
        price = prices.get(model) or prices.get(provider)
        cost = None if price is None else (tin * price[0] + tout * price[1]) / 1e6
        out.append({"provider": provider, "model": model, "calls": calls,
                    "input_tokens": tin, "output_tokens": tout, "cost": cost})
    return out


if __name__ == "__main__":
    for s in summary():
        cost = "?" if s["cost"] is None else f"${s['cost']:.4f}"
        print(f"{s['provider']:8} {s['model']:28} calls {s['calls']:5}  "
              f"in {s['input_tokens']:8}  out {s['output_tokens']:7}  cost {cost}")
