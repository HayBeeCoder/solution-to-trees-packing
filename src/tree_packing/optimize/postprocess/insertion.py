"""Upward insertion search inside the current bounding square."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import cast

from shapely.geometry.base import BaseGeometry

from tree_packing import config
from tree_packing.geometry import create_tree_polygon
from tree_packing.optimize.base import evaluate_layout
from tree_packing.optimize.types import Layout, Placement

_DEFAULT_ANGLES: tuple[float, ...] = (0.0, 15.0, 30.0, 45.0, 60.0, 75.0)


def _candidate_positions(side: Decimal, samples: int) -> Iterable[tuple[float, float]]:
    if samples <= 1:
        yield (0.0, 0.0)
        return

    span = float(side)
    start = -span / 2.0
    step = span / float(samples - 1)
    for iy in range(samples):
        y = start + step * iy
        for ix in range(samples):
            x = start + step * ix
            yield (x, y)


def _fits_in_square(polygon: BaseGeometry, side: Decimal) -> bool:
    half_side = float(side) * float(config.SCALE_FACTOR) / 2.0
    minx, miny, maxx, maxy = cast(tuple[float, float, float, float], polygon.bounds)
    return minx >= -half_side and miny >= -half_side and maxx <= half_side and maxy <= half_side


def _insert_one(layout: Layout, angles: tuple[float, ...], samples: int) -> Layout | None:
    evaluated = evaluate_layout(layout)
    if evaluated.side is None:
        return None

    existing_polygons = [
        create_tree_polygon(placement.x, placement.y, placement.deg)
        for placement in evaluated.placements
    ]
    for angle in angles:
        for x, y in _candidate_positions(evaluated.side, samples):
            candidate = Placement(x=x, y=y, deg=angle)
            candidate_polygon = create_tree_polygon(candidate.x, candidate.y, candidate.deg)
            if not _fits_in_square(candidate_polygon, evaluated.side):
                continue
            if any(
                candidate_polygon.intersects(other) and not candidate_polygon.touches(other)
                for other in existing_polygons
            ):
                continue

            updated = evaluate_layout(
                Layout(
                    n=evaluated.n + 1,
                    placements=(*evaluated.placements, candidate),
                )
            )
            if updated.side is not None and updated.side <= evaluated.side:
                return updated
    return None


def grow_layout(
    layout: Layout,
    *,
    max_insertions: int = 1,
    angles: tuple[float, ...] = _DEFAULT_ANGLES,
    samples: int = 7,
) -> tuple[Layout, ...]:
    """Repeatedly try to add one more tree without growing the square."""
    grown: list[Layout] = [evaluate_layout(layout)]
    current = grown[0]
    for _ in range(max_insertions):
        next_layout = _insert_one(current, angles=angles, samples=samples)
        if next_layout is None:
            break
        grown.append(next_layout)
        current = next_layout
    return tuple(grown)
