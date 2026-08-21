"""Exact four-piece convex decomposition of the canonical tree polygon."""

from __future__ import annotations

from shapely.geometry import Polygon

from tree_packing import config


def _piece(vertices: list[tuple[float, float]]) -> Polygon:
    return Polygon(vertices)


def tree_decomposition() -> tuple[Polygon, ...]:
    """Return the four convex pieces in unscaled problem coordinates."""
    return (
        _piece(
            [
                (-0.075, -float(config.TRUNK_HEIGHT)),
                (0.075, -float(config.TRUNK_HEIGHT)),
                (0.075, 0.0),
                (-0.075, 0.0),
            ]
        ),
        _piece([(-0.35, 0.0), (0.35, 0.0), (0.1, 0.25), (-0.1, 0.25)]),
        _piece([(-0.2, 0.25), (0.2, 0.25), (0.0625, 0.5), (-0.0625, 0.5)]),
        _piece([(-0.125, 0.5), (0.125, 0.5), (0.0, 0.8)]),
    )


def tree_piece_polygons() -> tuple[Polygon, ...]:
    """Return only the polygons for callers that do not need names."""
    return tree_decomposition()
