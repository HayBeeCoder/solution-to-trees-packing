"""Tests for the local regression-ratchet hook."""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_pre_push_hook_runs_the_verification_target() -> None:
    """The pre-push stage must block pushes when the full verification fails."""
    configuration = (REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "entry: make verify" in configuration
    assert "stages: [pre-push]" in configuration
