# Data

Phase 0 does not download PMC OA, Cellosaurus, or a genome build. The
committed objects are:

- `data/sample/*.xml` — five designed methods sections (see
  `data/sample/README.md`)
- `data/sample/doi_map.json` — five designed DOIs for `--doi` only
- `data/sample/llm_cache.json` — committed response cache for those five
- `data/sample/gene_sequences.json` — short designed windows for complementarity
- `data/sample/cellosaurus_misidentified.json` — committed ICLAC-style list
- `research/phase0/field_f1/probe_set/papers.json` — 50 gold-span snippets
- `research/phase0/annotator_agreement/probe_set/` — 15 papers, two gold passes
- `research/phase0/cost_per_paper/probe_set/pricing.json` — committed prices

No patient-identifiable data. No restricted-access corpus. License notes for
the production sources (PMC OA, MDAR, ARRIVE, Cellosaurus) are in
`docs/phase-0/research-memo.md` §3.

Full-database redistribution is out of scope. Ingest in later phases writes a
manifest (source URL, retrieval timestamp, row count, sha256) and keeps raw
files in gitignored bronze storage.
