"""H3.3 — turn an infinite double lattice into a valid n-tree selection.

Selecting which n cells of an infinite tiling to occupy is discrete: this
enumerates candidate lattice points (both sublattices), orders them by
distance from a centre, and takes the closest n. Any subset of a feasible
lattice (H3.1) remains overlap-free -- removing trees cannot create new
intersections -- so validity is structural, not something this module has to
re-verify per call. What *is* left to this module is picking a selection
tight enough to be worth using; the milestone's fuller plan additionally
refines the choice with simulated annealing over swap moves once a
candidate window is found, which is not yet implemented here (see
LAB_NOTEBOOK.md H3.3).
"""

from __future__ import annotations

import math

from tree_packing.geometry.lattice import LatticeBasis


def _candidate_pool(basis: LatticeBasis, half_range: int) -> list[tuple[float, float, float]]:
    a, b = basis.vectors()
    candidates: list[tuple[float, float, float]] = []
    for i in range(-half_range, half_range + 1):
        for j in range(-half_range, half_range + 1):
            x = i * a[0] + j * b[0]
            y = i * a[1] + j * b[1]
            candidates.append((x, y, 0.0))
            candidates.append((x + basis.u, y + basis.v, 180.0))
    return candidates


def truncate_to_n(basis: LatticeBasis, n: int) -> list[tuple[float, float, float]]:
    """Return exactly ``n`` ``(x, y, deg)`` placements, closest-to-centre first.

    Grows the candidate pool (binary-search-like doubling, not a fixed
    guess) until it comfortably exceeds ``n``, then keeps the ``n`` closest
    to the origin by Chebyshev distance -- the natural metric for a square
    window, since a square's binding constraint is its widest axis, not
    Euclidean radius.
    """
    if n <= 0:
        return []

    half_range = max(2, math.ceil(math.sqrt(n / 2.0)))
    while True:
        candidates = _candidate_pool(basis, half_range)
        if len(candidates) >= n:
            break
        half_range += 2

    candidates.sort(key=lambda placement: max(abs(placement[0]), abs(placement[1])))
    return candidates[:n]
