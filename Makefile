export PATH := $(HOME)/.local/bin:$(PATH)
UV ?= uv

.PHONY: setup lint test research eval demo record

setup:
	$(UV) sync --extra dev

lint:
	$(UV) run ruff check src tests research
	$(UV) run ruff format --check src tests research
	$(UV) run mypy

test:
	$(UV) run pytest

research:
	$(UV) run python research/phase0/run_all.py

eval:
	$(UV) run python research/phase0/field_f1/run.py
	$(UV) run python research/phase0/annotator_agreement/run.py
	$(UV) run python research/phase0/cost_per_paper/run.py
	$(UV) run python research/phase0/render_docs.py

demo:
	$(UV) run methods-audit demo-plan

record:
	@echo "Asciinema recordings are a Phase 3 deliverable (demo/*.cast)."
	@echo "Phase 0 has no extract CLI to record."
