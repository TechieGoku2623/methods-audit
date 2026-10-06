# field_f1

## What is measured

Per-field precision, recall, and F1 of the Phase 0 regex+cache extractor against 50 committed methods snippets with gold spans.

## Why it decides something

If median field F1 is below 0.70, a completeness leaderboard built on this extractor is not defensible. The gate is written before the run.

## How to run

```bash
uv run python research/phase0/field_f1/run.py
```

## Gold-label source

Gold spans are committed with the designed XML in `probe_set/papers.json`. This is not a live PMC OA annotation set. Replacing the 50 with hand-annotated OA methods sections is the measurement that would retire that limitation.
