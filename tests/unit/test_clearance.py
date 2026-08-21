from decimal import Decimal

from tree_packing.baseline import grid_positions
from tree_packing.geometry import create_tree_polygon
from tree_packing.validation.clearance import min_pairwise_clearance


def test_grid_clearance_matches_spacing() -> None:
    polygons = [create_tree_polygon(x, y, deg) for x, y, deg in grid_positions(4)]
    clearance = min_pairwise_clearance(polygons)
    assert abs(clearance - Decimal("0.1")) < Decimal("1e-12")


def test_touching_trees_have_zero_clearance() -> None:
    polygons = [create_tree_polygon(0, 0, 0), create_tree_polygon(0.7, 0, 0)]
    assert min_pairwise_clearance(polygons) == Decimal("0")


def test_overlapping_trees_are_negative() -> None:
    polygons = [create_tree_polygon(0, 0, 0), create_tree_polygon(0, 0, 0)]
    assert min_pairwise_clearance(polygons) < Decimal("0")


def test_single_polygon_is_unbounded() -> None:
    assert min_pairwise_clearance([create_tree_polygon(0, 0, 0)]) == Decimal("Infinity")
