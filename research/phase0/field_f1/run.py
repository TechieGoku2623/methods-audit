"""Per-field precision, recall, F1 of the Phase 0 extractor on 50 papers."""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

from methods_audit.extract import extract
from methods_audit.fields import FIELD_NAMES

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import gold_to_extraction, load_json, md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_set" / "papers.json"
RESULTS = HERE / "results"
MEDIAN_FLOOR = 0.70


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1


def main() -> None:
    payload = load_json(PROBE)
    papers = payload["papers"]
    per_field = {name: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for name in FIELD_NAMES}

    for row in papers:
        gold = gold_to_extraction(str(row["paper_id"]), row["gold"])
        pred = extract(str(row["xml"]), str(row["paper_id"]))
        for name in FIELD_NAMES:
            g = gold.fields[name]
            p = pred.fields[name]
            g_on = g.filled()
            p_on = p.filled()
            if g_on and p_on and _norm(g.value) == _norm(p.value):
                per_field[name]["tp"] += 1
            elif p_on and not g_on:
                per_field[name]["fp"] += 1
            elif p_on and g_on and _norm(g.value) != _norm(p.value):
                per_field[name]["fp"] += 1
                per_field[name]["fn"] += 1
            elif (not p_on) and g_on:
                per_field[name]["fn"] += 1
            else:
                per_field[name]["tn"] += 1

    rows_md: list[list[str]] = []
    f1s: list[float] = []
    codes_out: dict[str, object] = {}
    for name in FIELD_NAMES:
        stats = per_field[name]
        precision, recall, f1 = _prf(stats["tp"], stats["fp"], stats["fn"])
        support = stats["tp"] + stats["fn"]
        if support == 0:
            decision = "unmeasured (no gold positives)"
        else:
            f1s.append(f1)
            decision = "measured"
        codes_out[name] = {
            **stats,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "gold_positive": support,
            "decision": decision,
        }
        rows_md.append(
            [
                name,
                str(support),
                str(stats["tp"]),
                str(stats["fp"]),
                str(stats["fn"]),
                pct(precision),
                pct(recall),
                pct(f1),
                decision,
            ]
        )

    median_f1 = statistics.median(f1s) if f1s else 0.0
    defensible = median_f1 >= MEDIAN_FLOOR
    decision = (
        f"Median field F1 is {median_f1:.3f} (>= {MEDIAN_FLOOR:.2f}). "
        "A completeness leaderboard on this extractor is defensible on the probe set."
        if defensible
        else (
            f"Median field F1 is {median_f1:.3f} (< {MEDIAN_FLOOR:.2f}). "
            "The completeness leaderboard is not defensible."
        )
    )
    out = {
        "n_papers": len(papers),
        "median_field_f1": median_f1,
        "median_floor": MEDIAN_FLOOR,
        "n_fields_measured": len(f1s),
        "leaderboard_defensible": defensible,
        "decision": decision,
        "fields": codes_out,
        "gold_source": payload["disclaimer"],
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", out)
    table = md_table(
        ["field", "gold+", "TP", "FP", "FN", "precision", "recall", "F1", "decision"],
        rows_md,
    )
    md = (
        "# field_f1 results\n\n"
        f"n = {len(papers)} committed methods snippets.\n\n"
        f"{decision}\n\n"
        f"{table}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
