"""Committed LLM response cache. No live calls in Phase 0."""

from __future__ import annotations

import json
from pathlib import Path

from methods_audit.schemas import CacheEntry, SpanValue


class CacheStore:
    def __init__(self, entries: dict[str, CacheEntry]) -> None:
        self.entries = entries

    def get(self, paper_id: str) -> CacheEntry | None:
        return self.entries.get(paper_id)

    def __contains__(self, paper_id: str) -> bool:
        return paper_id in self.entries


def load_cache(path: Path) -> CacheStore:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries: dict[str, CacheEntry] = {}
    for paper_id, body in raw["papers"].items():
        fields = {
            name: SpanValue.model_validate(item) for name, item in body.get("fields", {}).items()
        }
        entries[paper_id] = CacheEntry(
            paper_id=paper_id,
            fields=fields,
            model=str(body.get("model", "committed-cache")),
            note=str(body.get("note", "")),
        )
    return CacheStore(entries)
