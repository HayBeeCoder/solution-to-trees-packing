from __future__ import annotations

import math
import random

from shapely.geometry import Polygon

from tree_packing.config import SCALE_FACTOR
from tree_packing.geometry.core import create_tree_polygon
from tree_packing.geometry.fast import create_tree_polygon_fast


def _vertex_deviation(a: Polygon, b: Polygon) -> float:
    coords_a = list(a.exterior.coords)[:-1]
    coords_b = list(b.exterior.coords)[:-1]
    return max(
        math.hypot((ax - bx) / float(SCALE_FACTOR), (ay - by) / float(SCALE_FACTOR))
        for (ax, ay), (bx, by) in zip(coords_a, coords_b, strict=True)
    )


def test_fast_geometry_matches_shapely_path() -> None:
    rng = random.Random(0)
    max_deviation = 0.0
    for _ in range(10_000):
        x = rng.uniform(-5.0, 5.0)
        y = rng.uniform(-5.0, 5.0)
        angle = rng.uniform(-180.0, 180.0)
        core = create_tree_polygon(x, y, angle)
        fast = create_tree_polygon_fast(x, y, angle)
        max_deviation = max(max_deviation, _vertex_deviation(core, fast))
    assert max_deviation <= 1e-14
