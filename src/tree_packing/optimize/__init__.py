"""Optimisation support types, strategies, and ledger helpers."""

from tree_packing.optimize.base import (
    SolveContext,
    Strategy,
    StrategyRegistry,
    build_default_registry,
    evaluate_layout,
    solve_portfolio,
)
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
from tree_packing.optimize.postprocess import (
    best_rotation,
    grow_layout,
    ratchet_layouts,
    rotate_layout,
)
from tree_packing.optimize.strategies import BaselineStrategy, LatticeStrategy, TightGridStrategy
from tree_packing.optimize.types import Layout, Placement, StrategyResult

__all__ = [
    "BaselineStrategy",
    "Budget",
    "LatticeStrategy",
    "Layout",
    "LedgerEntry",
    "Placement",
    "RunManifest",
    "SolveContext",
    "Strategy",
    "StrategyRegistry",
    "StrategyResult",
    "TightGridStrategy",
    "best_rotation",
    "build_default_registry",
    "build_ledger",
    "canonicalise_layout",
    "evaluate_layout",
    "grow_layout",
    "ratchet_layouts",
    "rotate_layout",
    "seed_ledger_from_baseline",
    "solve_portfolio",
    "store_run",
    "write_best_scores",
]
