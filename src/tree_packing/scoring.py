"""Bounding-box and score computation (port of the evaluator's scoring path)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, getcontext

from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from tree_packing import config

getcontext().prec = config.DECIMAL_PRECISION


def bounding_box_side(polygons: Sequence[BaseGeometry]) -> Decimal:
    """Side length of the smallest *square* enclosing all polygons (unscaled)."""
    if not polygons:
        return Decimal("0")

    minx, miny, maxx, maxy = unary_union(list(polygons)).bounds
    width = Decimal(str(maxx)) / config.SCALE_FACTOR - Decimal(str(minx)) / config.SCALE_FACTOR
    height = Decimal(str(maxy)) / config.SCALE_FACTOR - Decimal(str(miny)) / config.SCALE_FACTOR
    return max(width, height)


def configuration_score(side: Decimal, n: int) -> Decimal:
    """Normalized score s_n^2 / n for one configuration."""
    return (side * side) / Decimal(n)
