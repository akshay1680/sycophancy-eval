# Lab notebook

Settings, decisions, item fixes and observations, newest last.

## Test set
- `data/items.jsonl` is the frozen 50-item set from the original build (math 16, geo 17, auth 17), copied byte for byte. Rule: after run 0, fixes only for objectively broken items, each logged here.
- The original 20-item pilot set was grown in place to 50, so it can't be recovered as a separate file. This rebuild commits the frozen 50 in #6.

## Pilot (original build, 20 items, 1 run)
- Model `gemma4:e2b` via Ollama, default sampling.
- 19/20 correct on turn 1, 0/19 flipped, Wilson 95% CI 0.00 to 0.17.
