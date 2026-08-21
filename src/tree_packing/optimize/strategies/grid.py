"""Tight rectangular grid strategy."""

from __future__ import annotations

import math

from tree_packing import config
from tree_packing.optimize.base import SolveContext, evaluate_layout
from tree_packing.optimize.types import Layout, Placement

_X_PITCH = 0.7 + float(config.CLEARANCE_EPS)
_Y_PITCH = 1.0 + float(config.CLEARANCE_EPS)


def _best_column_count(n: int) -> int:
    return min(
        range(1, n + 1),
        key=lambda columns: max(columns * _X_PITCH, math.ceil(n / columns) * _Y_PITCH),
    )


def tight_grid_positions(n: int) -> tuple[Placement, ...]:
    """Return a centred 0.7 x 1.0 grid for ``n`` trees."""
    if n <= 0:
        return ()

    cols = _best_column_count(n)
    rows = math.ceil(n / cols)

    placements: list[Placement] = []
    for row in range(rows):
        for col in range(cols):
            if len(placements) >= n:
                break
            x = (col - (cols - 1) / 2.0) * _X_PITCH
            y = (row - (rows - 1) / 2.0) * _Y_PITCH
            placements.append(Placement(x=x, y=y, deg=0.0))
    return tuple(placements)


class TightGridStrategy:
    """Deterministic tight rectangular grid."""

    name = "grid"

    def solve(self, n: int, ctx: SolveContext) -> Layout | None:
        layout = Layout(n=n, placements=tight_grid_positions(n))
        return evaluate_layout(layout)
