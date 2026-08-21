from decimal import Decimal

from tree_packing.baseline import build_baseline
from tree_packing.geometry import create_tree_polygon
from tree_packing.scoring import bounding_box_side, configuration_score
from tree_packing.serialization import load_submission, write_submission
from tree_packing.validation import find_overlapping_pairs, validate_submission_frame


def test_baseline_is_structurally_valid(tmp_path) -> None:
    out = tmp_path / "baseline.csv"
    write_submission(build_baseline(), out)
    df = load_submission(out)
    assert validate_submission_frame(df) == []


def test_baseline_small_n_no_overlap_and_scores(tmp_path) -> None:
    out = tmp_path / "baseline.csv"
    write_submission(build_baseline(), out)
    df = load_submission(out)

    total = Decimal("0")
    for n in range(1, 21):
        cfg = df[df["n"] == n]
        polys = [create_tree_polygon(row.x, row.y, row.deg) for row in cfg.itertuples()]
        assert find_overlapping_pairs(polys) == []
        total += configuration_score(bounding_box_side(polys), n)

    assert total > 0
    n1 = df[df["n"] == 1]
    side = bounding_box_side(
        [create_tree_polygon(row.x, row.y, row.deg) for row in n1.itertuples()]
    )
    assert abs(configuration_score(side, 1) - Decimal("1.0")) < Decimal("1e-9")
