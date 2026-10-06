"""Data contracts for extractions, scores, and demo samples."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

FieldStatus = Literal["filled", "missing"]
CheckStatus = Literal["pass", "fail", "skipped"]


class SpanValue(BaseModel):
    """One field value with a required span into the source XML."""

    field: str
    status: FieldStatus
    value: str | None = None
    start: int | None = None
    end: int | None = None
    quote: str | None = None
    source: Literal["regex", "cache", "gold", "missing"] = "missing"

    def filled(self) -> bool:
        return self.status == "filled" and self.value is not None and self.quote is not None


class Extraction(BaseModel):
    paper_id: str
    fields: dict[str, SpanValue]
    notes: str = ""


class CompletenessScore(BaseModel):
    paper_id: str
    n_applicable: int
    n_filled: int
    completeness: float
    applicable_fields: list[str]
    missing_fields: list[str]
    rationale: str


class ConsistencyCheck(BaseModel):
    name: str
    status: CheckStatus
    detail: str


class SamplePaper(BaseModel):
    sample_id: str
    filename: str
    path_exercised: str
    why_present: str
    expected_behavior: str


class CacheEntry(BaseModel):
    paper_id: str
    fields: dict[str, SpanValue] = Field(default_factory=dict)
    model: str = "committed-cache"
    note: str = ""
