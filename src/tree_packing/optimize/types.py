"""Frozen data structures used by the optimisation layer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Placement:
    """One tree placement in problem coordinates."""

    x: float
    y: float
    deg: float

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.deg)


@dataclass(frozen=True, slots=True)
class Layout:
    """A complete arrangement for one configuration size."""

    n: int
    placements: tuple[Placement, ...]
    side: Decimal | None = None
    score_term: Decimal | None = None
    min_clearance: Decimal | None = None

    def as_tuples(self) -> list[tuple[float, float, float]]:
        return [placement.as_tuple() for placement in self.placements]


@dataclass(frozen=True, slots=True)
class StrategyResult:
    """Summary of a completed search strategy."""

    run_id: str
    layouts: tuple[Layout, ...]
    total_score: Decimal | None = None
