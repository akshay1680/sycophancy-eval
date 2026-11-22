"""A one-line progress indicator on stderr, so stdout stays clean for results.

    ollama_run0__ollama-qwen3-8b   12/47  geo-10  ~1m10s left
"""
import sys
import time


def fmt_eta(seconds):
    if seconds is None:
        return "?"
    seconds = int(round(seconds))
    return f"{seconds // 60}m{seconds % 60:02d}s" if seconds >= 60 else f"{seconds}s"


class Bar:
    """Call as bar(label, done, total, item_id). done=0 starts the clock for that label."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.start = None

    def __call__(self, label, done, total, item_id):
        now = self.clock()
        if done == 0 or self.start is None:
            self.start = now
        eta = (now - self.start) / done * (total - done) if done else None
        line = f"{label}  {done}/{total}  {item_id or ''}  ~{fmt_eta(eta)} left"
        end = "\n" if done == total else ""
        sys.stderr.write(f"\r{line:<70}{end}")
        sys.stderr.flush()
