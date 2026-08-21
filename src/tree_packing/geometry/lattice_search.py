"""H3.2 — simulated annealing search for a dense, feasible double lattice.

Five continuous parameters (``LatticeBasis``), searched with
``scipy.optimize.dual_annealing``. The objective includes an explicit
clearance term so the optimum lands at ``config.CLEARANCE_EPS`` rather than
at exact contact (shared contract §7's warning: a prior search reached
density 0.7086 at an overlap area of 1.9e-9 -- mathematically touching,
practically invalid).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal

from scipy.optimize import dual_annealing

from tree_packing import config
from tree_packing.geometry.core import create_tree_polygon
from tree_packing.geometry.lattice import (
    LatticeBasis,
    is_lattice_feasible,
    lattice_points_near,
)
from tree_packing.geometry.neighbours import enumerate_neighbour_vectors
from tree_packing.validation.clearance import min_pairwise_clearance

_NEIGHBOUR_RADIUS = 1.6
_TREE_AREA_UNSCALED = create_tree_polygon(0.0, 0.0, 0.0).area / float(config.SCALE_FACTOR) ** 2

# Wide enough to contain the known-feasible ~0.6054 lattice mentioned in the
# milestone doc without assuming its exact parameters; tight enough that SA
# spends its budget in the plausible region rather than degenerate corners.
BOUNDS: tuple[tuple[float, float], ...] = (
    (0.35, 1.6),  # p
    (-0.9, 0.9),  # q
    (0.35, 1.6),  # h
    (-1.0, 1.0),  # u
    (-1.0, 1.0),  # v
)


@dataclass(frozen=True, slots=True)
class SearchResult:
    basis: LatticeBasis
    density: float
    min_clearance: Decimal
    seed: int
    wall_clock_s: float


def cell_density(basis: LatticeBasis) -> float:
    """``2 * tree_area / cell_area``; the cell holds one upright + one inverted tree."""
    cell_area = basis.p * basis.h
    if cell_area <= 0:
        return 0.0
    return float(2.0 * _TREE_AREA_UNSCALED / cell_area)


def min_signed_clearance(basis: LatticeBasis) -> Decimal:
    """Minimum clearance across all neighbour pairs, in unscaled problem units.

    Negative when polygons actually overlap. Reuses the same three neighbour
    families as ``is_lattice_feasible``, via the same scale-correct
    ``validation.clearance.min_pairwise_clearance`` used everywhere else in
    the repo, rather than comparing shapely's scaled-coordinate distances
    directly (that mismatch was the bug caught and fixed here -- see
    LAB_NOTEBOOK.md).
    """
    if basis.p <= 0 or basis.h <= 0:
        return Decimal("-1")

    a, b = basis.vectors()
    same_sublattice_vectors = enumerate_neighbour_vectors(a, b, radius=_NEIGHBOUR_RADIUS)
    origin_upright = create_tree_polygon(0.0, 0.0, 0.0)
    origin_inverted = create_tree_polygon(basis.u, basis.v, 180.0)

    worst = Decimal("Infinity")
    for dx, dy in same_sublattice_vectors:
        worst = min(
            worst, min_pairwise_clearance([origin_upright, create_tree_polygon(dx, dy, 0.0)])
        )
        worst = min(
            worst,
            min_pairwise_clearance(
                [origin_inverted, create_tree_polygon(basis.u + dx, basis.v + dy, 180.0)]
            ),
        )
    for dx, dy in lattice_points_near(a, b, target=(-basis.u, -basis.v), radius=_NEIGHBOUR_RADIUS):
        candidate = create_tree_polygon(basis.u + dx, basis.v + dy, 180.0)
        worst = min(worst, min_pairwise_clearance([origin_upright, candidate]))

    return worst if worst != Decimal("Infinity") else Decimal(str(_NEIGHBOUR_RADIUS))


def _objective(params: tuple[float, float, float, float, float]) -> float:
    basis = LatticeBasis(*params)
    clearance = min_signed_clearance(basis)
    gap = config.CLEARANCE_EPS - clearance
    if gap > 0:
        # Hard barrier: every infeasible candidate must score worse than every
        # feasible one (density is bounded in (0, 1)), with a linear term so
        # the search still has a gradient back toward feasibility rather than
        # a flat plateau. A soft-weighted penalty (an earlier version used
        # -density + 50 * gap) was not steep enough: dual_annealing reported
        # density 0.8663 at a clearance of -0.00184 (an actual overlap, not a
        # real improvement) -- exactly the sec 7 anomaly this milestone warns
        # about. See LAB_NOTEBOOK.md for the materialised, evaluator-checked
        # confirmation that this was a real optimiser exploit, not real gain.
        return 10.0 + float(gap) * 1000.0
    return -cell_density(basis)


def run_seed(seed: int) -> SearchResult:
    started = time.perf_counter()
    result = dual_annealing(
        _objective,
        bounds=BOUNDS,
        seed=seed,
        maxiter=400,
    )
    elapsed = time.perf_counter() - started
    basis = LatticeBasis(*result.x)
    return SearchResult(
        basis=basis,
        density=cell_density(basis),
        min_clearance=min_signed_clearance(basis),
        seed=seed,
        wall_clock_s=elapsed,
    )


def run_seeds(seeds: tuple[int, ...] = (0, 1, 2, 3, 4)) -> list[SearchResult]:
    return [run_seed(seed) for seed in seeds]


def best_of(results: list[SearchResult]) -> SearchResult:
    feasible = [r for r in results if is_lattice_feasible(r.basis)]
    pool = feasible or results
    return max(pool, key=lambda r: r.density)
