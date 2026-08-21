from __future__ import annotations

import json
from decimal import Decimal

from tree_packing import config
from tree_packing.baseline import build_baseline
from tree_packing.optimize import (
    BaselineStrategy,
    SolveContext,
    TightGridStrategy,
    best_rotation,
    build_default_registry,
    evaluate_layout,
)
from tree_packing.optimize.types import Layout, Placement
from tree_packing.serialization import write_submission
from tree_packing.validation.gatekeeper import gatekeep_submission


def test_default_registry_exposes_the_baseline_and_grid_portfolio() -> None:
    registry = build_default_registry()
    assert registry.names() == ("baseline", "grid")
    assert isinstance(registry.selected(SolveContext())[0], BaselineStrategy)
    assert isinstance(registry.selected(SolveContext())[1], TightGridStrategy)


def test_baseline_strategy_reproduces_the_reference_layout() -> None:
    strategy = BaselineStrategy()
    layout = strategy.solve(1, SolveContext())
    assert layout is not None
    reference = build_baseline()[1]
    assert layout.as_tuples() == reference


def test_best_rotation_finds_the_single_tree_canary() -> None:
    layout = evaluate_layout(
        Layout(
            n=1,
            placements=(Placement(x=0.0, y=0.0, deg=0.0),),
        )
    )
    rotated = best_rotation(layout)
    assert rotated.score_term.quantize(Decimal("0.00001")) == Decimal("0.66125")


def test_tight_grid_respects_the_clearance_floor() -> None:
    layout = TightGridStrategy().solve(2, SolveContext())
    assert layout is not None
    assert layout.min_clearance is not None
    assert layout.min_clearance >= config.CLEARANCE_EPS


def test_gatekeeper_compares_against_recorded_scores(tmp_path) -> None:
    submission = tmp_path / "submission.csv"
    write_submission(build_baseline(), submission)

    report = gatekeep_submission(submission)
    assert report.total_score is not None

    best_scores = tmp_path / "best_scores.json"
    best_scores.write_text(
        json.dumps(
            {
                "total_score": str(report.total_score - Decimal("0.0001")),
                "score_terms": {
                    str(report_config.n): str(report_config.score_term)
                    for report_config in report.configurations
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    regression = gatekeep_submission(submission, against=best_scores)
    assert not regression.is_valid
    assert any("total score" in error for error in regression.regression_errors)
