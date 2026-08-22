"""Basin-hopping with compaction as local minimiser (H4.4).

Essence: randomly perturb tree positions, compact, accept if better
(or occasionally if slightly worse — Metropolis criterion). Repeat.
This escapes local minima that plain compaction gets stuck in.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from tree_packing.optimize.postprocess.compaction import compact_layout
from tree_packing.optimize.types import Layout, Placement

_PERTURB_SCALE: float = 0.3  # std dev of random displacement (problem units)
_TEMPERATURE: float = 0.5  # Metropolis temperature (score units)
_N_HOPS: int = 15  # number of perturbation + compact cycles
_SEED: int = 42
FloatArray = NDArray[np.float64]


def basin_hop(
    layout: Layout,
    *,
    n_hops: int = _N_HOPS,
    perturb_scale: float = _PERTURB_SCALE,
    temperature: float = _TEMPERATURE,
    shrink_factor: float = 0.01,
    max_outer: int = 30,
    seed: int = _SEED,
) -> Layout:
    """Run basin-hopping on ``layout`` and return the best layout found.

    Each hop:
    1. Randomly displace all tree centres by Gaussian noise.
    2. Compact the perturbed layout.
    3. Accept if score improved, or with Metropolis probability if slightly worse.
    """
    rng = np.random.default_rng(seed)

    current = compact_layout(layout, shrink_factor=shrink_factor, max_outer=max_outer)
    best = current
    current_score = float(current.score_term) if current.score_term is not None else float("inf")
    best_score = current_score

    xs = np.array([p.x for p in current.placements], dtype=float)
    ys = np.array([p.y for p in current.placements], dtype=float)
    degs = np.array([p.deg for p in current.placements], dtype=float)
    n = len(xs)

    for _ in range(n_hops):
        # Perturb
        dx = rng.normal(0.0, perturb_scale, size=n)
        dy = rng.normal(0.0, perturb_scale, size=n)
        xs_p = xs + dx
        ys_p = ys + dy

        placements = tuple(
            Placement(x=float(xs_p[k]), y=float(ys_p[k]), deg=float(degs[k])) for k in range(n)
        )
        perturbed = Layout(n=n, placements=placements)

        # Compact
        compacted = compact_layout(perturbed, shrink_factor=shrink_factor, max_outer=max_outer)
        candidate_score = (
            float(compacted.score_term) if compacted.score_term is not None else float("inf")
        )

        # Metropolis accept/reject
        delta = candidate_score - current_score
        if delta < 0 or (temperature > 0 and rng.random() < math.exp(-delta / temperature)):
            current = compacted
            current_score = candidate_score
            xs = np.array([p.x for p in current.placements], dtype=float)
            ys = np.array([p.y for p in current.placements], dtype=float)

        if candidate_score < best_score:
            best = compacted
            best_score = candidate_score

    return best
