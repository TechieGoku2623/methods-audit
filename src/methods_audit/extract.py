"""Span-level CRISPR methods extractor.

Phase 0 is regex plus a committed response cache. A field is filled only
when a quote exists in the source text. Nothing is inferred from nearby
words, gene names, or "as previously described."
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from re import Pattern

from methods_audit.cache import CacheStore
from methods_audit.fields import FIELD_NAMES
from methods_audit.schemas import Extraction, SpanValue

# Each pattern captures the value in group 1. Order is first-match wins.
PATTERNS: dict[str, tuple[Pattern[str], ...]] = {
    "target_gene": (
        re.compile(r"target(?:ed|ing)?(?: the)? gene(?: locus)?\s+([A-Z0-9]{2,10})", re.I),
        re.compile(r"the ([A-Z0-9]{2,10}) locus", re.I),
    ),
    "species": (re.compile(r"\b(Homo sapiens|Mus musculus|human|mouse|rat)\b", re.I),),
    "genome_build": (re.compile(r"\b(GRCh38|GRCh37|hg38|hg19|GRCm39|GRCm38|mm39|mm10)\b"),),
    "cas_nuclease": (
        re.compile(r"\b(SpCas9|SaCas9|Cas12a|AsCas12a|LbCas12a|Cas9|Cas13|base editor)\b"),
    ),
    "guide_sequence": (
        re.compile(
            r"(?:guide(?: RNA)?|sgRNA|gRNA|protospacer)(?: sequence)?(?: was|:)?\s*"
            r"([ACGTU]{17,24})",
            re.I,
        ),
    ),
    "pam_motif": (
        re.compile(r"\bPAM(?: motif)?(?: was|:)?\s*([NT]{3,4})\b"),
        re.compile(r"\b(NGG|TTTV|TTTA|NGN)\b"),
    ),
    "delivery_method": (
        re.compile(
            r"\b(RNP|ribonucleoprotein|lentivirus|lipofection|electroporation|"
            r"nucleofection|AAV|lipid nanoparticle)\b",
            re.I,
        ),
    ),
    "cell_line_or_organism": (
        re.compile(
            r"\b(HEK293T|HEK293|HeLa|K562|INT-407|KB|WISH|Hep-2|MDA-MB-435|"
            r"Chang liver|MCF-7|U2OS|iPSC|C57BL/6J mice)\b"
        ),
    ),
    "editing_assay": (
        re.compile(
            r"\b(T7E1|T7EI|Sanger sequencing|amplicon NGS|NGS|ICE|TIDE|"
            r"qPCR|ddPCR|Western blot)\b",
            re.I,
        ),
    ),
    "n_biological_replicates": (
        re.compile(r"(?:n\s*=\s*|biological replicates?[^\d]{0,16})(\d+)", re.I),
    ),
    "nontargeting_control": (
        re.compile(
            r"\b(non[- ]targeting(?: sgRNA| control)?|scramble(?:d)? control|mock transfection)\b",
            re.I,
        ),
    ),
    "off_target_analysis_method": (
        re.compile(
            r"\b(GUIDE-seq|CIRCLE-seq|CHANGE-seq|CRISPOR|Cas-OFFinder|"
            r"in silico off-target|CHOPCHOP)\b",
            re.I,
        ),
    ),
    "cell_line_rrid": (re.compile(r"\b(RRID:CVCL_[A-Z0-9]+|CVCL_[A-Z0-9]+)\b"),),
    "donor_template_type": (
        re.compile(r"\b(ssODN|ssDNA donor|dsDNA donor|plasmid donor|HDR template)\b", re.I),
    ),
    "donor_sequence": (re.compile(r"(?:donor(?: sequence)?(?: was|:)?\s*)([ACGTU]{20,80})", re.I),),
    "animal_strain": (re.compile(r"\b(C57BL/6J|BALB/c|NSG|Sprague-Dawley)\b"),),
    "n_animals": (re.compile(r"(\d+) animals\b", re.I),),
    "animal_sex": (
        re.compile(r"\b(male and female|both sexes|female only|male only|females|males)\b", re.I),
    ),
    "guide_strand": (re.compile(r"\bstrand\s+(Watson|Crick|\+|−|-)\b", re.I),),
    "genomic_coordinates": (re.compile(r"\b((?:chr)?[0-9XYM]{1,2}:\d+-\d+)\b"),),
    "cas_variant": (re.compile(r"\b(eSpCas9|SpCas9-HF1|HypaCas9|dCas9|nCas9|Cas9nickase)\b"),),
    "selection_method": (
        re.compile(r"\b(puromycin|FACS|blasticidin|hygromycin|neomycin selection)\b", re.I),
    ),
    "reported_editing_efficiency": (
        re.compile(r"(?:editing efficiency|indel rate)\s+(?:of\s+)?(\d+(?:\.\d+)?\s*%)", re.I),
    ),
    "clone_isolation": (
        re.compile(r"\b(single-cell clones?|limiting dilution|clone isolation)\b", re.I),
    ),
    "off_target_sites_tested": (
        re.compile(r"(\d+) (?:nominated |predicted )?off-target sites", re.I),
    ),
    "antibody_rrid": (re.compile(r"\b(RRID:AB_\d+|AB_\d+)\b"),),
    "plasmid_rrid": (re.compile(r"\b(Addgene\s+\d+|RRID:Addgene_\d+)\b", re.I),),
    "guide_design_software": (re.compile(r"\b(CRISPOR|CHOPCHOP|Benchling|GuideScan)\b"),),
    "harvest_timepoint": (
        re.compile(r"(?:harvest(?:ed)?|collected)\s+(\d+\s*(?:hours|days|h))", re.I),
    ),
    "culture_conditions": (
        re.compile(
            r"\b((?:DMEM|RPMI)[^.;]{0,40}(?:37\s*°C|37C)[^.;]{0,20})\b",
            re.I,
        ),
    ),
    "statistical_test": (
        re.compile(
            r"\b(Student(?:'s)? t-test|Welch t-test|one-way ANOVA|"
            r"two-way ANOVA|Mann-Whitney)\b"
        ),
    ),
    "karyotype_or_cn_check": (
        re.compile(r"\b(karyotyp(?:e|ed)|copy-number check|SNP array)\b", re.I),
    ),
}


def _empty(paper_id: str) -> Extraction:
    fields = {
        name: SpanValue(field=name, status="missing", source="missing") for name in FIELD_NAMES
    }
    return Extraction(paper_id=paper_id, fields=fields)


def _from_match(field: str, match: re.Match[str], source: str) -> SpanValue:
    value = match.group(1).strip()
    return SpanValue(
        field=field,
        status="filled",
        value=value,
        start=match.start(1),
        end=match.end(1),
        quote=value,
        source=source,  # type: ignore[arg-type]
    )


def regex_extract(text: str, paper_id: str) -> Extraction:
    extraction = _empty(paper_id)
    for field, patterns in PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                extraction.fields[field] = _from_match(field, match, "regex")
                break
    return extraction


def _quote_in_text(quote: str, text: str) -> tuple[int, int] | None:
    idx = text.find(quote)
    if idx < 0:
        return None
    return idx, idx + len(quote)


def merge_cache(extraction: Extraction, cache: CacheStore, text: str) -> Extraction:
    """Fill missing fields from the committed cache only when the quote is present."""

    entry = cache.get(extraction.paper_id)
    if entry is None:
        return extraction
    for field, item in entry.fields.items():
        current = extraction.fields[field]
        if current.filled():
            continue
        if item.status != "filled" or not item.quote or not item.value:
            continue
        loc = _quote_in_text(item.quote, text)
        if loc is None:
            continue
        start, end = loc
        extraction.fields[field] = SpanValue(
            field=field,
            status="filled",
            value=item.value,
            start=start,
            end=end,
            quote=item.quote,
            source="cache",
        )
    return extraction


def extract(
    text: str,
    paper_id: str,
    cache: CacheStore | None = None,
) -> Extraction:
    extraction = regex_extract(text, paper_id)
    if cache is not None:
        extraction = merge_cache(extraction, cache, text)
    return extraction


def extract_many(
    items: Iterable[tuple[str, str]],
    cache: CacheStore | None = None,
) -> list[Extraction]:
    return [extract(text, paper_id, cache=cache) for paper_id, text in items]
