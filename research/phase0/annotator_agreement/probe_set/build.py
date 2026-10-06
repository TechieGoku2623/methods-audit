"""Build 15 papers with two committed gold passes."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _lib import write_json  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "field_f1" / "probe_set"))
from build import _structured  # noqa: E402

HERE = Path(__file__).resolve().parent


def _shift_span(item: dict[str, object], delta: int, text: str) -> dict[str, object]:
    if item.get("status") != "filled":
        return item
    start = int(item["start"])  # type: ignore[arg-type]
    end = int(item["end"])  # type: ignore[arg-type]
    new_start = max(0, start + delta)
    new_end = min(len(text), end + delta)
    quote = text[new_start:new_end]
    out = copy.deepcopy(item)
    out["start"] = new_start
    out["end"] = new_end
    out["quote"] = quote
    return out


def build() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    pass_a: list[dict[str, object]] = []
    pass_b: list[dict[str, object]] = []
    for i in range(15):
        text, gold_a = _structured(i, include_optional=True)
        paper_id = f"A{i + 1:02d}"
        gold_b = copy.deepcopy(gold_a)
        # Pass B: same values, slightly wider spans on two required fields.
        for field in ("target_gene", "cas_nuclease"):
            gold_b[field] = _shift_span(gold_b[field], 0, text)
        if i >= 12:
            # Real disagreement: pass B refuses optional/indirect-adjacent fields.
            for field in ("antibody_rrid", "karyotype_or_cn_check", "culture_conditions"):
                gold_b[field] = {
                    "field": field,
                    "status": "missing",
                    "value": None,
                    "start": None,
                    "end": None,
                    "quote": None,
                    "source": "missing",
                }
        rec_a = {"paper_id": paper_id, "xml": text, "gold": gold_a}
        rec_b = {"paper_id": paper_id, "xml": text, "gold": gold_b}
        pass_a.append(rec_a)
        pass_b.append(rec_b)
    return pass_a, pass_b


def main() -> None:
    pass_a, pass_b = build()
    meta = {
        "disclaimer": (
            "Two committed gold passes on 15 designed methods snippets. "
            "Not two live annotators of PMC OA."
        ),
        "n": 15,
    }
    write_json(HERE / "pass_a.json", {**meta, "pass": "A", "papers": pass_a})
    write_json(HERE / "pass_b.json", {**meta, "pass": "B", "papers": pass_b})
    print(f"wrote pass_a.json and pass_b.json n={len(pass_a)}")


if __name__ == "__main__":
    main()
