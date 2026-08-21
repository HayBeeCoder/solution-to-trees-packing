"""Overlap detection and submission-level validation (port of evaluator checks)."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from tree_packing import config


def find_overlapping_pairs(polygons: Sequence[BaseGeometry]) -> list[tuple[int, int]]:
    """Return index pairs ``(i, j)`` that intersect without merely touching."""
    if len(polygons) <= 1:
        return []

    index = STRtree(list(polygons))
    pairs: list[tuple[int, int]] = []
    for i, poly in enumerate(polygons):
        for j in index.query(poly):
            if j <= i:
                continue
            other = polygons[j]
            if poly.intersects(other) and not poly.touches(other):
                pairs.append((i, j))
    return pairs


def has_overlap(polygons: Sequence[BaseGeometry]) -> bool:
    return len(find_overlapping_pairs(polygons)) > 0


def validate_submission_frame(df: pd.DataFrame) -> list[str]:
    """Structural validation: completeness of ``(n, tree_idx)`` and coordinate bounds."""
    errors: list[str] = []

    expected = {(n, t) for n in range(config.MIN_TREES, config.MAX_TREES + 1) for t in range(n)}
    actual = set(zip(df["n"], df["tree_idx"], strict=True))

    if missing := expected - actual:
        errors.append(f"Missing {len(missing)} tree entries, e.g. {sorted(missing)[:5]}")
    if extra := actual - expected:
        errors.append(f"Unexpected {len(extra)} tree entries, e.g. {sorted(extra)[:5]}")

    out_of_bounds = df[
        (df["x"] < config.MIN_COORD)
        | (df["x"] > config.MAX_COORD)
        | (df["y"] < config.MIN_COORD)
        | (df["y"] > config.MAX_COORD)
    ]
    if len(out_of_bounds) > 0:
        errors.append(
            f"{len(out_of_bounds)} trees outside [{config.MIN_COORD}, {config.MAX_COORD}]"
        )

    return errors
