"""test(H3.6): fast arithmetic ratchet matches Shapely evaluate_layout."""

from __future__ import annotations

import pytest
from decimal import Decimal

from tree_packing.geometry.lattice import LatticeBasis
from tree_packing.geometry.truncation import truncate_to_n
from tree_packing.optimize.postprocess.fast_ratchet import fast_box_side
from tree_packing.optimize.base import evaluate_layout
from tree_packing.optimize.types import Layout, Placement

_BASIS = LatticeBasis(
    p=0.8466998057329839,
    q=-0.2595569327159729,
    h=0.8000013958277571,
    u=-0.15564510572139056,
    v=-0.30308104064715025,
)


def _make_layout(n: int) -> Layout:
    raw = truncate_to_n(_BASIS, n)
    return Layout(n=n, placements=tuple(Placement(x=x, y=y, deg=deg) for x, y, deg in raw))


@pytest.mark.parametrize("n", [21, 50, 100, 172, 200])
def test_fast_box_side_matches_shapely(n: int) -> None:
    """fast_box_side must agree with evaluate_layout to within 1e-9 (unscaled)."""
    layout = _make_layout(n)
    fast = fast_box_side(layout.placements)
    shapely = evaluate_layout(layout).side
    assert shapely is not None
    assert abs(fast - shapely) < Decimal("1e-9"), (
        f"n={n}: fast={fast} shapely={shapely} diff={abs(fast - shapely)}"
    )


def test_fast_box_side_empty() -> None:
    assert fast_box_side(()) == Decimal("0")
