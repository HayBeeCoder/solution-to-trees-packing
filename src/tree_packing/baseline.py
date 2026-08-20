"""Naive grid baseline (port of ``simple_algorithm.py``). No optimization."""

from __future__ import annotations

import math

from tree_packing import config

Placement = tuple[float, float, float]  # (x, y, deg)


def grid_positions(n: int, spacing: float = config.GRID_SPACING) -> list[Placement]:
    """Place ``n`` trees on a centred square-ish grid with zero rotation."""
    if n <= 0:
        return []

    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    placements: list[Placement] = []
    for row in range(rows):
        for col in range(cols):
            if len(placements) >= n:
                break
            x = (col - (cols - 1) / 2) * spacing
            y = (row - (rows - 1) / 2) * spacing
            placements.append((x, y, 0.0))
    return placements


def build_baseline() -> dict[int, list[Placement]]:
    """All 200 grid configurations keyed by tree count."""
    return {n: grid_positions(n) for n in range(config.MIN_TREES, config.MAX_TREES + 1)}
