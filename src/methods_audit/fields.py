"""Replication schema for CRISPR methods sections.

Defined before any extractor. Required / optional / conditional status is
grounded in published reporting guidelines, not in what a model finds easy.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Need = Literal["required", "optional", "conditional"]


class FieldSpec(BaseModel):
    name: str
    need: Need
    condition: str | None
    guideline: str
    description: str


# 32 fields. Citations are the reason the field exists, not a claim that any
# one paper used this exact name.
SCHEMA: tuple[FieldSpec, ...] = (
    FieldSpec(
        name="target_gene",
        need="required",
        condition=None,
        guideline="MDAR materials; Nature Portfolio Reporting Summary (genome editing)",
        description="Locus or gene symbol that was edited.",
    ),
    FieldSpec(
        name="species",
        need="required",
        condition=None,
        guideline="MDAR materials; ARRIVE 2.0 (Percie du Sert 2020) when in vivo",
        description="Organism (scientific or common name).",
    ),
    FieldSpec(
        name="genome_build",
        need="required",
        condition=None,
        guideline="Concordet & Haeussler 2018 NAR (CRISPOR): coordinates are build-specific",
        description="Reference assembly (GRCh38, hg38, GRCm39, …).",
    ),
    FieldSpec(
        name="cas_nuclease",
        need="required",
        condition=None,
        guideline="Hsu, Lander, Zhang 2014 Cell; Nature Reporting Summary",
        description="Nuclease family (SpCas9, Cas12a, base editor, …).",
    ),
    FieldSpec(
        name="guide_sequence",
        need="required",
        condition=None,
        guideline="Nature Reporting Summary; Concordet & Haeussler 2018 — most common omission",
        description="Protospacer / sgRNA sequence as written.",
    ),
    FieldSpec(
        name="pam_motif",
        need="required",
        condition=None,
        guideline="Hsu, Lander, Zhang 2014 Cell",
        description="PAM as reported (NGG, TTTV, …).",
    ),
    FieldSpec(
        name="delivery_method",
        need="required",
        condition=None,
        guideline="Nature Reporting Summary; MDAR materials",
        description="How the editor entered the cell (RNP, lentivirus, electroporation, …).",
    ),
    FieldSpec(
        name="cell_line_or_organism",
        need="required",
        condition=None,
        guideline="MDAR materials; Bairoch 2018 J Biomol Tech (Cellosaurus)",
        description="Named cell line or organismal system.",
    ),
    FieldSpec(
        name="editing_assay",
        need="required",
        condition=None,
        guideline="Nature Reporting Summary; MIQE (Bustin 2009) when qPCR is the assay",
        description="How editing was measured (T7E1, Sanger, NGS, ICE, TIDE, …).",
    ),
    FieldSpec(
        name="n_biological_replicates",
        need="required",
        condition=None,
        guideline="MDAR analysis; ARRIVE 2.0",
        description="Biological replicate count.",
    ),
    FieldSpec(
        name="nontargeting_control",
        need="required",
        condition=None,
        guideline="Nature Reporting Summary; MDAR design",
        description="Non-targeting / scramble / mock control as stated.",
    ),
    FieldSpec(
        name="off_target_analysis_method",
        need="required",
        condition=None,
        guideline="Nature Reporting Summary; Haeussler et al. 2016 Genome Biol",
        description="Off-target method (GUIDE-seq, CIRCLE-seq, CRISPOR, Cas-OFFinder, …).",
    ),
    FieldSpec(
        name="cell_line_rrid",
        need="conditional",
        condition="filled when cell_line_or_organism names a cultured line",
        guideline="Cell Press STAR Methods; Cellosaurus / RRID portal",
        description="CVCL_ / RRID for the line.",
    ),
    FieldSpec(
        name="donor_template_type",
        need="conditional",
        condition="filled when HDR / knock-in / donor is stated",
        guideline="Nature Reporting Summary (homology-directed repair)",
        description="ssODN, dsDNA, plasmid donor, …",
    ),
    FieldSpec(
        name="donor_sequence",
        need="conditional",
        condition="filled when HDR / knock-in / donor is stated",
        guideline="Nature Reporting Summary",
        description="Donor sequence or a repository identifier for it.",
    ),
    FieldSpec(
        name="animal_strain",
        need="conditional",
        condition="filled when an in-vivo animal experiment is stated",
        guideline="ARRIVE 2.0",
        description="Strain (C57BL/6J, …).",
    ),
    FieldSpec(
        name="n_animals",
        need="conditional",
        condition="filled when an in-vivo animal experiment is stated",
        guideline="ARRIVE 2.0",
        description="Number of animals.",
    ),
    FieldSpec(
        name="animal_sex",
        need="conditional",
        condition="filled when an in-vivo animal experiment is stated",
        guideline="ARRIVE 2.0",
        description="Sex of animals, or 'both' / 'not reported' if stated.",
    ),
    FieldSpec(
        name="guide_strand",
        need="optional",
        condition=None,
        guideline="Concordet & Haeussler 2018",
        description="Watson / Crick or + / −.",
    ),
    FieldSpec(
        name="genomic_coordinates",
        need="optional",
        condition=None,
        guideline="Concordet & Haeussler 2018",
        description="chr:start-end on the stated build.",
    ),
    FieldSpec(
        name="cas_variant",
        need="optional",
        condition=None,
        guideline="Hsu, Lander, Zhang 2014 Cell; subsequent high-fidelity variants",
        description="eSpCas9, SpCas9-HF1, dCas9, … if distinguished from the family.",
    ),
    FieldSpec(
        name="selection_method",
        need="optional",
        condition=None,
        guideline="MDAR materials",
        description="Antibiotic / FACS / puromycin, …",
    ),
    FieldSpec(
        name="reported_editing_efficiency",
        need="optional",
        condition=None,
        guideline="NIST Genome Editing Consortium measurement framing",
        description="Numeric efficiency as written. Not validated here.",
    ),
    FieldSpec(
        name="clone_isolation",
        need="optional",
        condition=None,
        guideline="MDAR materials",
        description="Whether single-cell clones were isolated.",
    ),
    FieldSpec(
        name="off_target_sites_tested",
        need="optional",
        condition=None,
        guideline="Haeussler et al. 2016 Genome Biol",
        description="Count or list of nominated sites actually assayed.",
    ),
    FieldSpec(
        name="antibody_rrid",
        need="optional",
        condition=None,
        guideline="Cell Press STAR Methods; Antibody Registry",
        description="AB_ RRID if an antibody is named.",
    ),
    FieldSpec(
        name="plasmid_rrid",
        need="optional",
        condition=None,
        guideline="Addgene / RRID; STAR Methods",
        description="Addgene catalog or RRID:Addgene_…",
    ),
    FieldSpec(
        name="guide_design_software",
        need="optional",
        condition=None,
        guideline="Concordet & Haeussler 2018; Labun et al. CHOPCHOP",
        description="CRISPOR, CHOPCHOP, Benchling, …",
    ),
    FieldSpec(
        name="harvest_timepoint",
        need="optional",
        condition=None,
        guideline="MDAR materials",
        description="Hours or days after delivery.",
    ),
    FieldSpec(
        name="culture_conditions",
        need="optional",
        condition=None,
        guideline="MDAR materials",
        description="Medium / temperature / atmosphere as written.",
    ),
    FieldSpec(
        name="statistical_test",
        need="optional",
        condition=None,
        guideline="MDAR analysis",
        description="Named test (t-test, ANOVA, …).",
    ),
    FieldSpec(
        name="karyotype_or_cn_check",
        need="optional",
        condition=None,
        guideline="MDAR materials; Cellosaurus commentary on misidentified lines",
        description="Karyotype or copy-number check of the edited line.",
    ),
)

FIELD_INDEX: dict[str, FieldSpec] = {spec.name: spec for spec in SCHEMA}
FIELD_NAMES: tuple[str, ...] = tuple(spec.name for spec in SCHEMA)
REQUIRED_ALWAYS: tuple[str, ...] = tuple(s.name for s in SCHEMA if s.need == "required")
CONDITIONAL: tuple[str, ...] = tuple(s.name for s in SCHEMA if s.need == "conditional")
OPTIONAL: tuple[str, ...] = tuple(s.name for s in SCHEMA if s.need == "optional")

assert 25 <= len(SCHEMA) <= 40
assert len(SCHEMA) == 32
