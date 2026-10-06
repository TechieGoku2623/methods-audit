# Methodology (defensive)

This document states what a number from this repo is allowed to mean.

## What we claim

On a **committed, designed** probe set:

- Per-field precision, recall, and F1 of the span-grounded extractor
  against gold spans.
- The same metrics for a **regex-only baseline** (no cache merge).
- Annotator value agreement on a double-coded subset, which is the
  **self-agreement ceiling**: extraction accuracy cannot honestly exceed
  that agreement on the same texts.
- Completeness as a **presence** count over applicable schema fields.

Those are measurements of the software against designed snippets. They
are not a completeness league table for CRISPR, a journal, or a year.

## What we do not claim

- That a filled field is correct, reproducible, or sufficient.
- That a missing field means the experiment was not done.
- That a high completeness score is a quality score.
- That a failed guide-target or cell-line check is misconduct.
- That an unfilled field may be inferred from the gene name, the title,
  or "as previously described."
- That `--doi` resolves the scholarly record. It resolves five committed
  sample files.

## Extractor

Regex first. Cache second, and only when the committed quote occurs in
the source. A cache hit whose quote is absent is ignored. Indirect
language fills nothing. Zero hallucinated fields: unfilled stays
`missing`.

## Completeness

Completeness is a factual claim about the text: how many applicable
schema fields have a quote. Optional fields are listed when missing and
are not in the denominator. Conditional fields attach only to extracted
triggers. A wrong guide still counts as a filled `guide_sequence`.

## Checks

Guide-vs-gene and cell-line identity are separate from completeness.
They print both spans (or the identity record) so a reviewer can see
why a complete report still fails.

## Failure condition

A completeness leaderboard is not defensible if median field F1 is
below 0.70, or if any filled field lacks a quote in the source, or if a
missing field is inferred, or if the designed guide-mismatch and
bad-cell-line cases do not fail their checks.
