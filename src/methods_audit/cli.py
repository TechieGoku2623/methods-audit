"""CLI: span-grounded extract, completeness score, consistency checks."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from methods_audit import SAFETY_DISCLAIMER, __version__
from methods_audit.config import get_settings
from methods_audit.fields import FIELD_INDEX, FIELD_NAMES
from methods_audit.logging import configure_logging
from methods_audit.pipeline import audit_text, load_reference_tables
from methods_audit.resolve import resolve_paper
from methods_audit.schemas import CompletenessScore, ConsistencyCheck, Extraction, SamplePaper

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=100)


def load_samples() -> list[SamplePaper]:
    path = get_settings().sample_dir / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [SamplePaper.model_validate(item) for item in raw["samples"]]


def _print_disclaimer() -> None:
    console.print()
    console.print(SAFETY_DISCLAIMER)


def _audit_resolved(
    paper: Path | None, doi: str | None
) -> tuple[Path, Extraction, CompletenessScore, list[ConsistencyCheck]]:
    try:
        path, paper_id = resolve_paper(paper=paper, doi=doi)
    except (ValueError, KeyError, FileNotFoundError) as exc:
        console.print(str(exc))
        raise typer.Exit(code=2) from exc
    text = path.read_text(encoding="utf-8")
    cache, genes, mis = load_reference_tables()
    extraction, score, checks = audit_text(
        text, paper_id, cache=cache, gene_sequences=genes, misidentified=mis
    )
    return path, extraction, score, checks


def _print_extraction(path: Path, extraction: Extraction) -> None:
    console.print(f"[bold]{extraction.paper_id}[/bold]  {path}")
    console.print("every field (unfilled = missing; nothing is inferred):\n")
    for name in FIELD_NAMES:
        item = extraction.fields[name]
        if item.filled():
            span = (
                f"{item.start}-{item.end}"
                if item.start is not None and item.end is not None
                else "—"
            )
            console.print(
                f"  {name:28}  {item.status:7}  {item.value}  "
                f"source={item.source}  span={span}  quote={item.quote!r}"
            )
        else:
            console.print(f"  {name:28}  missing")


def _list_or_none(names: list[str]) -> str:
    return ", ".join(names) if names else "(none)"


def _print_score(path: Path, score: CompletenessScore) -> None:
    console.print(f"[bold]{score.paper_id}[/bold]  {path}")
    console.print(
        f"completeness:  {score.completeness:.3f}  "
        f"({score.n_filled}/{score.n_applicable} applicable fields filled)"
    )
    console.print(score.rationale)
    console.print()
    console.print("missing by need (unfilled = missing; optional not in the denominator):")
    console.print(f"  required:     {_list_or_none(score.missing_required)}")
    console.print(f"  conditional:  {_list_or_none(score.missing_conditional)}")
    console.print(f"  optional:     {_list_or_none(score.missing_optional)}")
    console.print()
    console.print("applicable fields:")
    for name in score.applicable_fields:
        spec = FIELD_INDEX[name]
        state = "filled" if name not in score.missing_fields else "missing"
        console.print(f"  {name:28}  {state:7}  need={spec.need}")


def _print_check(check: ConsistencyCheck) -> None:
    console.print(f"[bold]{check.name}[/bold]  {check.status.upper()}")
    console.print(f"  detail:     {check.detail}")
    if check.left_field:
        span = f"{check.left_span[0]}-{check.left_span[1]}" if check.left_span else "—"
        console.print(f"  {check.left_field} span:  quote={check.left_quote!r}  span={span}")
    if check.right_field:
        span = f"{check.right_span[0]}-{check.right_span[1]}" if check.right_span else "—"
        console.print(f"  {check.right_field} span:  quote={check.right_quote!r}  span={span}")
    if check.alignment:
        console.print(f"  alignment:  {check.alignment}")
    if check.identity_record:
        rec = check.identity_record
        console.print("  Cellosaurus / ICLAC identity record:")
        console.print(f"    reported_as:  {rec.get('reported_as', '?')}")
        console.print(f"    actually:     {rec.get('actually', '?')}")
        console.print(f"    source:       {rec.get('source', '?')}")


@app.callback()
def _main() -> None:
    configure_logging()


@app.command("version")
def version() -> None:
    """Print the package version."""

    console.print(f"methods-audit {__version__}")


@app.command("demo-plan")
def demo_plan(
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
) -> None:
    """Print the designed sample methods sections and the path each exercises."""

    samples = load_samples()
    console.print("[bold]methods-audit designed sample methods sections[/bold]\n")
    for sample in samples:
        console.print(f"[bold]{sample.sample_id}[/bold]  {sample.filename}")
        console.print(f"  path:     {sample.path_exercised}")
        console.print(f"  expected: {sample.expected_behavior}\n")
    _print_disclaimer()
    if dry_run:
        console.print(
            "\nDry run only. Run `methods-audit demo` or `make demo` for the "
            "full extract/score/check walkthrough on the designed samples."
        )
    console.print(f"Sample manifest: {get_settings().sample_dir / 'manifest.json'}")


@app.command("sample-path")
def sample_path() -> None:
    """Print the committed sample directory path."""

    console.print(str(get_settings().sample_dir.resolve()))


@app.command("extract")
def extract_cmd(
    paper: Path | None = typer.Option(None, "--paper", help="Path to PMC-OA-style XML"),
    doi: str | None = typer.Option(None, "--doi", help="Committed DOI for one of the five samples"),
    summary: bool = typer.Option(False, "--summary", help="Filled fields only"),
) -> None:
    """Print every schema field. Missing stays missing. No inference."""

    path, extraction, _score, _checks = _audit_resolved(paper, doi)
    if summary:
        console.print(f"[bold]{extraction.paper_id}[/bold]  {path}")
        shown = 0
        for name in FIELD_NAMES:
            item = extraction.fields[name]
            if not item.filled():
                continue
            span = (
                f"{item.start}-{item.end}"
                if item.start is not None and item.end is not None
                else "—"
            )
            quote = (item.quote or "")[:40]
            console.print(
                f"  {name:24}  {item.value}  source={item.source}  span={span}  quote={quote!r}"
            )
            shown += 1
            if shown >= 6:
                break
        missing = sum(1 for name in FIELD_NAMES if not extraction.fields[name].filled())
        console.print(f"missing stays missing: {missing} unfilled fields")
    else:
        _print_extraction(path, extraction)
    _print_disclaimer()


@app.command("score")
def score_cmd(
    paper: Path | None = typer.Option(None, "--paper", help="Path to PMC-OA-style XML"),
    doi: str | None = typer.Option(None, "--doi", help="Committed DOI for one of the five samples"),
    summary: bool = typer.Option(False, "--summary", help="Completeness and missing required only"),
) -> None:
    """Completeness plus missing fields by required / conditional / optional."""

    path, _extraction, score, _checks = _audit_resolved(paper, doi)
    if summary:
        shown_path = path.name if path.is_absolute() else path
        console.print(f"[bold]{score.paper_id}[/bold]  {shown_path}")
        console.print(
            f"completeness:  {score.completeness:.3f}  "
            f"({score.n_filled}/{score.n_applicable} applicable fields filled)"
        )
        console.print(f"required missing:  {_list_or_none(score.missing_required)}")
        console.print("Completeness is a claim about the text, not a quality judgment.")
    else:
        _print_score(path, score)
    _print_disclaimer()


@app.command("check")
def check_cmd(
    paper: Path | None = typer.Option(None, "--paper", help="Path to PMC-OA-style XML"),
    doi: str | None = typer.Option(None, "--doi", help="Committed DOI for one of the five samples"),
) -> None:
    """Guide-vs-gene and cell-line identity. Completeness is not the finding."""

    path, extraction, score, checks = _audit_resolved(paper, doi)
    console.print(f"[bold]{extraction.paper_id}[/bold]  {path}")
    console.print(
        f"completeness: {score.completeness:.3f} "
        f"(presence only; not a quality or misconduct score)\n"
    )
    for check in checks:
        _print_check(check)
        console.print()
    _print_disclaimer()


@app.command("eval")
def eval_cmd(
    summary: bool = typer.Option(True, "--summary/--full"),
) -> None:
    """Print per-field F1 against hand annotation."""

    path = get_settings().repo_root / "docs" / "EVALUATION.md"
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Evaluation"):
            continue
        console.print(line[:100])
        if line.strip():
            n += 1
        if n >= 14:
            break
    _print_disclaimer()


@app.command("demo")
def demo_cmd() -> None:
    """Full walkthrough: extract with spans, score missing guide, run checks."""

    sample = get_settings().sample_dir
    console.print("[bold]methods-audit walkthrough[/bold]")
    console.print("Designed snippets only. Unfilled = missing.\n")

    console.print("[bold]Step 1 — extract complete.xml (every field + span)[/bold]")
    path, extraction, _score, _checks = _audit_resolved(sample / "complete.xml", None)
    _print_extraction(path, extraction)
    console.print()

    console.print("[bold]Step 2 — score no-guide.xml (missing by need)[/bold]")
    path, _extraction, score, _checks = _audit_resolved(sample / "no-guide.xml", None)
    _print_score(path, score)
    console.print()

    console.print("[bold]Step 3 — check guide-mismatch.xml (both spans + alignment)[/bold]")
    path, extraction, score, checks = _audit_resolved(sample / "guide-mismatch.xml", None)
    console.print(f"[bold]{extraction.paper_id}[/bold]  {path}")
    console.print(f"completeness: {score.completeness:.3f} (field is present; check still fails)\n")
    for check in checks:
        _print_check(check)
        console.print()

    console.print("[bold]Step 4 — check bad-cell-line.xml (Cellosaurus identity)[/bold]")
    path, extraction, score, checks = _audit_resolved(sample / "bad-cell-line.xml", None)
    console.print(f"[bold]{extraction.paper_id}[/bold]  {path}")
    console.print(f"completeness: {score.completeness:.3f} (identity is the finding)\n")
    for check in checks:
        _print_check(check)
        console.print()
    _print_disclaimer()


def repo_root() -> Path:
    return get_settings().repo_root


if __name__ == "__main__":
    app()
