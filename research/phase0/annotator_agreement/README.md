# annotator_agreement

## What is measured

Value agreement and span IoU between two committed gold passes on 15 designed papers. Agreement is the honest upper bound on extraction accuracy.

## Why it decides something

A model cannot be more accurate than the annotators on the same texts. Phase 3 claims above this number are not allowed.

## How to run

```bash
uv run python research/phase0/annotator_agreement/run.py
```

## Gold-label source

`probe_set/pass_a.json` and `pass_b.json`. Pass B disagrees on purpose on three papers' optional fields (antibody RRID, karyotype, culture conditions) and is otherwise value-aligned. Not two live annotators of PMC OA.
