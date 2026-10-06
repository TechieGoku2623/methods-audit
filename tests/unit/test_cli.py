from __future__ import annotations

from typer.testing import CliRunner

from methods_audit.cli import app, load_samples
from methods_audit.resolve import load_doi_map, resolve_paper

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


def test_extract_complete_shows_fields_and_spans() -> None:
    result = runner.invoke(app, ["extract", "--paper", "data/sample/complete.xml"])
    assert result.exit_code == 0, result.stdout
    assert "target_gene" in result.stdout
    assert "TP53" in result.stdout
    assert "span=" in result.stdout
    assert "quote=" in result.stdout
    assert "missing" in result.stdout
    assert "donor_template_type" in result.stdout


def test_score_no_guide_lists_missing_by_need() -> None:
    result = runner.invoke(app, ["score", "--paper", "data/sample/no-guide.xml"])
    assert result.exit_code == 0, result.stdout
    assert "completeness:" in result.stdout
    assert "required:" in result.stdout
    assert "guide_sequence" in result.stdout
    assert "conditional:" in result.stdout
    assert "optional:" in result.stdout


def test_check_guide_mismatch_shows_spans_and_alignment() -> None:
    result = runner.invoke(app, ["check", "--paper", "data/sample/guide-mismatch.xml"])
    assert result.exit_code == 0, result.stdout
    assert "guide_targets_gene" in result.stdout
    assert "FAIL" in result.stdout
    assert "target_gene span:" in result.stdout
    assert "guide_sequence span:" in result.stdout
    assert "alignment:" in result.stdout
    assert "AATTCCCGTCGCTATCAAGG" in result.stdout


def test_check_bad_cell_line_shows_identity_record() -> None:
    result = runner.invoke(app, ["check", "--paper", "data/sample/bad-cell-line.xml"])
    assert result.exit_code == 0, result.stdout
    assert "cell_line_identity" in result.stdout
    assert "FAIL" in result.stdout
    assert "INT-407" in result.stdout
    assert "HeLa" in result.stdout
    assert "identity record" in result.stdout


def test_score_doi_resolves_five_samples_only() -> None:
    result = runner.invoke(app, ["score", "--doi", "10.0000/methods-audit.no-guide"])
    assert result.exit_code == 0, result.stdout
    assert "guide_sequence" in result.stdout
    bad = runner.invoke(app, ["score", "--doi", "10.1234/not-in-map"])
    assert bad.exit_code == 2
    assert "five-sample map" in bad.stdout


def test_extract_indirect_does_not_hallucinate() -> None:
    result = runner.invoke(app, ["extract", "--paper", "data/sample/indirect.xml"])
    assert result.exit_code == 0, result.stdout
    assert "TP53" not in result.stdout
    assert result.stdout.count("  missing") >= 20


def test_demo_walkthrough() -> None:
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0, result.stdout
    assert "complete.xml" in result.stdout
    assert "no-guide.xml" in result.stdout
    assert "guide-mismatch.xml" in result.stdout
    assert "bad-cell-line.xml" in result.stdout


def test_doi_map_has_five_keys() -> None:
    mapping = load_doi_map()
    assert len(mapping) == 5
    path, paper_id = resolve_paper(paper=None, doi="10.0000/methods-audit.complete")
    assert paper_id == "complete"
    assert path.name == "complete.xml"
