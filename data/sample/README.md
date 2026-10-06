# Sample methods sections

These five records are designed, not sampled. Each one exists to exercise a
path the walkthrough names. XML is PMC-OA-shaped and short. `make demo` and
`make test` run with no network.

This directory contains no patient-identifiable data and no copyrighted
PMC full texts. Filenames are the teaching cases.

| File | Why it is here |
| --- | --- |
| `complete.xml` | Thoroughly reported. Most required fields present. Cross-checks pass. |
| `no-guide.xml` | Missing guide sequence — the most common omission. Do not invent one. |
| `guide-mismatch.xml` | Stated guide does not target stated gene. Completeness still counts the field; the complementarity check fails. |
| `bad-cell-line.xml` | INT-407 is on the committed Cellosaurus-style misidentification list. |
| `indirect.xml` | "As previously described." Extraction fails. Fields stay missing. |

`gene_sequences.json` holds short designed windows for the complementarity
check. `cellosaurus_misidentified.json` is a committed ICLAC-style list, not
a live Cellosaurus dump. `llm_cache.json` is a committed response cache for
these five papers; Phase 0 never calls a model.

S5 is the failing case the walkthrough is built around. A demo that only
shows `complete.xml` teaches nothing about when to trust the extractor.

Cross-checks, not filled-field counts, are the real findings on S3 and S4.
