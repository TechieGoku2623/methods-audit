"""Deterministic completeness over the extracted structure.

Scores presence, not quality. A wrong guide still counts as a filled
guide_sequence; complementarity is a separate consistency check.
"""

from __future__ import annotations

from methods_audit.fields import REQUIRED_ALWAYS
from methods_audit.schemas import CompletenessScore, Extraction, SpanValue


def _value(extraction: Extraction, name: str) -> str | None:
    item = extraction.fields.get(name)
    if item is None or not item.filled():
        return None
    return item.value


def _looks_like_cell_line(value: str | None) -> bool:
    if value is None:
        return False
    organism_words = {"mouse", "mice", "human", "rat", "organism", "c57bl/6j mice"}
    return value.lower() not in organism_words


def _hdr_stated(extraction: Extraction) -> bool:
    donor_type = _value(extraction, "donor_template_type")
    donor_seq = _value(extraction, "donor_sequence")
    return donor_type is not None or donor_seq is not None


def _in_vivo_stated(extraction: Extraction) -> bool:
    return any(
        _value(extraction, name) is not None
        for name in ("animal_strain", "n_animals", "animal_sex")
    ) or ((_value(extraction, "cell_line_or_organism") or "").lower().endswith("mice"))


def applicable_fields(extraction: Extraction) -> list[str]:
    names = list(REQUIRED_ALWAYS)
    if _looks_like_cell_line(_value(extraction, "cell_line_or_organism")):
        names.append("cell_line_rrid")
    if _hdr_stated(extraction):
        names.extend(["donor_template_type", "donor_sequence"])
    if _in_vivo_stated(extraction):
        names.extend(["animal_strain", "n_animals", "animal_sex"])
    # Unique, stable order.
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def _filled(item: SpanValue | None) -> bool:
    return item is not None and item.filled()


def score_completeness(extraction: Extraction) -> CompletenessScore:
    applicable = applicable_fields(extraction)
    missing = [name for name in applicable if not _filled(extraction.fields.get(name))]
    n_filled = len(applicable) - len(missing)
    completeness = n_filled / len(applicable) if applicable else 0.0
    return CompletenessScore(
        paper_id=extraction.paper_id,
        n_applicable=len(applicable),
        n_filled=n_filled,
        completeness=completeness,
        applicable_fields=applicable,
        missing_fields=missing,
        rationale=(
            f"{n_filled}/{len(applicable)} applicable fields filled. "
            "Optional fields are not in the denominator. Quality is not scored."
        ),
    )
