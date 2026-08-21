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
