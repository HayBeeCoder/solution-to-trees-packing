"""H3.3 (completion) — swap-move refinement of window truncation.

truncate_to_n's nearest-candidate selection is a valid but crude starting
point (see LAB_NOTEBOOK.md H3.3/H3.4: measured loss well above the
milestone doc's own worked example). This tests the refinement step the
milestone actually calls for: "refine the choice of which trees with
simulated annealing over swap moves."
"""

from __future__ import annotations

from decimal import Decimal

from tree_packing.geometry.core import create_tree_polygon
from tree_packing.geometry.lattice import LatticeBasis
from tree_packing.geometry.truncation import refine_truncation, truncate_to_n
from tree_packing.scoring import bounding_box_side
from tree_packing.validation.overlap import has_overlap

# The H3.2-confirmed feasible lattice (seed 4).
_BASIS = LatticeBasis(
    p=0.8466998057329839,
    q=-0.2595569327159729,
    h=0.8000013958277571,
    u=-0.15564510572139056,
    v=-0.30308104064715025,
)


def _side(placements: list[tuple[float, float, float]]) -> Decimal:
    polygons = [create_tree_polygon(x, y, deg) for x, y, deg in placements]
    return bounding_box_side(polygons)


def test_refinement_never_makes_the_box_larger() -> None:
    for n in (30, 50, 75, 100, 150, 200):
        baseline = truncate_to_n(_BASIS, n)
        refined = refine_truncation(_BASIS, baseline, seed=0)
        assert len(refined) == n
        assert _side(refined) <= _side(baseline)


def test_refinement_keeps_the_selection_valid() -> None:
    baseline = truncate_to_n(_BASIS, 50)
    refined = refine_truncation(_BASIS, baseline, seed=0)
    assert len(refined) == len(baseline)
    assert len(set(refined)) == len(refined)  # no duplicate trees introduced
    polygons = [create_tree_polygon(x, y, deg) for x, y, deg in refined]
    assert not has_overlap(polygons)


def test_refinement_meaningfully_shrinks_a_lossy_configuration() -> None:
    """n=50 measured a 35% loss with the crude baseline (LAB_NOTEBOOK H3.4).

    Refinement should close a substantial part of that gap, not just match
    the baseline -- a no-op "refinement" would trivially pass the
    never-larger test above without actually doing anything.
    """
    baseline = truncate_to_n(_BASIS, 50)
    refined = refine_truncation(_BASIS, baseline, seed=0)
    baseline_side = _side(baseline)
    refined_side = _side(refined)
    assert refined_side < baseline_side * Decimal("0.97")
