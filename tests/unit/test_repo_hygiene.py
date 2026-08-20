"""Repository hygiene regressions enforced through Git's own ignore engine."""

from __future__ import annotations

from pathlib import Path
from subprocess import run

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_no_tracked_file_is_ignored() -> None:
    """Tracked paths must never also match a repository ignore rule."""
    result = run(
        ["git", "ls-files", "-ci", "--exclude-standard"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=True,
        text=True,
    )

    assert result.stdout == "", f"Tracked files matched by ignore rules:\n{result.stdout}"
