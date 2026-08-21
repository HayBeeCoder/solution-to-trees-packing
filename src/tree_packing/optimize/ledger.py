"""Immutable run-store helpers and the derived ledger."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from tree_packing import config
from tree_packing.baseline import build_baseline
from tree_packing.geometry import create_tree_polygon
from tree_packing.optimize.types import Layout, Placement
from tree_packing.scoring import bounding_box_side, configuration_score
from tree_packing.validation.clearance import min_pairwise_clearance


@dataclass(frozen=True, slots=True)
class Budget:
    """Search budget metadata stored in run manifests."""

    kind: str
    value: int


@dataclass(frozen=True, slots=True)
class RunManifest:
    """Metadata for one immutable optimiser run."""

    run_id: str
    strategy: str
    params: dict[str, Any]
    seed: int
    git_sha: str
    started_at: str
    wall_clock_s: float
    budget: Budget
    experiment: bool
    n_range: tuple[int, int]


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """Derived arg-min entry for one configuration."""

    run_id: str
    score_term: Decimal


def _to_placement(value: Placement | tuple[float, float, float]) -> Placement:
    if isinstance(value, Placement):
        return value
    return Placement(*value)


def canonicalise_layout(layout: Layout) -> Layout:
    """Mirror the layout if the signed angle sum is negative."""
    placements = tuple(_to_placement(placement) for placement in layout.placements)
    if sum(placement.deg for placement in placements) < 0:
        placements = tuple(
            Placement(-placement.x, placement.y, -placement.deg) for placement in placements
        )
    return Layout(
        n=layout.n,
        placements=placements,
        side=layout.side,
        score_term=layout.score_term,
        min_clearance=layout.min_clearance,
    )


def _layout_to_json(layout: Layout) -> dict[str, Any]:
    canonical = canonicalise_layout(layout)
    placements = [list(placement.as_tuple()) for placement in canonical.placements]
    return {
        "n": canonical.n,
        "side": float(canonical.side) if canonical.side is not None else None,
        "score_term": float(canonical.score_term) if canonical.score_term is not None else None,
        "min_clearance": float(canonical.min_clearance)
        if canonical.min_clearance is not None
        else None,
        "placements": placements,
    }


def store_run(
    root: str | Path, manifest: RunManifest, layouts: list[Layout] | tuple[Layout, ...]
) -> Path:
    """Write one immutable run directory and return its path."""
    root_path = Path(root)
    run_dir = root_path / "runs" / manifest.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = run_dir / "manifest.json"
    layouts_path = run_dir / "layouts.jsonl"
    manifest_path.write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True), encoding="utf-8"
    )
    with layouts_path.open("w", encoding="utf-8") as handle:
        for layout in layouts:
            handle.write(json.dumps(_layout_to_json(layout), sort_keys=True))
            handle.write("\n")
    return run_dir


def _load_manifest(path: Path) -> RunManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    budget_data = data["budget"]
    return RunManifest(
        run_id=data["run_id"],
        strategy=data["strategy"],
        params=dict(data["params"]),
        seed=int(data["seed"]),
        git_sha=data["git_sha"],
        started_at=data["started_at"],
        wall_clock_s=float(data["wall_clock_s"]),
        budget=Budget(kind=budget_data["kind"], value=int(budget_data["value"])),
        experiment=bool(data["experiment"]),
        n_range=(int(data["n_range"][0]), int(data["n_range"][1])),
    )


def _load_layouts(path: Path) -> list[dict[str, Any]]:
    layouts: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            layouts.append(json.loads(line))
    return layouts


def build_ledger(root: str | Path = "artifacts") -> dict[str, LedgerEntry]:
    """Recompute the derived ledger from all stored runs."""
    root_path = Path(root)
    runs_root = root_path / "runs"
    ledger: dict[str, LedgerEntry] = {}

    if not runs_root.exists():
        return ledger

    for manifest_path in sorted(runs_root.glob("*/manifest.json")):
        manifest = _load_manifest(manifest_path)
        if manifest.experiment:
            continue
        layouts_path = manifest_path.with_name("layouts.jsonl")
        for layout_data in _load_layouts(layouts_path):
            n = int(layout_data["n"])
            score_term = Decimal(str(layout_data["score_term"]))
            min_clearance = Decimal(str(layout_data["min_clearance"]))
            if min_clearance < config.CLEARANCE_EPS:
                continue
            key = str(n)
            incumbent = ledger.get(key)
            if incumbent is None or score_term < incumbent.score_term:
                ledger[key] = LedgerEntry(run_id=manifest.run_id, score_term=score_term)

    ledger_path = root_path / "ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(
            {
                key: {"run_id": entry.run_id, "score_term": float(entry.score_term)}
                for key, entry in sorted(ledger.items(), key=lambda item: int(item[0]))
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return ledger


def seed_ledger_from_baseline(root: str | Path = "artifacts") -> dict[str, LedgerEntry]:
    """Populate the run store and ledger from the deterministic baseline."""
    baseline = build_baseline()
    layouts: list[Layout] = []
    for n, placements in baseline.items():
        polygon_data = [create_tree_polygon(str(x), str(y), str(deg)) for x, y, deg in placements]
        side = bounding_box_side(polygon_data)
        score_term = configuration_score(side, n)
        min_clearance = min_pairwise_clearance(polygon_data)
        layout = Layout(
            n=n,
            placements=tuple(Placement(x=x, y=y, deg=deg) for x, y, deg in placements),
            side=side,
            score_term=score_term,
            min_clearance=min_clearance,
        )
        layouts.append(layout)

    manifest = RunManifest(
        run_id="baseline",
        strategy="baseline",
        params={},
        seed=0,
        git_sha="baseline",
        started_at="1970-01-01T00:00:00Z",
        wall_clock_s=0.0,
        budget=Budget(kind="baseline", value=len(layouts)),
        experiment=False,
        n_range=(config.MIN_TREES, config.MAX_TREES),
    )
    store_run(root, manifest, layouts)
    return build_ledger(root)
