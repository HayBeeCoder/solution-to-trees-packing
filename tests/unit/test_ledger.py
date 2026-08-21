from decimal import Decimal

from tree_packing.optimize.ledger import (
    Budget,
    LedgerEntry,
    RunManifest,
    build_ledger,
    canonicalise_layout,
    seed_ledger_from_baseline,
    store_run,
    write_best_scores,
)
from tree_packing.optimize.types import Layout, Placement


def _manifest(run_id: str, experiment: bool = False) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        strategy="grid",
        params={},
        seed=1,
        git_sha="abc123",
        started_at="2026-08-21T00:00:00Z",
        wall_clock_s=1.0,
        budget=Budget(kind="evaluations", value=2),
        experiment=experiment,
        n_range=(1, 1),
    )


def _layout(score_term: str, clearance: str, deg: float = 1.0) -> Layout:
    return Layout(
        n=1,
        placements=(Placement(x=1.0, y=2.0, deg=deg),),
        side=Decimal("1.0"),
        score_term=Decimal(score_term),
        min_clearance=Decimal(clearance),
    )


def test_canonicalise_layout_reflects_negative_angle_sum() -> None:
    layout = Layout(
        n=1,
        placements=(Placement(x=1.0, y=2.0, deg=-1.0),),
        side=None,
        score_term=None,
        min_clearance=None,
    )
    canonical = canonicalise_layout(layout)
    assert canonical.placements[0].x == -1.0
    assert canonical.placements[0].deg == 1.0


def test_ledger_is_immutable_and_derived(tmp_path) -> None:
    artifacts = tmp_path / "artifacts"
    store_run(artifacts, _manifest("run-a"), [_layout("1.0", "1e-6")])
    store_run(artifacts, _manifest("run-b"), [_layout("0.9", "1e-6")])
    store_run(artifacts, _manifest("run-exp", experiment=True), [_layout("0.1", "1e-6")])
    store_run(artifacts, _manifest("run-bad"), [_layout("0.01", "1e-12")])

    ledger = build_ledger(artifacts)
    assert ledger == {"1": LedgerEntry(run_id="run-b", score_term=Decimal("0.9"))}
    ledger_text = (artifacts / "ledger.json").read_text(encoding="utf-8")
    assert "run-b" in ledger_text
    assert "run-exp" not in ledger_text
    assert "run-bad" not in ledger_text


def test_seed_ledger_from_baseline_populates_all_configurations(tmp_path) -> None:
    ledger = seed_ledger_from_baseline(tmp_path / "artifacts")
    assert sorted(int(key) for key in ledger) == list(range(1, 201))
    assert all(entry.score_term > Decimal("0") for entry in ledger.values())


def test_write_best_scores_serializes_total_and_terms(tmp_path) -> None:
    root = tmp_path / "artifacts"
    layouts = [
        Layout(
            n=1,
            placements=(Placement(x=1.0, y=2.0, deg=1.0),),
            side=Decimal("1.0"),
            score_term=Decimal("1.0"),
            min_clearance=Decimal("1e-6"),
        ),
        Layout(
            n=2,
            placements=(Placement(x=1.0, y=2.0, deg=1.0),),
            side=Decimal("1.0"),
            score_term=Decimal("0.9"),
            min_clearance=Decimal("1e-6"),
        ),
    ]
    best_scores = write_best_scores(root, layouts)
    assert best_scores == root / "best_scores.json"
    text = best_scores.read_text(encoding="utf-8")
    assert '"total_score": "1.9"' in text
    assert '"1": "1.0"' in text
    assert '"2": "0.9"' in text
