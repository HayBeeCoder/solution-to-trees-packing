"""Global rotation search for one complete layout."""

from __future__ import annotations

import math
from decimal import Decimal

from tree_packing.optimize.base import measure_layout
from tree_packing.optimize.types import Layout, Placement

_PHI = (1.0 + math.sqrt(5.0)) / 2.0


def _rotate_point(x: float, y: float, angle_degrees: float) -> tuple[float, float]:
    angle = math.radians(angle_degrees)
    cos_theta = math.cos(angle)
    sin_theta = math.sin(angle)
    return (x * cos_theta - y * sin_theta, x * sin_theta + y * cos_theta)


def rotate_layout(layout: Layout, angle_degrees: float) -> Layout:
    """Rotate the whole layout around the origin."""
    placements = tuple(
        Placement(
            x=rx,
            y=ry,
            deg=float(placement.deg) + angle_degrees,
        )
        for placement in layout.placements
        for rx, ry in [_rotate_point(float(placement.x), float(placement.y), angle_degrees)]
    )
    return Layout(n=layout.n, placements=placements)


def _evaluated_rotation(layout: Layout, angle_degrees: float) -> Layout:
    return measure_layout(rotate_layout(layout, angle_degrees))


def best_rotation(layout: Layout, coarse_step: float = 5.0, refinements: int = 10) -> Layout:
    """Search ``[0°, 90°)`` for the smallest bounding square."""
    best = _evaluated_rotation(layout, 0.0)
    best_angle = 0.0
    tolerance = Decimal("1e-12")

    angle = coarse_step
    while angle < 90.0:
        candidate = _evaluated_rotation(layout, angle)
        if candidate.side is not None and best.side is not None and candidate.side < best.side:
            best = candidate
            best_angle = angle
        angle += coarse_step

    left = max(0.0, best_angle - coarse_step)
    right = min(90.0, best_angle + coarse_step)
    if right - left <= 1e-9:
        return best

    inv_phi = 1.0 / _PHI
    c = right - (right - left) * inv_phi
    d = left + (right - left) * inv_phi
    fc = _evaluated_rotation(layout, c)
    fd = _evaluated_rotation(layout, d)

    for _ in range(refinements):
        if fc.side is not None and fd.side is not None and fc.side <= fd.side:
            right = d
            d = c
            fd = fc
            c = right - (right - left) * inv_phi
            fc = _evaluated_rotation(layout, c)
        else:
            left = c
            c = d
            fc = fd
            d = left + (right - left) * inv_phi
            fd = _evaluated_rotation(layout, d)

    for candidate in (fc, fd):
        if (
            candidate.side is not None
            and best.side is not None
            and candidate.side + tolerance < best.side
        ):
            best = candidate
    return best
