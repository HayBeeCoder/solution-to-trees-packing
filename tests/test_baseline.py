from tree_packing.baseline import build_baseline, grid_positions
from tree_packing.geometry import create_tree_polygon
from tree_packing.validation import has_overlap


def test_single_tree_at_origin() -> None:
    assert grid_positions(1) == [(0.0, 0.0, 0.0)]


def test_zero_returns_empty() -> None:
    assert grid_positions(0) == []


def test_count_matches_n() -> None:
    for n in (1, 2, 7, 25, 100, 200):
        assert len(grid_positions(n)) == n


def test_grid_never_overlaps() -> None:
    for n in (1, 2, 4, 9, 16, 25):
        polys = [create_tree_polygon(x, y, d) for x, y, d in grid_positions(n)]
        assert not has_overlap(polys)


def test_build_baseline_covers_all_configs() -> None:
    baseline = build_baseline()
    assert sorted(baseline) == list(range(1, 201))
    assert sum(len(value) for value in baseline.values()) == 20100
