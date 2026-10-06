"""Token cost and local latency per paper. No live API calls."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import tiktoken

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import load_json, md_table, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_set"
PAPERS = HERE.parent / "field_f1" / "probe_set" / "papers.json"
RESULTS = HERE / "results"
ENC = tiktoken.get_encoding("cl100k_base")


def _render(template: str, paper_id: str, xml: str) -> str:
    return template.replace("{{PAPER_ID}}", paper_id).replace("{{XML}}", xml)


def main() -> None:
    template = (PROBE / "prompt_template.txt").read_text(encoding="utf-8")
    pricing = json.loads((PROBE / "pricing.json").read_text(encoding="utf-8"))
    papers = load_json(PAPERS)["papers"]
    output_tokens = int(pricing["assumed_output_tokens"])

    t0 = time.perf_counter()
    prompts = [_render(template, str(row["paper_id"]), str(row["xml"])) for row in papers]
    token_counts = [len(ENC.encode(prompt)) for prompt in prompts]
    local_s = time.perf_counter() - t0

    n = len(prompts)
    mean_in = sum(token_counts) / n
    models_out: list[dict[str, Any]] = []
    rows: list[list[str]] = []
    for model in pricing["models"]:
        in_price = float(model["input_usd_per_mtok"])
        out_price = float(model["output_usd_per_mtok"])
        usd = mean_in / 1_000_000 * in_price + output_tokens / 1_000_000 * out_price
        models_out.append(
            {
                "id": model["id"],
                "input_usd_per_mtok": in_price,
                "output_usd_per_mtok": out_price,
                "mean_input_tokens_per_paper": mean_in,
                "usd_per_paper": usd,
                "usd_per_1000_papers": usd * 1000,
            }
        )
        rows.append(
            [
                str(model["id"]),
                f"{mean_in:.1f}",
                f"{usd:.6f}",
                f"{usd * 1000:.2f}",
            ]
        )

    cheapest = min(models_out, key=lambda row: float(row["usd_per_paper"]))
    payload = {
        "n_papers": n,
        "tokenizer": "tiktoken cl100k_base",
        "assumed_output_tokens_per_paper": output_tokens,
        "local_render_and_tokenize_seconds": local_s,
        "local_ms_per_paper": (local_s / n) * 1000,
        "api_round_trip_latency": "unmeasured",
        "api_round_trip_latency_measurement": (
            "A live call of the same prompts to each provider, recording "
            "p50/p95 RTT. Not run because this harness must work without keys."
        ),
        "decision": (
            f"Default extraction model: {cheapest['id']} "
            f"(${cheapest['usd_per_paper']:.6f}/paper). "
            "Escalate to a larger tier only when the cache miss fails "
            "span-grounded validation."
        ),
        "models": models_out,
        "per_paper_input_tokens": token_counts,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(
        ["model", "mean input tok/paper", "USD/paper", "USD/1000 papers"],
        rows,
    )
    md = (
        "# cost_per_paper results\n\n"
        f"n papers = {n}. Local render+tokenize = {local_s * 1000:.2f} ms total. "
        "API RTT = unmeasured.\n\n"
        f"{payload['decision']}\n\n"
        f"{table}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
