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
    g = guide.upper().replace("U", "T")
    gene = gene_seq.upper().replace("U", "T")
    if len(g) > len(gene):
        return None
    best: int | None = None
    for probe in (g, reverse_complement(g)):
        for i in range(0, len(gene) - len(probe) + 1):
            dist = hamming(probe, gene[i : i + len(probe)])
            if best is None or dist < best:
                best = dist
    return best


def load_gene_sequences(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in raw["genes"].items()}


def load_misidentified(path: Path) -> dict[str, dict[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): {str(a): str(b) for a, b in v.items()} for k, v in raw["lines"].items()}


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
        )
    dist = min_mismatch(guide, seq)
    if dist is None:
        return ConsistencyCheck(
            name="guide_targets_gene",
            status="fail",
            detail="Guide longer than committed gene sequence.",
        )
    if dist <= MAX_MISMATCH:
        return ConsistencyCheck(
            name="guide_targets_gene",
            status="pass",
            detail=f"Guide aligns to {gene} with {dist} mismatch(es).",
        )
    return ConsistencyCheck(
        name="guide_targets_gene",
        status="fail",
        detail=(
            f"Stated guide does not target stated gene {gene} "
            f"(best Hamming {dist} > {MAX_MISMATCH})."
        ),
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
