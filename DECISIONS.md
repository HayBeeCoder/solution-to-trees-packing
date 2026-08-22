# Implementation decisions

## Faithful port over reinvention

The constants and polygon vertices are copied from the supplied evaluator. The
geometry is defined once in `src/tree_packing/geometry/core.py`, then reused by scoring and validation,
so the internal gatekeeper cannot silently disagree with the official evaluator.

## M1 package boundaries and derived ledgers

M1 splits the flat geometry and validation modules into sub-packages so the
search-only fast path stays out of the authoritative validation path.
`src/tree_packing/geometry/fast.py` exists for search acceleration only; `src/tree_packing/validation/`
imports `src/tree_packing/geometry/core.py` and never the fast path. The run ledger is derived from stored
runs, not hand-edited, and it rejects experiment runs and layouts below the
clearance floor even if their score is attractive.

## `src/` layout and `uv`

The `src/` layout keeps package imports separate from repository tooling, while
`uv` provides an isolated environment and a reproducible lockfile. The CLI is a
single entry point over the pure package functions.

## Decimal coordinates and the scale factor

The evaluator's Decimal inputs are multiplied by `1e15` before reaching Shapely's
float64 geometry predicates. Retaining that convention protects small coordinate
comparisons from avoidable floating-point noise while preserving evaluator parity.

## Scope boundary

There is deliberately no optimizer. The grid baseline is the reference point for
future work, and the metric a future optimizer would target is the evaluator's
weighted sum of `s_n^2 / n`.

## Testing philosophy

Closed-form quantities such as the tree area (`0.245625`) and single-tree side
(`1.0`) have concrete expected values. Integration tests exercise all 200
configurations structurally but keep polygon scoring to small `n` for fast CI.
The parity test compares our polygon directly with the retained reference.

## Process: “Agentic Coding is Science”

The implementation is tracked as hypothesis → generate → run/observe → measure
→ select/refine. The quality gates and reference parity check are the labels;
`LAB_NOTEBOOK.md` records the hypotheses, traces, failures, and corrections so
the work is reviewable as a falsifiable engineering process rather than an
unexplained sequence of edits.

## M0 hygiene and reproducibility

The briefly introduced hosted CI workflow was reverted. The deliverable is
reviewed from a Drive folder, so a reviewer cannot rely on its remote Actions
history. A clean-room clone and a local `pre-push` hook running `make verify`
test the practical risks directly.

Ignore rules now describe only generated artifacts; committed decisions,
notebook, documentary, and plans remain visible. Pytest coverage is opt-in via
`make coverage`, preventing concurrent default test runs from competing for the
same `.coverage` file. The Makefile is intentionally a thin wrapper around the
existing `uv run` commands, keeping the README runbook and local hook aligned.

## M2 measurement order and the honest baseline

M2 comes before M3 because the free rotation and ratchet-style passes are
global post-processes: if the lattice were introduced first, its score would be
inflated by improvements that actually belong to the universal pipeline. The
comparison baseline for this milestone is therefore the tight rectangular grid,
not the sparse `1.1` baseline. That honest baseline measured `157.986`, while
the recorded M2 solve reached `157.0885749337038018263178` in `181.45s` and
kept the regression gate green.

### Addendum (2026-08-21 exit-gate closure audit)

Two things surfaced while closing the M2 exit gate that belong here rather
than only in `LAB_NOTEBOOK.md`, because they are decisions with consequences
for M3, not just observations:

1. **Insertion and ratchet are implemented but not wired into `solve`.**
   `src/tree_packing/optimize/base.py::solve_portfolio` only calls the strategy portfolio and
   `best_rotation`; it never calls `grow_layout` (insertion) or
   `ratchet_layouts` (ratchet). Both exist and are unit-tested in isolation.
   The committed score, `157.0885749337038018263178`, is therefore a grid +
   rotation result only. Decision: leave this unwired for M2's closure — the
   milestone's exit gate requires the score and the regression test to hold,
   not that every implemented pass be load-bearing in production yet — but
   M3 must not assume insertion/ratchet contributions are already banked
   into the M2 baseline it inherits.
2. **The regression test's tolerance is a decision, not a default.** Naive
   exact-Decimal monotonicity checking on the committed `score_terms` fails
   at ~1e-25 magnitude due to fixed-precision serialization, on data that is
   otherwise correct. `tests/regression/test_monotonicity.py` uses
   `TOLERANCE = 1e-20`, pinned by a second test to stay eleven orders below
   `CLEARANCE_EPS` so it cannot be loosened into masking a real defect.

## M3 kickoff - per-seed wall-clock recording (2026-08-21)

`RunManifest.wall_clock_s` has existed since M1/M2, but `cli.py::_solve` only
ever calls `store_run` once per whole `solve` invocation (one number for all
200 configurations). That was sufficient for M2 (grid + rotation is fast and
deterministic), but `M4-compaction.md` and `M5-small-n.md` both require
"equal wall-clock" comparisons across >=5 seeds, and `M3-lattice.md`'s own
H3.2 calls for five SA seeds "each recorded as its own run in the ledger" -
without a per-seed `wall_clock_s`, those later comparisons would have nothing
to compare against and would require re-running finished searches just to
capture timing that could have been free.

Decision: starting with H3.2, every simulated-annealing seed is stored as its
own `RunManifest` (`run_id` distinguishing the seed) with its own
`perf_counter()`-measured `wall_clock_s`, rather than one aggregate figure for
the whole search. This is a usage-pattern change only - `RunManifest` and
`store_run` already support it - recorded here so it's an explicit decision
rather than something that starts happening silently partway through M3.

## M3 kickoff — per-seed wall-clock recording (2026-08-21)

`RunManifest.wall_clock_s` has existed since M1/M2, but `cli.py::_solve` only
ever calls `store_run` once per whole `solve` invocation (one number for all
200 configurations). That was sufficient for M2 (grid + rotation is fast and
deterministic), but `M4-compaction.md` and `M5-small-n.md` both require
"equal wall-clock" comparisons across ≥5 seeds, and `M3-lattice.md`'s own
H3.2 calls for five SA seeds "each recorded as its own run in the ledger" —
without a per-seed `wall_clock_s`, those later comparisons would have nothing
to compare against and would require re-running finished searches just to
capture timing that could have been free.

Decision: starting with H3.2, every simulated-annealing seed is stored as its
own `RunManifest` (`run_id` distinguishing the seed) with its own
`perf_counter()`-measured `wall_clock_s`, rather than one aggregate figure for
the whole search. This is a usage-pattern change only — `RunManifest` and
`store_run` already support it — recorded here so it's an explicit decision
rather than something that starts happening silently partway through M3.

## M3 — Algorithm selection for the lattice parameter search

### Why simulated annealing over differential evolution

The lattice parameter search is a 5-dimensional continuous optimisation over
`(p, q, h, u, v)` with a hard feasibility barrier (clearance ≥ `CLEARANCE_EPS`).
Three methods were compared head-to-head at an equal 500-evaluation budget on
the lattice objective (shared contract §7; §8.2 records why this comparison was
deferred in an earlier session):

| Method | best ρ | worst ρ |
|---|---|---|
| `dual_annealing` (SA) | **0.6720** | 0.4542 |
| `differential_evolution` | 0.5525 | 0.5176 |
| `basinhopping` (generic local minimiser) | 0.5283 | 0.0000 |

SA has the highest peak density and the highest variance. DE has the lowest
variance. Basin-hopping failed outright on one seed because it was paired with a
generic local minimiser (Nelder-Mead), not a domain-specific one; its value is
the local minimiser, which is why M4 pairs it with compaction rather than using
it here.

Decision: use `dual_annealing`, ≥ 5 seeds, managing variance with seed count
rather than switching to the more consistent but lower-ceiling DE. This session's
five-seed run confirms the approach: seed 4 reached density **0.725241** (above
the 0.60 floor, above the 0.6720 best seen in the head-to-head), all five seeds
feasible, all five stored in `artifacts/lattice_runs/`.

Full five-seed results (2026-08-21):

| Seed | Density | Min clearance | Wall clock |
|---|---|---|---|
| 0 | 0.693730 | 0.001407 | 58.3 s |
| 1 | 0.622670 | 0.004559 | 35.2 s |
| 2 | 0.669979 | 0.009375 | 42.8 s |
| 3 | 0.552120 | 0.002119 | 35.6 s |
| 4 | **0.725241** | 0.0000014 | 43.9 s |

Seed 4 selected as the working basis. Its near-zero clearance (1.4 × 10⁻⁶,
above `CLEARANCE_EPS` = 10⁻⁹) was verified overlap-free against
`reference/evaluator.py` on materialised 7×7 and 9×9 patches before use.

### Why genetic algorithms are rejected

The challenge document suggests genetic algorithms. They are rejected for a
specific structural reason: crossover has no valid semantics for packing.
Splicing the left half of one layout with the right half of another produces
overlaps along the seam in almost every case, so a repair operator dominates
and the genetic operators themselves stop doing work. SA and basin-hopping cover
the same stochastic-search ground with operators that are always valid.

### Why feasibility is decided geometrically, not by index window

An earlier session's lattice search reported density 0.877; `reference/evaluator.py`
measured 0.327 with 29 overlapping pairs (shared contract §8.1). Root cause: the
feasibility check enumerated neighbours over a ±2 lattice-index window. For a
strongly sheared basis the true violating neighbour sat at index offset (4, 2) —
geometrically close but outside the index window. The optimiser did not solve the
packing problem; it found the hole in the constraint set.

Fix (mandatory, implemented in `src/tree_packing/geometry/lattice.py`): enumerate candidate
neighbours by geometric distance (< 1.6 unscaled units) over a Gauss-reduced
basis via `geometry.neighbours.enumerate_neighbour_vectors`. Index windows are
prohibited. This is enforced by the property test in
`tests/property/test_lattice_feasibility.py`, which generates random strongly
sheared bases and cross-checks internal feasibility against a materialised patch
scored by the official evaluator.
