"""H2.5 — the downward ratchet propagates improvements for free.

A valid n+1 layout contains a valid n layout by deleting a tree, so
s_n <= s_{n+1} is a theorem, not an aspiration: a violation means the ledger
holds a worse-than-necessary solution somewhere (shared contract sec 2.2/H2.5).

s_n is derived from the committed per-configuration score terms via
s_n = sqrt(term_n * n), since configuration_score(side, n) = side**2 / n.

A small tolerance (TOLERANCE) is required, not a stylistic choice: the score
terms in artifacts/best_scores.json are serialized Decimal strings truncated
at limited precision, so recomputing s_n at higher working precision surfaces
representation noise on the order of 1e-24 to 1e-25 between adjacent terms
even for the real, correct, committed data (confirmed empirically below this
docstring, see LAB_NOTEBOOK.md M2.5). That noise is ~15 orders of magnitude
below CLEARANCE_EPS (1e-9) and is not a geometric regression. TOLERANCE is set
two orders above the observed noise floor and eleven below CLEARANCE_EPS, so
it cannot mask a real violation while still tolerating serialization noise.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from tree_packing import config

TOLERANCE = Decimal("1e-20")

BEST_SCORES_PATH = Path(__file__).parent.parent.parent / "artifacts" / "best_scores.json"


def _load_side_lengths(path: Path) -> dict[int, Decimal]:
    data = json.loads(path.read_text(encoding="utf-8"))
    terms = {int(key): Decimal(value) for key, value in data["score_terms"].items()}
    return {n: (terms[n] * n).sqrt() for n in terms}


def test_monotonicity_holds_across_committed_best_scores() -> None:
    """s_n <= s_{n+1} (within serialization tolerance) for all committed configs."""
    sides = _load_side_lengths(BEST_SCORES_PATH)
    assert sorted(sides) == list(range(config.MIN_TREES, config.MAX_TREES + 1))

    violations = [
        (n, sides[n], sides[n + 1])
        for n in range(config.MIN_TREES, config.MAX_TREES)
        if sides[n] > sides[n + 1] + TOLERANCE
    ]
    assert violations == [], f"monotonicity violated at: {violations[:5]}"


def test_monotonicity_tolerance_is_far_below_clearance_eps() -> None:
    """The tolerance used above must never approach a real geometric quantity."""
    assert TOLERANCE * Decimal("1e11") <= config.CLEARANCE_EPS
