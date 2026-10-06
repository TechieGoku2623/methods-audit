from __future__ import annotations

from methods_audit.cache import CacheStore, load_cache
from methods_audit.checks import min_mismatch, reverse_complement
from methods_audit.config import get_settings
from methods_audit.extract import extract, extract_many, regex_extract
from methods_audit.pipeline import audit_text, load_reference_tables
from methods_audit.schemas import CacheEntry, SpanValue
from methods_audit.score import score_completeness


def _read(name: str) -> str:
    return (get_settings().sample_dir / name).read_text(encoding="utf-8")


def test_complete_fills_required_and_passes_checks() -> None:
    cache, genes, mis = load_reference_tables()
    text = _read("complete.xml")
    extraction, score, checks = audit_text(
        text, "complete", cache=cache, gene_sequences=genes, misidentified=mis
    )
    assert extraction.fields["target_gene"].value == "TP53"
    assert extraction.fields["guide_sequence"].value == "GGCGCCATCTACAAGCAGTC"
    assert extraction.fields["guide_sequence"].quote in text
    assert score.completeness >= 0.8
    by_name = {c.name: c for c in checks}
    assert by_name["guide_targets_gene"].status == "pass"
    assert by_name["cell_line_identity"].status == "pass"


def test_no_guide_stays_missing() -> None:
    text = _read("no-guide.xml")
    extraction = regex_extract(text, "no-guide")
    assert extraction.fields["guide_sequence"].status == "missing"
    assert extraction.fields["target_gene"].value == "EGFR"
    score = score_completeness(extraction)
    assert "guide_sequence" in score.missing_fields


def test_guide_mismatch_is_complete_and_fails_check() -> None:
    cache, genes, mis = load_reference_tables()
    text = _read("guide-mismatch.xml")
    extraction, score, checks = audit_text(
        text, "guide-mismatch", cache=cache, gene_sequences=genes, misidentified=mis
    )
    assert extraction.fields["guide_sequence"].value == "AATTCCCGTCGCTATCAAGG"
    assert extraction.fields["target_gene"].value == "TP53"
    assert score.completeness > 0.5
    by_name = {c.name: c for c in checks}
    assert by_name["guide_targets_gene"].status == "fail"


def test_bad_cell_line_fails_identity() -> None:
    cache, genes, mis = load_reference_tables()
    text = _read("bad-cell-line.xml")
    extraction, _score, checks = audit_text(
        text, "bad-cell-line", cache=cache, gene_sequences=genes, misidentified=mis
    )
    assert extraction.fields["cell_line_or_organism"].value == "INT-407"
    by_name = {c.name: c for c in checks}
    assert by_name["cell_line_identity"].status == "fail"


def test_indirect_does_not_hallucinate() -> None:
    cache, genes, mis = load_reference_tables()
    text = _read("indirect.xml")
    extraction, score, checks = audit_text(
        text, "indirect", cache=cache, gene_sequences=genes, misidentified=mis
    )
    filled = [name for name, item in extraction.fields.items() if item.filled()]
    assert filled == []
    assert score.completeness == 0.0
    by_name = {c.name: c for c in checks}
    assert by_name["guide_targets_gene"].status == "skipped"
    assert by_name["cell_line_identity"].status == "skipped"


def test_cache_ignored_when_quote_absent() -> None:
    text = _read("indirect.xml")
    fake = CacheStore(
        {
            "indirect": CacheEntry(
                paper_id="indirect",
                fields={
                    "target_gene": SpanValue(
                        field="target_gene",
                        status="filled",
                        value="TP53",
                        quote="TP53",
                        start=0,
                        end=4,
                        source="cache",
                    )
                },
            )
        }
    )
    extraction = extract(text, "indirect", cache=fake)
    assert extraction.fields["target_gene"].status == "missing"


def test_cache_fills_when_quote_present() -> None:
    text = _read("complete.xml")
    empty = regex_extract("no methods here", "complete")
    cache = load_cache(get_settings().sample_dir / "llm_cache.json")
    # cache merge only fills missing fields whose quote occurs
    from methods_audit.extract import merge_cache

    merged = merge_cache(empty, cache, text)
    assert merged.fields["target_gene"].filled()
    assert merged.fields["target_gene"].source == "cache"


def test_extract_many_and_unknown_gene_skip() -> None:
    rows = extract_many([("a", "We targeted the ZZ9 locus in human using Cas9.")])
    assert rows[0].fields["target_gene"].value == "ZZ9"
    _cache, genes, mis = load_reference_tables()
    _, _, checks = audit_text(
        "We targeted the ZZ9 locus. The guide RNA sequence was ACGTACGTACGTACGTACG.",
        "zz9",
        gene_sequences=genes,
        misidentified=mis,
    )
    assert any(c.status == "skipped" for c in checks)


def test_reverse_complement_and_mismatch() -> None:
    assert reverse_complement("ACGT") == "ACGT"
    assert min_mismatch("AAAA", "TTTT") == 0
    assert min_mismatch("ACGTACGTACGTACGTACG", "TTTT") is None


def test_in_vivo_conditionals() -> None:
    text = (
        "We targeted the TP53 locus in mouse (GRCm39) using Cas9. "
        "The guide RNA sequence was GGCGCCATCTACAAGCAGTC. The PAM motif was NGG. "
        "Electroporation delivered RNP into C57BL/6J mice. "
        "12 animals, male and female. A non-targeting sgRNA was included. "
        "Editing was measured by T7E1 (n = 3). Off-target analysis used CRISPOR."
    )
    extraction = regex_extract(text, "mouse")
    score = score_completeness(extraction)
    assert "animal_strain" in score.applicable_fields
    assert extraction.fields["animal_strain"].value == "C57BL/6J"
