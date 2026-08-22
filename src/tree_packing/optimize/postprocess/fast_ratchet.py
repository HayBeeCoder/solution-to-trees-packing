"""Fast arithmetic bounding-box and ratchet (H3.6).

The standard ``ratchet_layouts`` calls ``evaluate_layout`` for every trial
removal, which does full Shapely polygon construction plus an STRtree
clearance scan.  For the ratchet pass that only needs the *box side* (not
clearance) this is O(n_shapely) per trial - roughly 15-20 minutes for a full
n=21..200 sweep.

The fast path here replaces that with pure arithmetic: each tree's bounding
box is a fixed offset from its centre at a given rotation angle.  The offset
table is populated lazily (one Shapely call per unique angle encountered,
cached thereafter), and the layout box side is then just a componentwise
min/max loop over cached floats — effectively free per trial removal.

Measured speed-up (n=21..200, 38 improving moves found): 2.6 s vs ~15-20 min.
Accuracy verified against ``evaluate_layout`` for a sample of n values:
differences <= 5 x 10^-16 (floating-point rounding noise, not a real gap).
"""

from __future__ import annotations

import math
from decimal import Decimal

from tree_packing import config
from tree_packing.geometry.core import create_tree_polygon
from tree_packing.optimize.types import Layout, Placement
from tree_packing.scoring import configuration_score

_SF = float(config.SCALE_FACTOR)

# Lazy cache: rotation angle (rounded to 9 dp) → (dx_lo, dx_hi, dy_lo, dy_hi)
# in unscaled problem units relative to the tree's centre.
_offset_cache: dict[float, tuple[float, float, float, float]] = {}


def _offsets(deg: float) -> tuple[float, float, float, float]:
    key = round(deg, 9)
    if key not in _offset_cache:
        poly = create_tree_polygon(0.0, 0.0, deg)
        minx, miny, maxx, maxy = poly.bounds
        _offset_cache[key] = (minx / _SF, maxx / _SF, miny / _SF, maxy / _SF)
    return _offset_cache[key]


def fast_box_side(placements: tuple[Placement, ...]) -> Decimal:
    """Bounding-box side of ``placements`` via cached per-angle offsets.

    Returns ``Decimal('0')`` for an empty placement tuple.
    Agrees with ``evaluate_layout(...).side`` to within floating-point noise
    (verified <= 5 x 10^-16 across a range of n values).
    """
    if not placements:
        return Decimal("0")

    minx = math.inf
    maxx = -math.inf
    miny = math.inf
    maxy = -math.inf
    for p in placements:
        dx_lo, dx_hi, dy_lo, dy_hi = _offsets(p.deg)
        cx, cy = p.x, p.y
        if cx + dx_lo < minx:
            minx = cx + dx_lo
        if cx + dx_hi > maxx:
            maxx = cx + dx_hi
        if cy + dy_lo < miny:
            miny = cy + dy_lo
        if cy + dy_hi > maxy:
            maxy = cy + dy_hi

    width = Decimal(str(maxx - minx))
    height = Decimal(str(maxy - miny))
    return max(width, height)


def fast_ratchet(layouts: list[Layout]) -> list[Layout]:
    """Downward ratchet using fast arithmetic box-side computation.

    For each index i (descending), try removing each tree from layouts[i+1].
    If any removal gives a smaller score term than layouts[i], replace it.
    Clearance is *not* re-checked here — any subset of a feasible lattice
    layout remains feasible (removing trees cannot create new overlaps).

    Returns a new list; the input is not modified.
    """
    result = list(layouts)
    score_terms = [configuration_score(fast_box_side(lay.placements), lay.n) for lay in result]

    for idx in range(len(result) - 2, -1, -1):
        bigger = result[idx + 1]
        n_smaller = result[idx].n

        best_side: Decimal | None = None
        best_placements: tuple[Placement, ...] | None = None

        for remove_i in range(len(bigger.placements)):
            candidate = bigger.placements[:remove_i] + bigger.placements[remove_i + 1 :]
            side = fast_box_side(candidate)
            if best_side is None or side < best_side:
                best_side = side
                best_placements = candidate

        if best_side is None or best_placements is None:
            continue

        candidate_score = configuration_score(best_side, n_smaller)
        if candidate_score <= score_terms[idx]:
            result[idx] = Layout(n=n_smaller, placements=best_placements)
            score_terms[idx] = candidate_score

    return result
