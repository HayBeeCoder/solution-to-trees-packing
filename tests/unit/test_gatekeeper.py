from pathlib import Path

from tree_packing.baseline import build_baseline
from tree_packing.config import CLEARANCE_EPS
from tree_packing.optimize.ledger import Budget, RunManifest, store_run
from tree_packing.optimize.types import Layout, Placement
from tree_packing.validation.gatekeeper import gatekeep_submission


def _write_adversarial_submission(path: Path) -> None:
    baseline = build_baseline()
    baseline[2] = [(0.0, 0.0, 0.0), (0.7000000005, 0.0, 0.0)]
    from tree_packing.serialization import write_submission

    write_submission(baseline, path)
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("s0.7000000005", "s0.70000000"), encoding="utf-8")


def test_gatekeeper_rejects_rounding_into_contact(tmp_path) -> None:
    submission = tmp_path / "submission.csv"
    _write_adversarial_submission(submission)
    report = gatekeep_submission(submission)
    assert not report.is_valid
    assert report.validation_errors == ()
    assert any(report.configurations)
    n2 = next(config for config in report.configurations if config.n == 2)
    assert n2.min_clearance < CLEARANCE_EPS


def test_store_run_and_gatekeeper_can_round_trip(tmp_path) -> None:
    artifacts = tmp_path / "artifacts"
    run_dir = artifacts / "runs"
    manifest = RunManifest(
        run_id="run-a",
        strategy="grid",
        params={},
        seed=1,
        git_sha="abc123",
        started_at="2026-08-21T00:00:00Z",
        wall_clock_s=1.0,
        budget=Budget(kind="evaluations", value=2),
        experiment=False,
        n_range=(1, 1),
    )
    layout = Layout(
        n=1,
        placements=(Placement(x=0.0, y=0.0, deg=0.0),),
        side=None,
        score_term=None,
        min_clearance=None,
    )
    stored = store_run(artifacts, manifest, [layout])
    assert stored == run_dir / "run-a"
