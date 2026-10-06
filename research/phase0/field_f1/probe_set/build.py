"""Build 50 committed synthetic methods snippets with gold spans."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _lib import write_json  # noqa: E402

from methods_audit.fields import FIELD_NAMES  # noqa: E402
from methods_audit.schemas import SpanValue  # noqa: E402

HERE = Path(__file__).resolve().parent

GENES = [
    ("TP53", "GGCGCCATCTACAAGCAGTC"),
    ("EGFR", "AATTCCCGTCGCTATCAAGG"),
    ("CFTR", "ATGGCGCTCTGGGCCTGTTC"),
    ("HBB", "GATGAAGTTGGTGGTGAGGC"),
]
LINES = [
    ("HEK293T", "RRID:CVCL_0063"),
    ("K562", "RRID:CVCL_0004"),
    ("HeLa", "RRID:CVCL_0030"),
    ("U2OS", "RRID:CVCL_0042"),
]


def _gold(text: str, field: str, value: str, *, after: str | None = None) -> dict[str, object]:
    start_at = text.find(after) if after else 0
    if start_at < 0:
        start_at = 0
    start = text.find(value, start_at)
    if start < 0:
        start = text.find(value)
    if start < 0:
        raise ValueError(f"{field} value {value!r} not in text")
    return SpanValue(
        field=field,
        status="filled",
        value=value,
        start=start,
        end=start + len(value),
        quote=value,
        source="gold",
    ).model_dump()


def _missing(field: str) -> dict[str, object]:
    return SpanValue(field=field, status="missing", source="missing").model_dump()


def _blank_gold() -> dict[str, dict[str, object]]:
    return {name: _missing(name) for name in FIELD_NAMES}


def _structured(
    i: int, include_optional: bool, omit: str | None = None
) -> tuple[str, dict[str, dict[str, object]]]:
    gene, guide = GENES[i % len(GENES)]
    line, rrid = LINES[i % len(LINES)]
    cas = "SpCas9" if i % 2 == 0 else "Cas9"
    delivery = ("electroporation", "lentivirus", "lipofection", "RNP")[i % 4]
    assay = ("amplicon NGS", "T7E1", "Sanger sequencing", "ICE")[i % 4]
    ot = ("GUIDE-seq", "CRISPOR", "Cas-OFFinder", "CIRCLE-seq")[i % 4]
    control = "non-targeting sgRNA" if i % 2 == 0 else "scrambled control"
    n = 3 + (i % 3)
    bits = [
        f"We targeted the {gene} locus in Homo sapiens (GRCh38) using {cas}.",
        (
            f"The guide RNA sequence was {guide}."
            if omit != "guide_sequence"
            else "A targeting reagent was used."
        ),
        "The PAM motif was NGG.",
        f"Delivery used {delivery} into {line} ({rrid}).",
        f"A {control} was included.",
        f"Editing was measured by {assay} (n = {n} biological replicates).",
        f"Off-target analysis used {ot}.",
    ]
    extras: dict[str, str] = {}
    if include_optional:
        extras = {
            "guide_design_software": "CRISPOR",
            "harvest_timepoint": "72 hours",
            "selection_method": "puromycin",
            "clone_isolation": "single-cell clones",
            "statistical_test": "Student's t-test",
            "plasmid_rrid": "Addgene 62988",
            "reported_editing_efficiency": "55%",
            "off_target_sites_tested": "11",
            "guide_strand": "Watson",
            "cas_variant": "eSpCas9",
            "antibody_rrid": "RRID:AB_331743",
            "karyotype_or_cn_check": "karyotyped",
            "culture_conditions": "DMEM with 10% FBS at 37 °C",
            "genomic_coordinates": "chr17:7676594-7676613",
        }
        bits.append(
            f"Guides were designed with {extras['guide_design_software']} "
            f"on strand {extras['guide_strand']}. "
            f"Coordinates {extras['genomic_coordinates']}. "
            f"Variant {extras['cas_variant']}. "
            f"Cells were harvested {extras['harvest_timepoint']} after "
            f"{extras['selection_method']} selection. "
            f"We isolated {extras['clone_isolation']}. "
            f"Editing efficiency of {extras['reported_editing_efficiency']}. "
            f"{extras['off_target_sites_tested']} nominated off-target sites "
            f"were assayed. "
            f"The plasmid was {extras['plasmid_rrid']}. "
            f"Antibody {extras['antibody_rrid']}. "
            f"Statistics used {extras['statistical_test']}. "
            f"Clones were {extras['karyotype_or_cn_check']}. "
            f"Culture used {extras['culture_conditions']}."
        )
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<article><sec sec-type="methods"><p>\n'
        + " ".join(bits)
        + "\n</p></sec></article>\n"
    )
    gold = _blank_gold()
    values = {
        "target_gene": gene,
        "species": "Homo sapiens",
        "genome_build": "GRCh38",
        "cas_nuclease": cas,
        "pam_motif": "NGG",
        "delivery_method": delivery,
        "cell_line_or_organism": line,
        "cell_line_rrid": rrid,
        "editing_assay": assay,
        "n_biological_replicates": str(n),
        "nontargeting_control": control,
        "off_target_analysis_method": ot,
    }
    if omit != "guide_sequence":
        values["guide_sequence"] = guide
    values.update(extras)
    hints = {
        "n_biological_replicates": "n = ",
        "off_target_sites_tested": "efficiency of",
        "harvest_timepoint": "harvested",
        "guide_sequence": "guide RNA sequence was ",
        "pam_motif": "PAM motif was ",
        "delivery_method": "Delivery used ",
    }
    for field, value in values.items():
        gold[field] = _gold(text, field, value, after=hints.get(field))
    return text, gold


def _indirect(i: int) -> tuple[str, dict[str, dict[str, object]]]:
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<article><sec sec-type="methods"><p>\n'
        f"Genome editing was performed as previously described (Smith et al., {2018 + (i % 5)}). "
        "Cells were treated using standard laboratory protocols. Outcomes were assessed "
        "with established assays. Reagents were used according to the "
        "manufacturers' instructions.\n"
        "</p></sec></article>\n"
    )
    return text, _blank_gold()


def build() -> list[dict[str, object]]:
    papers: list[dict[str, object]] = []
    for i in range(30):
        text, gold = _structured(i, include_optional=True)
        papers.append(
            {
                "paper_id": f"P{i + 1:02d}",
                "cohort": "structured",
                "xml": text,
                "gold": gold,
            }
        )
    for i in range(10):
        text, gold = _structured(i + 30, include_optional=False, omit="guide_sequence")
        papers.append(
            {
                "paper_id": f"P{i + 31:02d}",
                "cohort": "no_guide",
                "xml": text,
                "gold": gold,
            }
        )
    for i in range(10):
        text, gold = _indirect(i)
        papers.append(
            {
                "paper_id": f"P{i + 41:02d}",
                "cohort": "indirect",
                "xml": text,
                "gold": gold,
            }
        )
    if len(papers) != 50:
        raise RuntimeError(f"expected 50 papers, got {len(papers)}")
    return papers


def main() -> None:
    papers = build()
    write_json(
        HERE / "papers.json",
        {
            "disclaimer": (
                "Designed PMC-OA-style methods snippets with gold spans. Not a live PMC dump."
            ),
            "n": len(papers),
            "papers": papers,
        },
    )
    print(f"wrote {HERE / 'papers.json'} n={len(papers)}")


if __name__ == "__main__":
    main()
