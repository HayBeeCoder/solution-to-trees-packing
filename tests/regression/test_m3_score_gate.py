"""M3 exit gate — total score must not exceed the committed M3 ceiling.

The lattice pipeline (H3.6) produced a verified combined score of
100.2872... across n=1..200. This gate asserts the committed best_scores.json
total stays at or below that ceiling, so no future change can silently worsen
the M3 result.

The ceiling is set to 100.30 (rounded up by 0.02 from the measured 100.287)
to absorb any floating-point noise in Decimal serialisation without masking
a real regression (a real regression would move the score by at least 0.1).
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

BEST_SCORES_PATH = Path(__file__).parent.parent.parent / "artifacts" / "best_scores.json"

M3_SCORE_CEILING = Decimal("100.30")
M3_TARGET = Decimal("110")


def test_m3_total_score_within_ceiling() -> None:
    """Committed total score must be <= M3 ceiling (100.30)."""
    data = json.loads(BEST_SCORES_PATH.read_text(encoding="utf-8"))
    terms = {int(k): Decimal(v) for k, v in data["score_terms"].items()}
    total = sum(terms.values())
    assert total <= M3_SCORE_CEILING, (
        f"Total score {total} exceeds M3 ceiling {M3_SCORE_CEILING} — "
        "a layout change has worsened the result"
    )


def test_m3_target_met() -> None:
    """Committed total score must be <= the M3 milestone target of 110."""
    data = json.loads(BEST_SCORES_PATH.read_text(encoding="utf-8"))
    terms = {int(k): Decimal(v) for k, v in data["score_terms"].items()}
    total = sum(terms.values())
    assert total <= M3_TARGET, (
        f"Total score {total} exceeds M3 target {M3_TARGET}"
    )
