# Phase 0 harnesses

`make research` runs these in order:

1. `data/sample/build_cache.py` — rebuild the committed five-paper LLM cache
2. `field_f1/probe_set/build.py` — rebuild the 50 gold-span snippets
3. `annotator_agreement/probe_set/build.py` — rebuild the 15-paper double gold
4. `field_f1/run.py` — per-field precision / recall / F1
5. `annotator_agreement/run.py` — agreement ceiling
6. `cost_per_paper/run.py` — token cost by model tier
7. `render_docs.py` — write `docs/phase-0/research-memo.md`, `docs/EVALUATION.md`, and the measured tables in `README.md`

No number in the memo is typed by hand. If a quantity cannot be produced here, the memo says **unmeasured** and names the measurement that would settle it.
