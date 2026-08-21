"""Vectorised vertex transform for SEARCH ONLY.

This module is NOT authoritative. It is deliberately not bit-identical to
``geometry.core``; deviations of order 1e-16 in problem units are expected and
acceptable because every candidate is re-validated through ``core`` before it can
enter the ledger. Never import this module from ``validation/``.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from shapely.geometry import Polygon

from tree_packing import config
from tree_packing.geometry.core import tree_vertices

BASE_VERTICES: Any = np.asarray(tree_vertices(), dtype=float)


def transform_vertices(center_x: float, center_y: float, angle_degrees: float) -> Any:
    """Rotate and translate the cached vertex array in Shapely working space."""
    angle = math.radians(float(angle_degrees))
    cos_theta = math.cos(angle)
    sin_theta = math.sin(angle)
    x_coords = BASE_VERTICES[:, 0]
    y_coords = BASE_VERTICES[:, 1]
    rotated_x = x_coords * cos_theta - y_coords * sin_theta
    rotated_y = x_coords * sin_theta + y_coords * cos_theta
    offset_x = float(center_x) * float(config.SCALE_FACTOR)
    offset_y = float(center_y) * float(config.SCALE_FACTOR)
    return np.column_stack((rotated_x + offset_x, rotated_y + offset_y))


def create_tree_polygon_fast(center_x: float, center_y: float, angle_degrees: float) -> Polygon:
    """Build a tree polygon from the NumPy transform."""
    return Polygon(transform_vertices(center_x, center_y, angle_degrees))


def tree_vertices_array() -> Any:
    """Return a copy of the cached tree vertex array."""
    return BASE_VERTICES.copy()
