"""Canonical Christmas-tree polygon construction.

Faithful re-implementation of ``create_tree_polygon`` from the official evaluator.
This is the single source of truth for the tree shape; scoring and validation both
import ``create_tree_polygon`` from here.
"""

from __future__ import annotations

from decimal import Decimal

from shapely import affinity
from shapely.geometry import Polygon

from tree_packing import config

_HALF = Decimal("2")
_QUARTER = Decimal("4")

Number = Decimal | float | str


def _scaled(value: Decimal) -> float:
    """Lift an unscaled decimal coordinate into Shapely's working space."""
    return float(value * config.SCALE_FACTOR)


def tree_vertices() -> list[tuple[float, float]]:
    """The 15 tree vertices in scaled space, starting at the tip, going clockwise."""
    return [
        (_scaled(Decimal("0.0")), _scaled(config.TIP_Y)),  # tip
        (_scaled(config.TOP_WIDTH / _HALF), _scaled(config.TIER_1_Y)),  # R top outer
        (_scaled(config.TOP_WIDTH / _QUARTER), _scaled(config.TIER_1_Y)),  # R top inner
        (_scaled(config.MID_WIDTH / _HALF), _scaled(config.TIER_2_Y)),  # R mid outer
        (_scaled(config.MID_WIDTH / _QUARTER), _scaled(config.TIER_2_Y)),  # R mid inner
        (_scaled(config.BASE_WIDTH / _HALF), _scaled(config.BASE_Y)),  # R base
        (_scaled(config.TRUNK_WIDTH / _HALF), _scaled(config.BASE_Y)),  # R trunk top
        (_scaled(config.TRUNK_WIDTH / _HALF), _scaled(config.TRUNK_BOTTOM_Y)),  # R trunk bottom
        (
            _scaled(-(config.TRUNK_WIDTH / _HALF)),
            _scaled(config.TRUNK_BOTTOM_Y),
        ),  # L trunk bottom
        (_scaled(-(config.TRUNK_WIDTH / _HALF)), _scaled(config.BASE_Y)),  # L trunk top
        (_scaled(-(config.BASE_WIDTH / _HALF)), _scaled(config.BASE_Y)),  # L base
        (_scaled(-(config.MID_WIDTH / _QUARTER)), _scaled(config.TIER_2_Y)),  # L mid inner
        (_scaled(-(config.MID_WIDTH / _HALF)), _scaled(config.TIER_2_Y)),  # L mid outer
        (_scaled(-(config.TOP_WIDTH / _QUARTER)), _scaled(config.TIER_1_Y)),  # L top inner
        (_scaled(-(config.TOP_WIDTH / _HALF)), _scaled(config.TIER_1_Y)),  # L top outer
    ]


def create_tree_polygon(center_x: Number, center_y: Number, angle: Number) -> Polygon:
    """Return a tree polygon at ``(center_x, center_y)`` rotated by ``angle`` degrees.

    Rotation is applied about the origin first, then translation — matching the
    official evaluator exactly.
    """
    cx = Decimal(str(center_x))
    cy = Decimal(str(center_y))
    ang = Decimal(str(angle))

    polygon = Polygon(tree_vertices())
    rotated = affinity.rotate(polygon, float(ang), origin=(0, 0))
    return affinity.translate(
        rotated,
        xoff=float(cx * config.SCALE_FACTOR),
        yoff=float(cy * config.SCALE_FACTOR),
    )
