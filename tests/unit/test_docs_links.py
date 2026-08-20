"""Regression checks for paths documented in tracked Markdown files."""

from __future__ import annotations

import re
from pathlib import Path
from subprocess import run

REPOSITORY_ROOT = Path(__file__).parents[2]
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
INLINE_PATH = re.compile(r"`([\w./-]+\.(?:md|py|csv|toml))`")
GENERATED_PREFIXES = ("artifacts/", "data/submissions/")
PROSPECTIVE_DOCUMENT_PREFIX = "sprints/"


def _tracked_markdown() -> list[Path]:
    result = run(
        ["git", "ls-files", "*.md"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    return [REPOSITORY_ROOT / path for path in result.stdout.splitlines()]


def _relative_targets(document: Path) -> list[Path]:
    text = document.read_text(encoding="utf-8")
    targets: list[Path] = []
    for target in MARKDOWN_LINK.findall(text):
        path = target.split("#", maxsplit=1)[0]
        if path and "://" not in path and not path.startswith("/"):
            targets.append(document.parent / path)
    for path in INLINE_PATH.findall(text):
        root_target = REPOSITORY_ROOT / path
        document_target = document.parent / path
        if "/" in path or root_target.exists():
            targets.append(root_target)
        elif document_target.exists():
            targets.append(document_target)
    return targets


def _is_tracked(path: Path) -> bool:
    relative_path = path.relative_to(REPOSITORY_ROOT).as_posix()
    result = run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def test_documented_relative_paths_exist() -> None:
    """Present-state docs link only to clean-clone files, not future milestones."""
    missing = sorted(
        relative_path
        for document in _tracked_markdown()
        if not document.relative_to(REPOSITORY_ROOT)
        .as_posix()
        .startswith(PROSPECTIVE_DOCUMENT_PREFIX)
        for target in _relative_targets(document)
        if (relative_path := target.relative_to(REPOSITORY_ROOT).as_posix())
        and not relative_path.startswith(GENERATED_PREFIXES)
        and (not target.exists() or not _is_tracked(target))
    )

    assert not missing, f"Documented paths do not exist: {missing}"


def test_readme_links_every_project_document() -> None:
    """README is a one-hop entry point for project documentation."""
    readme_targets = {
        target.relative_to(REPOSITORY_ROOT).as_posix()
        for target in _relative_targets(REPOSITORY_ROOT / "README.md")
    }
    project_documents = {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in _tracked_markdown()
        if path.parent != REPOSITORY_ROOT / "reference"
    }
    missing = sorted((project_documents - {"README.md"}) - readme_targets)

    assert not missing, f"README does not link project documents: {missing}"
