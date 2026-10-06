"""Phase 0 audit path: extract, score, cross-check. No live LLM."""

from __future__ import annotations

from pathlib import Path

from methods_audit.cache import CacheStore, load_cache
from methods_audit.checks import load_gene_sequences, load_misidentified, run_checks
from methods_audit.config import get_settings
from methods_audit.extract import extract
from methods_audit.schemas import CompletenessScore, ConsistencyCheck, Extraction
from methods_audit.score import score_completeness


def audit_text(
    text: str,
    paper_id: str,
    *,
    cache: CacheStore | None = None,
    gene_sequences: dict[str, str] | None = None,
    misidentified: dict[str, dict[str, str]] | None = None,
) -> tuple[Extraction, CompletenessScore, list[ConsistencyCheck]]:
    extraction = extract(text, paper_id, cache=cache)
    score = score_completeness(extraction)
    genes = gene_sequences if gene_sequences is not None else {}
    mis = misidentified if misidentified is not None else {}
    checks = run_checks(extraction, genes, mis)
    return extraction, score, checks


def load_reference_tables(
    sample_dir: Path | None = None,
) -> tuple[CacheStore, dict[str, str], dict[str, dict[str, str]]]:
    root = sample_dir or get_settings().sample_dir
    cache = load_cache(root / "llm_cache.json")
    genes = load_gene_sequences(root / "gene_sequences.json")
    mis = load_misidentified(root / "cellosaurus_misidentified.json")
    return cache, genes, mis
