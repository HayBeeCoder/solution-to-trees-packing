"""Strategy wrapper around the checked-in baseline grid."""

from __future__ import annotations

from tree_packing.baseline import build_baseline
from tree_packing.optimize.base import SolveContext, evaluate_layout
from tree_packing.optimize.types import Layout, Placement


class BaselineStrategy:
    """Re-expose the repository baseline as a strategy."""

    name = "baseline"

    def solve(self, n: int, ctx: SolveContext) -> Layout | None:
        baseline = build_baseline().get(n)
        if baseline is None:
            return None
        layout = Layout(
            n=n,
            placements=tuple(Placement(x=x, y=y, deg=deg) for x, y, deg in baseline),
        )
        return evaluate_layout(layout)
