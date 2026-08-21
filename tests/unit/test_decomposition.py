from shapely.geometry import Polygon

from tree_packing.geometry.decomposition import tree_decomposition, tree_piece_polygons


def _canonical_polygon() -> Polygon:
    return Polygon(
        [
            (0.0, 0.8),
            (0.125, 0.5),
            (0.0625, 0.5),
            (0.2, 0.25),
            (0.1, 0.25),
            (0.35, 0.0),
            (0.075, 0.0),
            (0.075, -0.2),
            (-0.075, -0.2),
            (-0.075, 0.0),
            (-0.35, 0.0),
            (-0.1, 0.25),
            (-0.2, 0.25),
            (-0.0625, 0.5),
            (-0.125, 0.5),
        ]
    )


def test_four_piece_decomposition_is_exact() -> None:
    pieces = tree_decomposition()
    assert len(pieces) == 4
    assert all(piece.is_valid for piece in pieces)
    assert all(piece.equals(piece.convex_hull) for piece in pieces)
    assert all(
        piece.intersection(other).area == 0.0
        for i, piece in enumerate(pieces)
        for other in pieces[i + 1 :]
    )
    union = pieces[0].union(pieces[1]).union(pieces[2]).union(pieces[3])
    assert union.symmetric_difference(_canonical_polygon()).area < 1e-15
    assert abs(sum(piece.area for piece in pieces) - 0.245625) < 1e-15


def test_piece_alias_matches() -> None:
    assert tree_piece_polygons() == tree_decomposition()
