"""Per-field precision, recall, F1 vs gold, plus regex baseline and agreement ceiling."""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

from methods_audit.cache import load_cache
from methods_audit.config import get_settings
from methods_audit.extract import extract, regex_extract
from methods_audit.fields import FIELD_NAMES

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import gold_to_extraction, load_json, md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_set" / "papers.json"
AGREE_A = HERE.parent / "annotator_agreement" / "probe_set" / "pass_a.json"
AGREE_B = HERE.parent / "annotator_agreement" / "probe_set" / "pass_b.json"
RESULTS = HERE / "results"
MEDIAN_FLOOR = 0.70


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1


def _score_fields(
    papers: list[dict[str, object]],
    pred_fn: object,
) -> dict[str, dict[str, int]]:
    per_field = {name: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for name in FIELD_NAMES}
    for row in papers:
        gold = gold_to_extraction(str(row["paper_id"]), row["gold"])  # type: ignore[arg-type]
        pred = pred_fn(str(row["xml"]), str(row["paper_id"]))
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
    return per_field


def _agreement_ceiling() -> dict[str, float]:
    pass_a = load_json(AGREE_A)["papers"]
    pass_b = load_json(AGREE_B)["papers"]
    by_id_b = {row["paper_id"]: row for row in pass_b}
    field_agree: dict[str, list[int]] = {name: [] for name in FIELD_NAMES}
    for row in pass_a:
        other = by_id_b[row["paper_id"]]
        gold_a = gold_to_extraction(str(row["paper_id"]), row["gold"])
        gold_b = gold_to_extraction(str(other["paper_id"]), other["gold"])
        for name in FIELD_NAMES:
            a = gold_a.fields[name]
            b = gold_b.fields[name]
            same = _norm(a.value) == _norm(b.value) and a.filled() == b.filled()
            field_agree[name].append(1 if same else 0)
    return {name: (sum(vals) / len(vals) if vals else 0.0) for name, vals in field_agree.items()}


def main() -> None:
    payload = load_json(PROBE)
    papers = payload["papers"]
    cache = load_cache(get_settings().sample_dir / "llm_cache.json")

    def system_pred(xml: str, paper_id: str):
        return extract(xml, paper_id, cache=cache)

    system = _score_fields(papers, system_pred)
    regex = _score_fields(papers, regex_extract)
    ceiling = _agreement_ceiling()

    rows_md: list[list[str]] = []
    f1s: list[float] = []
    regex_f1s: list[float] = []
    codes_out: dict[str, object] = {}
    for name in FIELD_NAMES:
        stats = system[name]
        precision, recall, f1 = _prf(stats["tp"], stats["fp"], stats["fn"])
        r_prec, r_rec, r_f1 = _prf(regex[name]["tp"], regex[name]["fp"], regex[name]["fn"])
        support = stats["tp"] + stats["fn"]
        if support == 0:
            decision = "unmeasured (no gold positives)"
        else:
            f1s.append(f1)
            regex_f1s.append(r_f1)
            decision = "measured"
        codes_out[name] = {
            **stats,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "regex_precision": r_prec,
            "regex_recall": r_rec,
            "regex_f1": r_f1,
            "agreement_ceiling": ceiling[name],
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
                pct(r_f1),
                pct(ceiling[name]),
                decision,
            ]
        )

    median_f1 = statistics.median(f1s) if f1s else 0.0
    median_regex = statistics.median(regex_f1s) if regex_f1s else 0.0
    median_ceiling = statistics.median([ceiling[n] for n in FIELD_NAMES])
    defensible = median_f1 >= MEDIAN_FLOOR
    decision = (
        f"Median field F1 is {median_f1:.3f} (>= {MEDIAN_FLOOR:.2f}). "
        f"Regex-only baseline median F1 is {median_regex:.3f}. "
        f"Self-agreement ceiling (median per-field value agreement) is "
        f"{median_ceiling:.3f}. A completeness leaderboard on this extractor "
        "is defensible on the probe set."
        if defensible
        else (
            f"Median field F1 is {median_f1:.3f} (< {MEDIAN_FLOOR:.2f}). "
            "The completeness leaderboard is not defensible."
        )
    )
    out = {
        "n_papers": len(papers),
        "median_field_f1": median_f1,
        "median_regex_f1": median_regex,
        "median_agreement_ceiling": median_ceiling,
        "median_floor": MEDIAN_FLOOR,
        "n_fields_measured": len(f1s),
        "leaderboard_defensible": defensible,
        "decision": decision,
        "fields": codes_out,
        "gold_source": payload["disclaimer"],
        "note": (
            "System column is regex + committed cache. Cache keys are the five "
            "demo papers; on this 50-paper gold set a cache miss leaves the "
            "regex fill. Self-agreement is an accuracy ceiling, not a score."
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", out)
    table = md_table(
        [
            "field",
            "gold+",
            "TP",
            "FP",
            "FN",
            "precision",
            "recall",
            "F1",
            "regex F1",
            "agreement ceiling",
            "decision",
        ],
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
