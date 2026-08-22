"""
Full optimised solve with compaction.
Run manually: uv run python solve_full.py
Updates artifacts/best_scores.json and data/submissions/current.csv
"""

import json
import time
from decimal import Decimal, getcontext
from pathlib import Path

from tree_packing.geometry.lattice import LatticeBasis
from tree_packing.geometry.truncation import truncate_to_n
from tree_packing.optimize.base import SolveContext, evaluate_layout
from tree_packing.optimize.postprocess.compaction import compact_layout
from tree_packing.optimize.postprocess.fast_ratchet import fast_ratchet
from tree_packing.optimize.postprocess.rotation import best_rotation
from tree_packing.optimize.strategies.grid import TightGridStrategy
from tree_packing.optimize.types import Layout, Placement
from tree_packing.serialization import write_submission

getcontext().prec = 25


BASIS = LatticeBasis(
    p=0.8466998057329839,
    q=-0.2595569327159729,
    h=0.8000013958277571,
    u=-0.15564510572139056,
    v=-0.30308104064715025,
)

ctx = SolveContext()
strategy = TightGridStrategy()
all_layouts = []
score_terms: dict[int, Decimal] = {}
t_start = time.perf_counter()

# n=1..20: grid + compaction
print("n=1..20: grid + compaction ...")
for n in range(1, 21):
    lay = evaluate_layout(strategy.solve(n, ctx))
    compacted = compact_layout(lay, shrink_factor=0.01, max_outer=50)
    score_terms[n] = compacted.score_term
    all_layouts.append(compacted)
    print(
        f"  n={n:3d}: {float(lay.side):.4f} -> {float(compacted.side):.4f}",
        f"  clr={compacted.min_clearance}",
    )

# n=21..200: lattice + rotation + ratchet + compaction
print("n=21..200: lattice + ratchet + compaction ...")
raw_layouts = []
for n in range(21, 201):
    raw = truncate_to_n(BASIS, n)
    pl = tuple(Placement(x=x, y=y, deg=deg) for x, y, deg in raw)
    raw_layouts.append(best_rotation(Layout(n=n, placements=pl)))

ratcheted = fast_ratchet(raw_layouts)
for lay in ratcheted:
    ev = evaluate_layout(lay)
    compacted = compact_layout(ev, shrink_factor=0.005, max_outer=30)
    score_terms[lay.n] = compacted.score_term
    all_layouts.append(compacted)
    print(
        f"  n={lay.n:3d}: {float(ev.side):.4f} -> {float(compacted.side):.4f}",
        f"  clr={compacted.min_clearance}",
    )

total = sum(score_terms.values())
elapsed = time.perf_counter() - t_start

print(f"\nTotal score: {float(total):.4f}")
print(f"Wall time:   {elapsed / 60:.1f} minutes")

# Save best scores
out = {
    "total_score": str(total),
    "score_terms": {str(n): str(score_terms[n]) for n in range(1, 201)},
}
with Path.open("artifacts/best_scores.json", "w") as f:
    json.dump(out, f, indent=2)
print("Saved artifacts/best_scores.json")

# Write submission CSV
write_submission(all_layouts, "data/submissions/current.csv")
print("Saved data/submissions/current.csv")
