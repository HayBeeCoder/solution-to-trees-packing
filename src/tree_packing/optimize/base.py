"""Strategy protocol, registry, and common optimisation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from tree_packing import config
from tree_packing.geometry import create_tree_polygon
from tree_packing.optimize.types import Layout, Placement, StrategyResult
from tree_packing.scoring import bounding_box_side, configuration_score
from tree_packing.validation.clearance import min_pairwise_clearance


@dataclass(frozen=True, slots=True)
class SolveContext:
    """Inputs shared by every strategy in one solve run."""

    artifacts_root: Path = Path("artifacts")
    run_id: str = "current"
    seed: int = 0
    strategy_names: tuple[str, ...] = ()
    params: dict[str, object] = field(default_factory=dict)
    experiment: bool = False
    n_range: tuple[int, int] = (config.MIN_TREES, config.MAX_TREES)


class Strategy(Protocol):
    """One deterministic layout generator."""

    name: str

    def solve(self, n: int, ctx: SolveContext) -> Layout | None: ...


@dataclass(slots=True)
class StrategyRegistry:
    """Ordered strategy registry used by ``tree-packing solve``."""

    _strategies: dict[str, Strategy] = field(default_factory=dict)

    def register(self, strategy: Strategy) -> Strategy:
        self._strategies[strategy.name] = strategy
        return strategy

    def names(self) -> tuple[str, ...]:
        return tuple(self._strategies)

    def selected(self, ctx: SolveContext) -> tuple[Strategy, ...]:
        if ctx.strategy_names:
            return tuple(self._strategies[name] for name in ctx.strategy_names)
        return tuple(self._strategies.values())

    def solve(self, n: int, ctx: SolveContext) -> Layout | None:
        """Return the best layout among all registered strategies for ``n``."""
        best: Layout | None = None
        for strategy in self.selected(ctx):
            candidate = strategy.solve(n, ctx)
            if candidate is None:
                continue
            evaluated = evaluate_layout(candidate)
            if best is None:
                best = evaluated
                continue
            if evaluated.score_term is not None and best.score_term is not None:
                if evaluated.score_term < best.score_term:
                    best = evaluated
                continue
            if evaluated.side is not None and best.side is not None and evaluated.side < best.side:
                best = evaluated
        return best


def evaluate_layout(layout: Layout) -> Layout:
    """Recompute the authoritative metrics for one layout."""
    placements = tuple(
        Placement(x=float(placement.x), y=float(placement.y), deg=float(placement.deg))
        for placement in layout.placements
    )
    polygons = [
        create_tree_polygon(placement.x, placement.y, placement.deg) for placement in placements
    ]
    side = bounding_box_side(polygons)
    score_term = configuration_score(side, layout.n)
    min_clearance = min_pairwise_clearance(polygons)
    return Layout(
        n=layout.n,
        placements=placements,
        side=side,
        score_term=score_term,
        min_clearance=min_clearance,
    )


def measure_layout(layout: Layout) -> Layout:
    """Compute only the score-facing metrics for search heuristics."""
    placements = tuple(
        Placement(x=float(placement.x), y=float(placement.y), deg=float(placement.deg))
        for placement in layout.placements
    )
    polygons = [
        create_tree_polygon(placement.x, placement.y, placement.deg) for placement in placements
    ]
    side = bounding_box_side(polygons)
    score_term = configuration_score(side, layout.n)
    return Layout(
        n=layout.n,
        placements=placements,
        side=side,
        score_term=score_term,
        min_clearance=None,
    )


def build_default_registry() -> StrategyRegistry:
    """Create the default strategy portfolio."""
    from tree_packing.optimize.strategies.baseline import BaselineStrategy
    from tree_packing.optimize.strategies.grid import TightGridStrategy
    from tree_packing.optimize.strategies.lattice import LatticeStrategy

    registry = StrategyRegistry()
    registry.register(BaselineStrategy())
    registry.register(TightGridStrategy())
    registry.register(LatticeStrategy())
    registry.register(LatticeStrategy())
    return registry


def solve_portfolio(ctx: SolveContext, registry: StrategyRegistry | None = None) -> StrategyResult:
    """Solve the configured range and apply the universal post-processes."""
    from tree_packing.optimize.postprocess.fast_ratchet import fast_ratchet
    from tree_packing.optimize.postprocess.rotation import best_rotation

    active_registry = registry or build_default_registry()
    layouts: list[Layout] = []
    for n in range(ctx.n_range[0], ctx.n_range[1] + 1):
        layout = active_registry.solve(n, ctx)
        if layout is None:
            raise ValueError(f"No strategy produced a layout for n={n}")
        layouts.append(best_rotation(layout))

    ratcheted_layouts = fast_ratchet(layouts)
    ratcheted = tuple(evaluate_layout(layout) for layout in ratcheted_layouts)
    total_score = sum(
        (layout.score_term for layout in ratcheted if layout.score_term is not None),
        Decimal("0"),
    )
    return StrategyResult(run_id=ctx.run_id, layouts=ratcheted, total_score=total_score)
