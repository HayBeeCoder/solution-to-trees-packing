import pandas as pd

from tree_packing.geometry import create_tree_polygon
from tree_packing.validation import (
    find_overlapping_pairs,
    has_overlap,
    validate_submission_frame,
)


def test_identical_trees_overlap() -> None:
    polys = [create_tree_polygon(0, 0, 0), create_tree_polygon(0, 0, 0)]
    assert has_overlap(polys)
    assert find_overlapping_pairs(polys) == [(0, 1)]


def test_far_apart_trees_do_not_overlap() -> None:
    polys = [create_tree_polygon(0, 0, 0), create_tree_polygon(5, 0, 0)]
    assert not has_overlap(polys)


def test_single_polygon_never_overlaps() -> None:
    assert find_overlapping_pairs([create_tree_polygon(0, 0, 0)]) == []


def test_submission_frame_flags_missing_and_out_of_bounds() -> None:
    frame = pd.DataFrame(
        [
            {"n": 1, "tree_idx": 0, "x": 0.0, "y": 0.0, "deg": 0.0},
            {"n": 2, "tree_idx": 0, "x": 101.0, "y": 0.0, "deg": 0.0},
        ]
    )
    errors = validate_submission_frame(frame)
    assert any("Missing" in error for error in errors)
    assert any("outside" in error for error in errors)
