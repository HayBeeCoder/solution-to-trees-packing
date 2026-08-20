"""Regression checks for the clean-checkout CI contract."""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_runs_gate_and_reference_baseline_check() -> None:
    """CI must exercise quality gates and the official evaluator separately."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for command in (
        "uv sync --locked",
        "uv run ruff format --check .",
        "uv run ruff check .",
        "uv run mypy src",
        "uv run pytest",
        "uv run tree-packing generate",
        "uv run python reference/evaluator.py",
    ):
        assert command in workflow
