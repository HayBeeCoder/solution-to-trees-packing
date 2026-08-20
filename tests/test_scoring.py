from decimal import Decimal

from tree_packing.geometry import create_tree_polygon
from tree_packing.scoring import bounding_box_side, configuration_score


def test_single_tree_side_is_one() -> None:
    side = bounding_box_side([create_tree_polygon(0, 0, 0)])
    assert abs(side - Decimal("1.0")) < Decimal("1e-9")


def test_single_tree_score_is_one() -> None:
    side = bounding_box_side([create_tree_polygon(0, 0, 0)])
    assert abs(configuration_score(side, 1) - Decimal("1.0")) < Decimal("1e-9")


def test_empty_returns_zero() -> None:
    assert bounding_box_side([]) == Decimal("0")


def test_score_normalizes_by_n() -> None:
    assert configuration_score(Decimal("2.0"), 4) == Decimal("1.0")
