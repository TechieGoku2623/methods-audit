"""Phase 0 CLI. Extraction, scoring, and APIs are Phase 2."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from methods_audit import SAFETY_DISCLAIMER, __version__
from methods_audit.config import get_settings
from methods_audit.logging import configure_logging
from methods_audit.schemas import SamplePaper

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=140)


def load_samples() -> list[SamplePaper]:
    path = get_settings().sample_dir / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [SamplePaper.model_validate(item) for item in raw["samples"]]


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
    console.print()
    console.print(SAFETY_DISCLAIMER)
    if dry_run:
        console.print(
            "\nDry run only. Extraction (`methods-audit extract`) is Phase 2; "
            "this command exists so `make demo` can show that the sample set "
            "is designed, not sampled from a live PMC dump."
        )
    console.print(f"Sample manifest: {get_settings().sample_dir / 'manifest.json'}")


@app.command("sample-path")
def sample_path() -> None:
    """Print the committed sample directory path."""

    console.print(str(get_settings().sample_dir.resolve()))


def repo_root() -> Path:
    return get_settings().repo_root
