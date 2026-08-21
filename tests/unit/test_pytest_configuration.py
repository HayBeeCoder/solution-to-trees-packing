"""Tests for fast, side-effect-free default test execution."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_default_pytest_options_do_not_enable_coverage() -> None:
    """Coverage reporting is opt-in so concurrent test runs do not share state."""
    configuration = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())
    addopts = configuration["tool"]["pytest"]["ini_options"]["addopts"]

    assert "--cov" not in addopts
