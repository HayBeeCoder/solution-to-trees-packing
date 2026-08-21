"""Double-lattice parameterisation and internal feasibility (H3.1).

Five parameters describe the motif: ``a = (p, 0)``, ``b = (q, h)`` with
``p, h > 0`` (without loss of generality — any basis can be rotated so the
first vector is horizontal), plus the 180-degree-inverted partner offset
``(u, v)``. Feasibility is decided on the fundamental cell using geometric
distance over a Gauss-reduced basis (``geometry.neighbours``), never an index
window over lattice coordinates — an index window is exactly the sec 8.1
failure mode this milestone guards against, since a strongly sheared basis
can have geometrically close neighbours at large, non-adjacent indices.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

import numpy as np
import numpy.typing as npt
from shapely.geometry import Polygon

from tree_packing import config
from tree_packing.geometry.core import create_tree_polygon
from tree_packing.geometry.neighbours import enumerate_neighbour_vectors
from tree_packing.validation.clearance import min_pairwise_clearance

_NEIGHBOUR_RADIUS = 1.6
Matrix2D = npt.NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class LatticeBasis:
    """Five free parameters of a double lattice (upright + 180-degree partner)."""

    p: float
    q: float
    h: float
    u: float
    v: float

    def vectors(self) -> tuple[tuple[float, float], tuple[float, float]]:
        return (self.p, 0.0), (self.q, self.h)


def is_lattice_feasible(basis: LatticeBasis, clearance_eps: Decimal | None = None) -> bool:
    """Decide feasibility on the fundamental cell alone.

    Checks three neighbour families, each over Gauss-reduced geometric
    distance rather than raw lattice indices:
    upright-upright, inverted-inverted (both use the same basis vectors, so
    share one neighbour enumeration), and upright-inverted across the
    ``(u, v)`` offset.
    """
    if basis.p <= 0 or basis.h <= 0:
        return False

    eps = clearance_eps if clearance_eps is not None else config.CLEARANCE_EPS
    a, b = basis.vectors()
    same_sublattice_vectors = enumerate_neighbour_vectors(a, b, radius=_NEIGHBOUR_RADIUS)

    origin_upright = create_tree_polygon(0.0, 0.0, 0.0)
    origin_inverted = create_tree_polygon(basis.u, basis.v, 180.0)

    # Upright-upright and inverted-inverted: both live on the same basis, so
    # any collision within one motif copy of itself rules the basis out.
    for dx, dy in same_sublattice_vectors:
        neighbour_upright = create_tree_polygon(dx, dy, 0.0)
        if _collides(origin_upright, neighbour_upright, eps):
            return False
        neighbour_inverted = create_tree_polygon(basis.u + dx, basis.v + dy, 180.0)
        if _collides(origin_inverted, neighbour_inverted, eps):
            return False

    # Upright-inverted: the inverted sublattice is the upright one shifted by
    # (u, v). Its near neighbours to an upright tree at the origin are the
    # lattice points L (integer combinations of a, b) for which (u, v) + L is
    # short — i.e. lattice points near the target -(u, v), not near the
    # origin. This is a different search from the self-neighbour case above
    # and must not reuse the origin-centred enumeration: for a general
    # (u, v), the lattice vectors that land close to the origin once shifted
    # are not the same as the lattice vectors that are themselves short.
    for dx, dy in lattice_points_near(a, b, target=(-basis.u, -basis.v), radius=_NEIGHBOUR_RADIUS):
        candidate = create_tree_polygon(basis.u + dx, basis.v + dy, 180.0)
        if _collides(origin_upright, candidate, eps):
            return False

    return True


def lattice_points_near(
    a: tuple[float, float],
    b: tuple[float, float],
    target: tuple[float, float],
    radius: float,
) -> list[tuple[float, float]]:
    """Integer combinations ``n*a + m*b`` within ``radius`` of ``target``.

    Bounds the search using the same row-sum technique as
    ``geometry.neighbours``'s coefficient bound, but centred on an arbitrary
    target rather than the origin, so it also finds lattice points that are
    only close to the origin *after* being shifted by an offset such as
    ``(u, v)`` — the case the self-neighbour enumeration cannot cover.
    """
    matrix = cast(Matrix2D, np.column_stack([np.asarray(a, dtype=float), np.asarray(b, dtype=float)]))
    inverse = cast(Matrix2D, np.linalg.inv(matrix))
    target_vec = cast(Matrix2D, np.asarray(target, dtype=float))
    target_coeffs = inverse @ target_vec
    row_sums = np.sum(np.abs(inverse), axis=1)
    bound = math.ceil(radius * float(np.max(row_sums))) + 1

    points: list[tuple[float, float]] = []
    n_center, m_center = round(target_coeffs[0]), round(target_coeffs[1])
    for n in range(n_center - bound, n_center + bound + 1):
        for m in range(m_center - bound, m_center + bound + 1):
            x = n * a[0] + m * b[0]
            y = n * a[1] + m * b[1]
            if math.hypot(x - target[0], y - target[1]) < radius:
                points.append((x, y))
    return points


def _collides(first: Polygon, second: Polygon, eps: Decimal) -> bool:
    # min_pairwise_clearance already converts shapely's scaled-coordinate
    # distances (and overlap areas) back into unscaled problem units, so eps
    # is compared like-for-like against config.CLEARANCE_EPS. A prior version
    # of this function compared raw (scaled) shapely distances directly
    # against eps, which is off by config.SCALE_FACTOR (1e15) and made the
    # clearance margin silently inert -- caught and fixed while wiring up
    # H3.2's search objective, see LAB_NOTEBOOK.md.
    return min_pairwise_clearance([first, second]) < eps


def materialise_patch(basis: LatticeBasis, extent: int = 7) -> list[tuple[float, float, float]]:
    """Materialise a finite ``extent`` x ``extent`` patch of both sublattices.

    Returns ``(x, y, deg)`` placements, in unscaled problem units, suitable
    for passing straight into ``reference.evaluator.create_tree_polygon``.
    """
    a, b = basis.vectors()
    half = extent // 2
    placements: list[tuple[float, float, float]] = []
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            x = i * a[0] + j * b[0]
            y = i * a[1] + j * b[1]
            placements.append((x, y, 0.0))
            placements.append((x + basis.u, y + basis.v, 180.0))
    return placements
