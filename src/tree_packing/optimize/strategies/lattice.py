"""Deterministic M3 lattice strategy backed by the verified seed-4 basis."""

from __future__ import annotations

from tree_packing.geometry.lattice import LatticeBasis
from tree_packing.geometry.truncation import truncate_and_refine
from tree_packing.optimize.base import SolveContext
from tree_packing.optimize.types import Layout, Placement

LATTICE_MIN_TREES = 21

# This is the feasible, evaluator-checked basis recorded in
# artifacts/lattice_runs/seed-4.json.  Keeping the basis in code makes the
# default solve deterministic and avoids rerunning the expensive SA search.
VERIFIED_BASIS = LatticeBasis(
    p=0.8466998057329839,
    q=-0.2595569327159729,
    h=0.8000013958277571,
    u=-0.15564510572139056,
    v=-0.30308104064715025,
)


class LatticeStrategy:
    """Select a finite, refined subset of the verified double lattice."""

    name = "lattice"

    def solve(self, n: int, ctx: SolveContext) -> Layout | None:
        if n < LATTICE_MIN_TREES:
            return None

        placements = truncate_and_refine(VERIFIED_BASIS, n, seed=4)
        return Layout(
            n=n,
            placements=tuple(Placement(x=x, y=y, deg=deg) for x, y, deg in placements),
        )
