# Christmas Tree Packing baseline

This repository is a typed, tested port of the supplied Christmas Tree Packing
Challenge boilerplate. It intentionally contains only the deterministic grid
baseline; it does not implement an optimizer.

## Setup

Install [uv](https://docs.astral.sh/uv/) and use Python 3.12 or newer:

```bash
uv sync
uv run pre-commit install
```

Run the quality gates:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src
uv run pytest
```

Generate and evaluate the baseline:

```bash
uv run tree-packing generate --output data/submissions/baseline.csv
uv run tree-packing evaluate data/submissions/baseline.csv
uv run python reference/evaluator.py data/submissions/baseline.csv
```

The generated CSV contains 20,100 rows, covering every configuration from one
through 200 trees. The optional visualization command requires the extra:

```bash
uv sync --extra viz
uv run tree-packing visualize data/submissions/baseline.csv --n 10
```

The reference challenge files are retained in `reference/` for direct comparison.
See [DECISIONS.md](DECISIONS.md) for the implementation trade-offs and
[LAB_NOTEBOOK.md](LAB_NOTEBOOK.md) for the hypothesis-and-label execution record.
