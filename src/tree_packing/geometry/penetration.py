"""Penetration depth and gradient direction for tree pairs (H4.1)."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import cast

import numpy as np
from numpy.typing import NDArray
from shapely.geometry import Polygon

from tree_packing.geometry.decomposition import tree_decomposition

type FloatArray = NDArray[np.float64]


@lru_cache(maxsize=1)
def _canonical_pieces() -> tuple[FloatArray, ...]:
    return tuple(np.array(p.exterior.coords[:-1], dtype=float) for p in tree_decomposition())


def _rotate_translate_verts(
    verts: FloatArray, cos_a: float, sin_a: float, cx: float, cy: float
) -> FloatArray:
    x = verts[:, 0] * cos_a - verts[:, 1] * sin_a + cx
    y = verts[:, 0] * sin_a + verts[:, 1] * cos_a + cy
    return cast(FloatArray, np.column_stack((x, y)))


def _sat_verts(
    va: FloatArray,
    vb: FloatArray,
    centre_a: FloatArray,
    centre_b: FloatArray,
) -> tuple[float, FloatArray]:
    _zero = np.zeros(2, dtype=float)
    min_depth = float("inf")
    best_axis: FloatArray = _zero.copy()

    for verts in (va, vb):
        n = len(verts)
        for i in range(n):
            edge = verts[(i + 1) % n] - verts[i]
            normal = np.array([-edge[1], edge[0]], dtype=float)
            length = float(np.linalg.norm(normal))
            if length < 1e-12:
                continue
            axis = normal / length
            proj_a = va @ axis
            proj_b = vb @ axis
            overlap = float(min(proj_a.max(), proj_b.max())) - float(
                max(proj_a.min(), proj_b.min())
            )
            if overlap <= 0.0:
                return 0.0, _zero
            if overlap < min_depth:
                min_depth = overlap
                best_axis = -axis if float((centre_b - centre_a) @ axis) < 0.0 else axis.copy()

    if min_depth == float("inf"):
        return 0.0, _zero
    return min_depth, best_axis


def pair_penetration_depth(poly_a: Polygon, poly_b: Polygon) -> tuple[float, FloatArray]:
    va = np.array(poly_a.exterior.coords[:-1], dtype=float)
    vb = np.array(poly_b.exterior.coords[:-1], dtype=float)
    return _sat_verts(va, vb, va.mean(axis=0), vb.mean(axis=0))


def _angle_trig(deg: float) -> tuple[float, float]:
    rad = math.radians(deg)
    return math.cos(rad), math.sin(rad)


def tree_pair_depth(
    cx1: float,
    cy1: float,
    deg1: float,
    cx2: float,
    cy2: float,
    deg2: float,
) -> tuple[float, FloatArray]:
    cos1, sin1 = _angle_trig(deg1)
    cos2, sin2 = _angle_trig(deg2)
    canonical = _canonical_pieces()
    tree_c1 = np.array([cx1, cy1], dtype=float)
    tree_c2 = np.array([cx2, cy2], dtype=float)

    max_depth = 0.0
    best_direction: FloatArray = np.zeros(2, dtype=float)

    for i in range(4):
        va = _rotate_translate_verts(canonical[i], cos1, sin1, cx1, cy1)
        for j in range(4):
            vb = _rotate_translate_verts(canonical[j], cos2, sin2, cx2, cy2)
            depth, direction = _sat_verts(va, vb, tree_c1, tree_c2)
            if depth > max_depth:
                max_depth = depth
                best_direction = direction

    return max_depth, best_direction


def tree_pair_mtv(
    cx1: float,
    cy1: float,
    deg1: float,
    cx2: float,
    cy2: float,
    deg2: float,
) -> tuple[float, float]:
    depth, direction = tree_pair_depth(cx1, cy1, deg1, cx2, cy2, deg2)
    return float(depth * direction[0]), float(depth * direction[1])
