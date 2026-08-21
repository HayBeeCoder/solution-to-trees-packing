"""Minimum pairwise clearance reporting."""

from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import Decimal

from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from tree_packing import config


def _to_problem_units(value: float) -> Decimal:
    return Decimal(str(value)) / config.SCALE_FACTOR


def _signed_clearance(a: BaseGeometry, b: BaseGeometry) -> Decimal:
    if a.intersects(b) and not a.touches(b):
        overlap_area = Decimal(str(a.intersection(b).area))
        return -(overlap_area / (config.SCALE_FACTOR * config.SCALE_FACTOR))
    return _to_problem_units(a.distance(b))


def min_pairwise_clearance(polygons: Sequence[BaseGeometry]) -> Decimal:
    """Return the minimum signed separation over all candidate pairs."""
    if len(polygons) <= 1:
        return Decimal("Infinity")

    tree = STRtree(list(polygons))
    minx = min(poly.bounds[0] for poly in polygons)
    miny = min(poly.bounds[1] for poly in polygons)
    maxx = max(poly.bounds[2] for poly in polygons)
    maxy = max(poly.bounds[3] for poly in polygons)
    search_radius = math.hypot(maxx - minx, maxy - miny)

    minimum = Decimal("Infinity")
    for i, poly in enumerate(polygons):
        query_geometry = box(
            poly.bounds[0] - search_radius,
            poly.bounds[1] - search_radius,
            poly.bounds[2] + search_radius,
            poly.bounds[3] + search_radius,
        )
        for j in tree.query(query_geometry):
            if j <= i:
                continue
            clearance = _signed_clearance(poly, polygons[j])
            if clearance < minimum:
                minimum = clearance
    return minimum
