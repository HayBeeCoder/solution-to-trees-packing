.PHONY: gate baseline solve gatekeep verify coverage

gate:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src
	uv run lint-imports
	uv run pytest

baseline:
	uv run tree-packing generate --output data/submissions/baseline.csv
	uv run tree-packing evaluate data/submissions/baseline.csv

solve:
	uv run tree-packing solve --output data/submissions/current.csv

gatekeep:
	uv run tree-packing gatekeep data/submissions/current.csv --against artifacts/best_scores.json

verify: gate solve gatekeep
	uv run python reference/evaluator.py data/submissions/current.csv --quiet

coverage:
	uv run pytest --cov=tree_packing --cov-report=term-missing
