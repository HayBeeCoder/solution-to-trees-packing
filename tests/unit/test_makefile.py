"""Tests for the documented Makefile interface."""

from __future__ import annotations

from pathlib import Path
from subprocess import run

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_makefile_exposes_the_documented_quality_targets() -> None:
    """Each runbook target must expand without relying on shell aliases."""
    for target in ("gate", "baseline", "verify", "coverage"):
        result = run(
            ["make", "--dry-run", target],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
