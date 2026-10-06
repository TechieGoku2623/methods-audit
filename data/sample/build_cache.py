"""Rebuild the committed LLM cache from regex spans on the five samples.

Indirect stays empty on purpose. Cache quotes must occur in the XML.
"""

from __future__ import annotations

import json
from pathlib import Path

from methods_audit.extract import regex_extract
from methods_audit.fields import FIELD_NAMES

HERE = Path(__file__).resolve().parent
FILES = {
    "complete": HERE / "complete.xml",
    "no-guide": HERE / "no-guide.xml",
    "guide-mismatch": HERE / "guide-mismatch.xml",
    "bad-cell-line": HERE / "bad-cell-line.xml",
    "indirect": HERE / "indirect.xml",
}


def main() -> None:
    papers: dict[str, object] = {}
    for paper_id, path in FILES.items():
        text = path.read_text(encoding="utf-8")
        extraction = regex_extract(text, paper_id)
        fields = {}
        if paper_id != "indirect":
            for name in FIELD_NAMES:
                item = extraction.fields[name]
                fields[name] = item.model_dump()
        else:
            for name in FIELD_NAMES:
                fields[name] = {
                    "field": name,
                    "status": "missing",
                    "value": None,
                    "start": None,
                    "end": None,
                    "quote": None,
                    "source": "missing",
                }
        papers[paper_id] = {
            "model": "committed-cache",
            "note": (
                "Phase 0 cache. Quotes must appear in the source XML. "
                "Indirect is empty: the model is not allowed to guess."
                if paper_id == "indirect"
                else "Regex-derived spans committed so later phases can swap in a model cache."
            ),
            "fields": fields,
        }
    payload = {
        "disclaimer": "Committed LLM response cache. No live API. Quotes are span-grounded.",
        "papers": papers,
    }
    path = HERE / "llm_cache.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
