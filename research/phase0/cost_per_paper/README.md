# cost_per_paper

## What is measured

Input tokens (tiktoken cl100k_base) and USD per paper across committed model list prices. Local render+tokenize latency. API RTT is unmeasured.

## Why it decides something

The default extraction tier is the cheapest row that can later be escalated when a cache miss fails span validation. No live API.

## How to run

```bash
uv run python research/phase0/cost_per_paper/run.py
```

Uses the same 50 papers as `field_f1`.
