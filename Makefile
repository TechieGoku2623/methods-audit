export PATH := $(HOME)/.local/bin:$(PATH)
UV ?= uv

.PHONY: demo-shots setup lint test research eval demo record

setup:
	$(UV) sync --extra dev

lint:
	$(UV) run ruff check src tests research scripts
	$(UV) run ruff format --check src tests research scripts
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
	$(UV) run methods-audit demo

demo-shots:
	$(UV) run --with pyyaml python demo/verify_shots.py

record:
	bash demo/record.sh
	bash demo/render.sh
