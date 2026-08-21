"""H3.3 — turn an infinite double lattice into a valid n-tree selection.

Selecting which n cells of an infinite tiling to occupy is discrete: this
enumerates candidate lattice points (both sublattices), orders them by
distance from a centre, and takes the closest n. Any subset of a feasible
lattice (H3.1) remains overlap-free -- removing trees cannot create new
intersections, and swapping one lattice-point tree for another preserves
this too, since every pairwise combination in the *infinite* lattice is
already collision-free by construction -- so validity is structural
throughout this module, never re-verified per candidate.

``truncate_to_n`` alone is a crude starting point (nearest-by-Chebyshev-
distance), measured in LAB_NOTEBOOK.md H3.4 as leaving substantial boundary
loss on the table. ``refine_truncation`` is the milestone's other half:
"refine the choice of which trees with simulated annealing over swap
moves" -- discrete SA, since there is no continuous local minimiser over
which trees are included.
"""

from __future__ import annotations

import math
import random

from tree_packing import config
from tree_packing.geometry.core import create_tree_polygon
from tree_packing.geometry.lattice import LatticeBasis

# Axis-aligned half-extents of one tree at the origin, in *scaled* Shapely
# units, fixed for each of the two orientations used in the lattice (0 and
# 180 degrees). Precomputed once so the SA inner loop can compute a
# candidate's bounding contribution with pure arithmetic instead of
# constructing and rotating a Shapely polygon on every trial.
_BOUNDS_BY_DEGREE = {
    0.0: create_tree_polygon(0.0, 0.0, 0.0).bounds,
    180.0: create_tree_polygon(0.0, 0.0, 180.0).bounds,
}


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


def _quick_bounds(
    placements: list[tuple[float, float, float]],
) -> tuple[float, float, float, float]:
    """Aggregate bounding box in scaled units, via arithmetic, not Shapely.

    Equivalent to ``unary_union(polygons).bounds`` for the purpose of a
    bounding box (a set's bounding box is the componentwise min/max of its
    members' own bounds; union geometry itself is not needed), but avoids
    constructing and rotating a Shapely polygon per placement per trial --
    the SA loop below evaluates this on the order of thousands of times.
    """
    minx = miny = math.inf
    maxx = maxy = -math.inf
    for x, y, deg in placements:
        bx0, by0, bx1, by1 = _BOUNDS_BY_DEGREE[deg]
        scaled_x = x * float(config.SCALE_FACTOR)
        scaled_y = y * float(config.SCALE_FACTOR)
        minx = min(minx, bx0 + scaled_x)
        miny = min(miny, by0 + scaled_y)
        maxx = max(maxx, bx1 + scaled_x)
        maxy = max(maxy, by1 + scaled_y)
    return minx, miny, maxx, maxy


def _quick_side(placements: list[tuple[float, float, float]]) -> float:
    minx, miny, maxx, maxy = _quick_bounds(placements)
    scale = float(config.SCALE_FACTOR)
    return max((maxx - minx) / scale, (maxy - miny) / scale)


def refine_truncation(
    basis: LatticeBasis,
    placements: list[tuple[float, float, float]],
    *,
    seed: int = 0,
    iterations: int = 300,
    pool_margin: int = 6,
    tie_eps: float = 1e-9,
) -> list[tuple[float, float, float]]:
    """Simulated annealing over swap moves, minimising bounding side.

    A plain single-tree swap plateaus immediately on this lattice: because
    the tiling is periodic, whole rows of included trees commonly share the
    *exact* coordinate that defines the current bounding extreme (verified
    directly -- e.g. n=50 has five trees tied at the binding extreme on
    each side), so swapping out any one of them leaves the bound completely
    unchanged until every tied member is gone. Each move here therefore
    swaps an entire currently-tied boundary group at once -- still a "swap
    move" in the sense the milestone means (trees traded for other lattice
    candidates, not a continuous relaxation), just sized to the group the
    geometry actually presents rather than fixed at one tree.

    The best configuration seen at any point is returned, not necessarily
    the final one, since Metropolis acceptance can wander uphill late in
    the schedule.
    """
    n = len(placements)
    if n == 0:
        return []

    rng = random.Random(seed)
    half_range = max(2, math.ceil(math.sqrt(n / 2.0))) + pool_margin
    pool = _candidate_pool(basis, half_range)
    included = list(placements)
    included_set = set(included)
    excluded = [candidate for candidate in pool if candidate not in included_set]

    current_side = _quick_side(included)
    best_side = current_side
    best = list(included)

    initial_temperature = max(current_side * 0.05, 1e-6)
    for step in range(iterations):
        if not excluded or len(included) < 2:
            break
        temperature = initial_temperature * (1.0 - step / iterations)

        minx, miny, maxx, maxy = _quick_bounds(included)
        side = max(maxx - minx, maxy - miny)
        binding_extremes = []
        if maxx - minx >= side - tie_eps:
            binding_extremes += ["minx", "maxx"]
        if maxy - miny >= side - tie_eps:
            binding_extremes += ["miny", "maxy"]
        extreme = rng.choice(binding_extremes)

        group_indices = _tied_group_indices(included, extreme, minx, miny, maxx, maxy, tie_eps)
        if len(group_indices) >= len(excluded):
            continue

        # Greedy per-vacancy replacement, evaluated by actual resulting
        # bounding side rather than a single-axis proxy: sorting candidates
        # by "smallest contribution to this one extreme" alone picks
        # candidates that are extreme in the *opposite* direction on the
        # same axis (e.g. minimising a maxy contribution favours very
        # negative y, which promptly becomes the new miny record instead).
        # Only a handful of the nearest excluded candidates are realistic
        # replacements regardless, so the frontier is capped for cost, not
        # correctness.
        frontier = sorted(excluded, key=_chebyshev)[: max(40, 4 * len(group_indices))]
        outgoing = [included[i] for i in group_indices]
        chosen: list[tuple[float, float, float]] = []
        available = list(frontier)
        for i in group_indices:
            if not available:
                break
            best_candidate = min(
                available, key=lambda candidate: _side_if_swapped(included, i, candidate)
            )
            included[i] = best_candidate
            chosen.append(best_candidate)
            available.remove(best_candidate)

        candidate_side = _quick_side(included)
        delta = candidate_side - current_side
        accept = delta <= 0
        if not accept and temperature > 0:
            accept = rng.random() < math.exp(-delta / temperature)

        if accept:
            for candidate in chosen:
                excluded.remove(candidate)
            excluded.extend(outgoing)
            current_side = candidate_side
            if current_side < best_side - tie_eps:
                best_side = current_side
                best = list(included)
        else:
            for i, tree in zip(group_indices, outgoing, strict=True):
                included[i] = tree

    return best


def _chebyshev(placement: tuple[float, float, float]) -> float:
    return max(abs(placement[0]), abs(placement[1]))


def _side_if_swapped(
    included: list[tuple[float, float, float]], index: int, candidate: tuple[float, float, float]
) -> float:
    original = included[index]
    included[index] = candidate
    side = _quick_side(included)
    included[index] = original
    return side


def _tied_group_indices(
    included: list[tuple[float, float, float]],
    extreme: str,
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    tie_eps: float,
) -> list[int]:
    target = {"minx": minx, "maxx": maxx, "miny": miny, "maxy": maxy}[extreme]
    indices = []
    for i, placement in enumerate(included):
        value = _extreme_contribution(placement, extreme)
        if abs(value - target) < tie_eps:
            indices.append(i)
    return indices


def _extreme_contribution(placement: tuple[float, float, float], extreme: str) -> float:
    x, y, deg = placement
    bx0, by0, bx1, by1 = _BOUNDS_BY_DEGREE[deg]
    scale = float(config.SCALE_FACTOR)
    scaled_x, scaled_y = x * scale, y * scale
    return float(
        {
            "minx": bx0 + scaled_x,
            "maxx": bx1 + scaled_x,
            "miny": by0 + scaled_y,
            "maxy": by1 + scaled_y,
        }[extreme]
    )


def truncate_and_refine(
    basis: LatticeBasis, n: int, *, seed: int = 0
) -> list[tuple[float, float, float]]:
    """Convenience wrapper: crude nearest-candidate selection, then refined."""
    return refine_truncation(basis, truncate_to_n(basis, n), seed=seed)
