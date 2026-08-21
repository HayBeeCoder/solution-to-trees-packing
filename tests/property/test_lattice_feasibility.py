"""H3.1 — feasibility of a double lattice is decided on the fundamental cell.

The direct guard against the sec 8.1 failure: an internally-feasible lattice
must also pass the *official* reference/evaluator.py on a materialised patch,
for every basis tested, including strongly sheared ones. Internal feasibility
uses geometry.neighbours (Gauss-reduced geometric distance), never an index
window over the lattice indices — that distinction is the whole point.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

from tree_packing.geometry.lattice import LatticeBasis, is_lattice_feasible, materialise_patch

REFERENCE_ROOT = Path(__file__).parents[2] / "reference"
if str(REFERENCE_ROOT) not in sys.path:
    sys.path.insert(0, str(REFERENCE_ROOT))

from evaluator import check_overlap as reference_check_overlap  # noqa: E402
from evaluator import create_tree_polygon as reference_create_tree_polygon  # noqa: E402


def _random_basis(rng: random.Random) -> LatticeBasis:
    p = rng.uniform(0.6, 1.4)
    q = rng.uniform(-0.9, 0.9)  # shear: allowed to be strongly non-orthogonal
    h = rng.uniform(0.6, 1.4)
    u = rng.uniform(-p, p)
    v = rng.uniform(-h, h)
    return LatticeBasis(p=p, q=q, h=h, u=u, v=v)


@pytest.mark.parametrize("seed", range(30))
def test_feasible_bases_pass_the_reference_evaluator(seed: int) -> None:
    """Every basis this audit calls feasible must also be evaluator-clean."""
    rng = random.Random(seed)
    basis = _random_basis(rng)

    if not is_lattice_feasible(basis):
        pytest.skip("basis rejected internally; not a claim under test")

    placements = materialise_patch(basis, extent=7)
    reference_polygons = [reference_create_tree_polygon(x, y, deg) for x, y, deg in placements]
    overlap_found, overlapping_pairs = reference_check_overlap(reference_polygons)
    assert not overlap_found, (
        f"basis {basis} was internally feasible but the reference evaluator "
        f"found overlaps on the materialised 7x7 patch: {overlapping_pairs[:5]}"
    )


def test_a_known_infeasible_basis_is_rejected() -> None:
    """A basis with p smaller than the tree's own footprint must be rejected."""
    basis = LatticeBasis(p=0.05, q=0.0, h=0.05, u=0.0, v=0.0)
    assert not is_lattice_feasible(basis)


def test_strongly_sheared_feasible_basis_still_passes() -> None:
    """Explicit strongly-sheared case, not left to chance in the random sweep."""
    basis = LatticeBasis(p=1.0, q=0.85, h=0.9, u=0.5, v=0.45)
    if not is_lattice_feasible(basis):
        pytest.skip("this particular sheared basis is infeasible; not the claim under test")
    placements = materialise_patch(basis, extent=7)
    reference_polygons = [reference_create_tree_polygon(x, y, deg) for x, y, deg in placements]
    overlap_found, overlapping_pairs = reference_check_overlap(reference_polygons)
    assert not overlap_found, overlapping_pairs[:5]
