"""Shared I/O helpers for Phase 0 harnesses."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from methods_audit.schemas import Extraction, SpanValue

REPO_ROOT = Path(__file__).resolve().parents[2]


def write_json(path: Path, payload: Mapping[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join([head, sep, body])


def pct(num: float) -> str:
    return f"{num:.3f}"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def gold_to_extraction(paper_id: str, fields: dict[str, Any]) -> Extraction:
    parsed = {name: SpanValue.model_validate(item) for name, item in fields.items()}
    return Extraction(paper_id=paper_id, fields=parsed)
