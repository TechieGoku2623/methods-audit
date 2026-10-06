"""Cross-checks on extracted structure. These are the real findings."""

from __future__ import annotations

import json
from pathlib import Path

from methods_audit.schemas import ConsistencyCheck, Extraction

COMPLEMENT = str.maketrans("ACGTUacgtu", "TGCAAtgcaa")
MAX_MISMATCH = 2


def reverse_complement(seq: str) -> str:
    return seq.translate(COMPLEMENT)[::-1]


def hamming(left: str, right: str) -> int:
    return sum(a != b for a, b in zip(left, right, strict=True))


def min_mismatch(guide: str, gene_seq: str) -> int | None:
    aligned = best_alignment(guide, gene_seq)
    return None if aligned is None else aligned[0]


def best_alignment(guide: str, gene_seq: str) -> tuple[int, str, int, str] | None:
    """Return (distance, strand, offset, window) for the best Hamming hit."""

    g = guide.upper().replace("U", "T")
    gene = gene_seq.upper().replace("U", "T")
    if len(g) > len(gene):
        return None
    best: tuple[int, str, int, str] | None = None
    for strand, probe in (("forward", g), ("reverse_complement", reverse_complement(g))):
        for i in range(0, len(gene) - len(probe) + 1):
            window = gene[i : i + len(probe)]
            dist = hamming(probe, window)
            if best is None or dist < best[0]:
                best = (dist, strand, i, window)
    return best


def load_gene_sequences(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in raw["genes"].items()}


def load_misidentified(path: Path) -> dict[str, dict[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): {str(a): str(b) for a, b in v.items()} for k, v in raw["lines"].items()}


def _span_tuple(item: object) -> tuple[int, int] | None:
    start = getattr(item, "start", None)
    end = getattr(item, "end", None)
    if start is None or end is None:
        return None
    return (int(start), int(end))


def check_guide_targets_gene(
    extraction: Extraction,
    gene_sequences: dict[str, str],
) -> ConsistencyCheck:
    gene_item = extraction.fields.get("target_gene")
    guide_item = extraction.fields.get("guide_sequence")
    if gene_item is None or not gene_item.filled() or guide_item is None or not guide_item.filled():
        return ConsistencyCheck(
            name="guide_targets_gene",
            status="skipped",
            detail="target_gene or guide_sequence is missing; not inferred.",
        )
    gene = gene_item.value or ""
    guide = guide_item.value or ""
    seq = gene_sequences.get(gene.upper()) or gene_sequences.get(gene)
    if seq is None:
        return ConsistencyCheck(
            name="guide_targets_gene",
            status="skipped",
            detail=f"No committed sequence for gene {gene}.",
            left_field="target_gene",
            left_quote=gene_item.quote,
            left_span=_span_tuple(gene_item),
            right_field="guide_sequence",
            right_quote=guide_item.quote,
            right_span=_span_tuple(guide_item),
        )
    aligned = best_alignment(guide, seq)
    if aligned is None:
        return ConsistencyCheck(
            name="guide_targets_gene",
            status="fail",
            detail="Guide longer than committed gene sequence.",
            left_field="target_gene",
            left_quote=gene_item.quote,
            left_span=_span_tuple(gene_item),
            right_field="guide_sequence",
            right_quote=guide_item.quote,
            right_span=_span_tuple(guide_item),
        )
    dist, strand, offset, window = aligned
    alignment = (
        f"guide={guide}  window={window}  strand={strand}  "
        f"offset={offset}  Hamming={dist}  max_allowed={MAX_MISMATCH}"
    )
    if dist <= MAX_MISMATCH:
        return ConsistencyCheck(
            name="guide_targets_gene",
            status="pass",
            detail=f"Guide aligns to {gene} with {dist} mismatch(es).",
            left_field="target_gene",
            left_quote=gene_item.quote,
            left_span=_span_tuple(gene_item),
            right_field="guide_sequence",
            right_quote=guide_item.quote,
            right_span=_span_tuple(guide_item),
            alignment=alignment,
        )
    return ConsistencyCheck(
        name="guide_targets_gene",
        status="fail",
        detail=(
            f"Stated guide does not target stated gene {gene} "
            f"(best Hamming {dist} > {MAX_MISMATCH})."
        ),
        left_field="target_gene",
        left_quote=gene_item.quote,
        left_span=_span_tuple(gene_item),
        right_field="guide_sequence",
        right_quote=guide_item.quote,
        right_span=_span_tuple(guide_item),
        alignment=alignment,
    )


def check_cell_line_identity(
    extraction: Extraction,
    misidentified: dict[str, dict[str, str]],
) -> ConsistencyCheck:
    item = extraction.fields.get("cell_line_or_organism")
    if item is None or not item.filled() or item.value is None:
        return ConsistencyCheck(
            name="cell_line_identity",
            status="skipped",
            detail="cell_line_or_organism is missing; not inferred.",
        )
    name = item.value
    record = misidentified.get(name)
    if record is None:
        return ConsistencyCheck(
            name="cell_line_identity",
            status="pass",
            detail=f"{name} is not on the committed Cellosaurus-style misidentification list.",
            left_field="cell_line_or_organism",
            left_quote=item.quote,
            left_span=_span_tuple(item),
        )
    return ConsistencyCheck(
        name="cell_line_identity",
        status="fail",
        detail=(
            f"{name} is listed as misidentified "
            f"(reported as {record.get('reported_as', '?')}; "
            f"actually {record.get('actually', '?')}; "
            f"source {record.get('source', '?')})."
        ),
        left_field="cell_line_or_organism",
        left_quote=item.quote,
        left_span=_span_tuple(item),
        identity_record=record,
    )


def run_checks(
    extraction: Extraction,
    gene_sequences: dict[str, str],
    misidentified: dict[str, dict[str, str]],
) -> list[ConsistencyCheck]:
    return [
        check_guide_targets_gene(extraction, gene_sequences),
        check_cell_line_identity(extraction, misidentified),
    ]
