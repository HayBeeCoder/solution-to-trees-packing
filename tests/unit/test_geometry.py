from decimal import Decimal

import pytest

from tree_packing.config import SCALE_FACTOR
from tree_packing.geometry import create_tree_polygon, tree_vertices


def test_has_fifteen_vertices() -> None:
    assert len(tree_vertices()) == 15


def test_polygon_is_valid(origin_tree) -> None:
    assert origin_tree.is_valid


def test_unscaled_area(origin_tree) -> None:
    area = origin_tree.area / float(SCALE_FACTOR) ** 2
    assert area == pytest.approx(0.245625, rel=1e-9)


def test_unscaled_bounds(origin_tree) -> None:
    minx, miny, maxx, maxy = (Decimal(str(b)) / SCALE_FACTOR for b in origin_tree.bounds)
    assert (minx, miny, maxx, maxy) == (
        Decimal("-0.35"),
        Decimal("-0.2"),
        Decimal("0.35"),
        Decimal("0.8"),
    )


def test_translation_moves_centroid() -> None:
    a = create_tree_polygon(0, 0, 0)
    b = create_tree_polygon(5, 0, 0)
    shift = (b.centroid.x - a.centroid.x) / float(SCALE_FACTOR)
    assert shift == pytest.approx(5.0, rel=1e-9)


def test_vertical_symmetry(origin_tree) -> None:
    minx, _, maxx, _ = origin_tree.bounds
    assert (minx + maxx) == pytest.approx(0.0, abs=1.0)
