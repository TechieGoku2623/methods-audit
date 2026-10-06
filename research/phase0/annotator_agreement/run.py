"""Agreement between two committed gold passes on 15 papers."""

from __future__ import annotations

import sys
from pathlib import Path

from methods_audit.fields import FIELD_NAMES

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import gold_to_extraction, load_json, md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _iou(a_start: int | None, a_end: int | None, b_start: int | None, b_end: int | None) -> float:
    if a_start is None or a_end is None or b_start is None or b_end is None:
        return 0.0
    inter = max(0, min(a_end, b_end) - max(a_start, b_start))
    union = max(a_end, b_end) - min(a_start, b_start)
    return inter / union if union else 0.0


def main() -> None:
    pass_a = load_json(HERE / "probe_set" / "pass_a.json")["papers"]
    pass_b = load_json(HERE / "probe_set" / "pass_b.json")["papers"]
    by_id_b = {row["paper_id"]: row for row in pass_b}
    value_agree = 0
    span_agree = 0
    compared = 0
    iou_sum = 0.0
    both_filled = 0
    field_value_agree: dict[str, list[int]] = {name: [] for name in FIELD_NAMES}

    for row in pass_a:
        other = by_id_b[row["paper_id"]]
        gold_a = gold_to_extraction(str(row["paper_id"]), row["gold"])
        gold_b = gold_to_extraction(str(other["paper_id"]), other["gold"])
        for name in FIELD_NAMES:
            a = gold_a.fields[name]
            b = gold_b.fields[name]
            compared += 1
            same_value = _norm(a.value) == _norm(b.value) and a.filled() == b.filled()
            if same_value:
                value_agree += 1
                field_value_agree[name].append(1)
            else:
                field_value_agree[name].append(0)
            if a.filled() and b.filled():
                both_filled += 1
                iou = _iou(a.start, a.end, b.start, b.end)
                iou_sum += iou
                if a.start == b.start and a.end == b.end:
                    span_agree += 1

    value_rate = value_agree / compared if compared else 0.0
    span_rate = span_agree / both_filled if both_filled else 0.0
    mean_iou = iou_sum / both_filled if both_filled else 0.0
    decision = (
        f"Value agreement is {value_rate:.3f} on {compared} field-pairs. "
        f"Exact-span agreement on jointly filled fields is {span_rate:.3f} "
        f"(mean IoU {mean_iou:.3f}). Extraction accuracy cannot honestly exceed "
        "this agreement on the same texts."
    )
    per_field = {
        name: (sum(vals) / len(vals) if vals else 0.0) for name, vals in field_value_agree.items()
    }
    out = {
        "n_papers": len(pass_a),
        "n_field_pairs": compared,
        "value_agreement": value_rate,
        "exact_span_agreement": span_rate,
        "mean_span_iou": mean_iou,
        "n_jointly_filled": both_filled,
        "decision": decision,
        "per_field_value_agreement": per_field,
        "accuracy_upper_bound": value_rate,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", out)
    rows = [[name, pct(per_field[name])] for name in FIELD_NAMES if per_field[name] < 1.0]
    if rows:
        disagree_table = md_table(["field", "value agreement"], rows)
    else:
        disagree_table = "_No field-level disagreement._"
    table = md_table(
        ["metric", "value"],
        [
            ["n papers", str(len(pass_a))],
            ["value agreement", pct(value_rate)],
            ["exact span agreement", pct(span_rate)],
            ["mean span IoU", pct(mean_iou)],
            ["accuracy upper bound", pct(value_rate)],
        ],
    )
    md = (
        "# annotator_agreement results\n\n"
        f"n = {len(pass_a)} papers, two committed gold passes.\n\n"
        f"{decision}\n\n"
        f"{table}\n\n"
        "Fields with any disagreement:\n\n"
        f"{disagree_table}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
