"""Persisted store for H3.2 lattice-search runs.

``optimize.ledger.RunManifest``/``store_run`` are shaped for per-configuration
submissions (a ``Layout`` keyed by ``n``), which a lattice-search run is not:
one run here produces a single five-parameter cell, not 200 per-n layouts.
Rather than force an awkward fit, this stores lattice runs in their own,
smaller schema under ``artifacts/lattice_runs/`` -- in the same spirit as the
milestone's explicit warning that a good, unstored result is gone forever
(the ``0.7086`` result lost because it was only printed).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from tree_packing.geometry.lattice_search import SearchResult


def store_lattice_run(root: str | Path, result: SearchResult) -> Path:
    """Write one immutable lattice-run record and return its path."""
    root_path = Path(root)
    run_dir = root_path / "lattice_runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"seed-{result.seed}.json"
    payload = {
        "seed": result.seed,
        "basis": asdict(result.basis),
        "density": result.density,
        "min_clearance": str(result.min_clearance),
        "wall_clock_s": result.wall_clock_s,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_lattice_runs(root: str | Path) -> list[dict[str, object]]:
    """Read back every stored lattice run, sorted by seed."""
    run_dir = Path(root) / "lattice_runs"
    if not run_dir.exists():
        return []
    records = []
    for path in sorted(run_dir.glob("seed-*.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records
