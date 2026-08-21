.PHONY: gate baseline verify coverage

gate:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src
	uv run lint-imports
	uv run pytest

baseline:
	uv run tree-packing generate --output data/submissions/baseline.csv
	uv run tree-packing evaluate data/submissions/baseline.csv

verify: gate baseline
	uv run python reference/evaluator.py data/submissions/baseline.csv --quiet

coverage:
	uv run pytest --cov=tree_packing --cov-report=term-missing
