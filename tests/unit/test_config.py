from __future__ import annotations

import os

from methods_audit.cli import repo_root
from methods_audit.config import get_settings
from methods_audit.fields import SCHEMA
from methods_audit.logging import configure_logging


def test_settings_point_at_committed_sample_dir() -> None:
    settings = get_settings()
    assert (settings.sample_dir / "complete.xml").is_file()
    assert (settings.research_dir / "run_all.py").is_file()
    assert repo_root() == settings.repo_root


def test_schema_size() -> None:
    assert 25 <= len(SCHEMA) <= 40


def test_configure_logging_does_not_raise() -> None:
    configure_logging()
    os.environ["METHODS_AUDIT_ENV"] = "prod"
    try:
        configure_logging()
    finally:
        os.environ.pop("METHODS_AUDIT_ENV", None)
