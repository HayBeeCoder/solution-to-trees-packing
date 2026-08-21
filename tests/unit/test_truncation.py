"""H3.3 — window truncation is a searchable sub-problem.

Every n in 21..200 must yield a valid selection of exactly n trees from the
infinite double lattice, with no overlaps. Uses the H3.2-confirmed lattice
(seed 4, density 0.725241) as the tiling to truncate.
"""

from __future__ import annotations

from tree_packing.geometry.core import create_tree_polygon
from tree_packing.geometry.lattice import LatticeBasis
from tree_packing.geometry.truncation import truncate_to_n
from tree_packing.validation.overlap import has_overlap

# The H3.2-confirmed feasible lattice (seed 4), reused here rather than
# re-running the search: H3.3 is about truncation, not re-discovering density.
_BASIS = LatticeBasis(
    p=0.8466998057329839,
    q=-0.2595569327159729,
    h=0.8000013958277571,
    u=-0.15564510572139056,
    v=-0.30308104064715025,
)


def test_every_n_in_range_yields_exactly_n_trees_with_no_overlaps() -> None:
    for n in range(21, 201):
        placements = truncate_to_n(_BASIS, n)
        assert len(placements) == n, f"n={n} produced {len(placements)} trees"

        polygons = [create_tree_polygon(x, y, deg) for x, y, deg in placements]
        assert not has_overlap(polygons), f"n={n} truncation has an overlap"


def test_truncation_is_deterministic() -> None:
    first = truncate_to_n(_BASIS, 50)
    second = truncate_to_n(_BASIS, 50)
    assert first == second
