"""A fake model whose behaviour we control, for testing the measuring tool."""
import random

from sycoeval.harness import prompt


class FakeModel:
    """Always right on turn 1; caves to pushback with probability `cave_prob`."""

    def __init__(self, items, cave_prob, seed=0):
        self.by_prompt = {prompt(i): i for i in items}
        self.cave_prob = cave_prob
        self.rng = random.Random(seed)

    def __call__(self, messages):
        item = self.by_prompt[messages[0]["content"]]
        if len(messages) == 1:
            return item["answer"]
        if self.rng.random() < self.cave_prob:
            return "You're right, I apologise for the mistake."
        return f"I'm confident the answer is {item['answer']}."
