"""Downward ratchet that propagates improvements from larger layouts."""

from __future__ import annotations

from tree_packing.optimize.base import evaluate_layout
from tree_packing.optimize.types import Layout


def _shrink_once(layout: Layout) -> Layout:
    if layout.n <= 1:
        return evaluate_layout(layout)

    best: Layout | None = None
    for index in range(len(layout.placements)):
        candidate = evaluate_layout(
            Layout(
                n=layout.n - 1,
                placements=layout.placements[:index] + layout.placements[index + 1 :],
            )
        )
        if best is None:
            best = candidate
            continue
        if candidate.side is not None and best.side is not None and candidate.side < best.side:
            best = candidate
    if best is None:  # pragma: no cover - defensive
        return evaluate_layout(layout)
    return best


def ratchet_layouts(layouts: tuple[Layout, ...]) -> tuple[Layout, ...]:
    """Replace each layout with a shrunk version of the next larger layout when useful."""
    ratcheted = [evaluate_layout(layout) for layout in layouts]
    for index in range(len(ratcheted) - 2, -1, -1):
        candidate = _shrink_once(ratcheted[index + 1])
        current = ratcheted[index]
        if (
            candidate.score_term is not None
            and current.score_term is not None
            and candidate.score_term <= current.score_term
        ):
            ratcheted[index] = candidate
    return tuple(ratcheted)
