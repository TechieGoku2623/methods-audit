"""methods-audit: span-grounded CRISPR methods extraction and completeness scoring.

Research / decision-support tooling. Completeness is not quality, novelty, or
reproducibility. Unfilled fields stay missing. Nothing is inferred. Phase 0
uses designed PMC-OA-style XML snippets, not a live PMC dump.
"""

__version__ = "0.1.0"

SAFETY_DISCLAIMER = (
    "Research tool only. Completeness scoring is not a judgment of experimental "
    "quality or of whether a paper should have been published. Phase 0 records "
    "are designed synthetic methods snippets, not a live PMC OA dump. Unfilled "
    "fields are missing, never inferred."
)
