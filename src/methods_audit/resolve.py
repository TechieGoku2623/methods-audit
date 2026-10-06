"""Resolve a paper path or a committed DOI to sample XML.

`--doi` is allowed only for the five designed samples. Unknown DOIs fail
closed. No Crossref, no network.
"""

from __future__ import annotations

import json
from pathlib import Path

from methods_audit.config import get_settings


def load_doi_map() -> dict[str, str]:
    path = get_settings().sample_dir / "doi_map.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in raw["dois"].items()}


def paper_id_from_path(path: Path) -> str:
    return path.stem


def resolve_paper(*, paper: Path | None, doi: str | None) -> tuple[Path, str]:
    if paper is not None and doi:
        raise ValueError("Pass --paper or --doi, not both.")
    if paper is None and not doi:
        raise ValueError("Provide --paper PATH or --doi DOI.")
    root = get_settings().repo_root
    sample_dir = get_settings().sample_dir
    if doi:
        mapping = load_doi_map()
        key = doi.strip()
        if key not in mapping:
            known = ", ".join(sorted(mapping))
            raise KeyError(f"DOI {doi!r} is not in the committed five-sample map. Known: {known}")
        path = sample_dir / mapping[key]
        return path, paper_id_from_path(path)
    assert paper is not None
    path = paper if paper.is_absolute() else (root / paper)
    if not path.is_file():
        alt = sample_dir / paper.name
        if alt.is_file():
            path = alt
        else:
            raise FileNotFoundError(f"Paper not found: {paper}")
    return path, paper_id_from_path(path)
