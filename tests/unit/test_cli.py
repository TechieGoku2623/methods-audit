from __future__ import annotations

from typer.testing import CliRunner

from methods_audit.cli import app, load_samples

runner = CliRunner()


def test_demo_plan_lists_five_designed_paths() -> None:
    result = runner.invoke(app, ["demo-plan"])
    assert result.exit_code == 0, result.stdout
    assert "S1-complete" in result.stdout
    assert "complete.xml" in result.stdout
    assert "no-guide.xml" in result.stdout
    assert "guide-mismatch.xml" in result.stdout
    assert "bad-cell-line.xml" in result.stdout
    assert "indirect.xml" in result.stdout
    assert "Research tool only" in result.stdout
    assert "Dry run only" in result.stdout


def test_demo_plan_no_dry_run() -> None:
    result = runner.invoke(app, ["demo-plan", "--no-dry-run"])
    assert result.exit_code == 0
    assert "Dry run only" not in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "methods-audit" in result.stdout


def test_sample_path() -> None:
    result = runner.invoke(app, ["sample-path"])
    assert result.exit_code == 0
    assert "data/sample" in result.stdout


def test_five_designed_samples() -> None:
    samples = load_samples()
    assert len(samples) == 5
    assert samples[0].filename == "complete.xml"
