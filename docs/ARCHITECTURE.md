# Architecture and data contracts

Phase 1 freeze of the schema, extractor, scorer, and checks the CLI uses.
Nothing here is a live PMC OA ingest or a live LLM call.

## Topology

```
PMC-OA-style XML
    │
    ├─► regex_extract → SpanValue per field (quote or missing)
    ├─► merge_cache    → fill only when the committed quote occurs in the text
    │         │
    │         └─► Extraction
    │                ├─► score_completeness → CompletenessScore
    │                └─► run_checks → guide_targets_gene, cell_line_identity
    └─► doi_map.json (five samples only)
```

A field is `filled` only when `quote` occurs in the source. Completeness is
filled applicable fields over applicable fields. Optional fields are not
in the denominator. Quality is not scored.

## Contracts

| Object | Module | Role |
| --- | --- | --- |
| `FieldSpec` | `fields.py` | 32-field schema: required / conditional / optional, cited. |
| `SpanValue` | `schemas.py` | Value + offsets + quote + source. Unfilled stays `missing`. |
| `Extraction` | `schemas.py` | All 32 fields, never a subset that hides empties. |
| `CompletenessScore` | `schemas.py` | Presence counts plus missing lists by need. |
| `ConsistencyCheck` | `schemas.py` | `pass` / `fail` / `skipped` with spans and alignment when present. |
| `CacheEntry` | `schemas.py` | Committed cache row. Quote must occur in the XML or it is ignored. |
| `doi_map.json` | `data/sample/` | Five designed DOIs → filenames. Unknown DOI fails closed. |

## CLI surface (Phase 2)

| Command | Contract |
| --- | --- |
| `methods-audit extract --paper` | Print every field: value, source, span. Missing is printed as missing. |
| `methods-audit score --paper` | Completeness plus missing lists by required / conditional / optional. |
| `methods-audit score --doi` | Same, after resolving the committed five-sample DOI map. |
| `methods-audit check --paper` | Guide-vs-gene (both spans + alignment) and Cellosaurus identity. |
| `methods-audit demo` | Full walkthrough of the designed paths. |

## What is not in this slice

Live PMC ingest, a live model on cache miss, genome-wide off-target search,
and a hosted API. The extractor and checks already exist; this slice
exposes them and measures regex vs gold with an agreement ceiling.
