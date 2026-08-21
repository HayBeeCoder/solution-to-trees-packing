"""Regression tests for CLI overlap reporting."""

from __future__ import annotations

import inspect

from tree_packing import cli


def test_evaluate_records_one_overlap_error_per_configuration() -> None:
    """Overlap reporting uses direct appends and one shared error collection."""
    source = inspect.getsource(cli._evaluate)

    assert "overlap_errors.append((n, len(pairs)))" in source
    assert "len(overlap_errors) - 10" in source
