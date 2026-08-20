# Implementation decisions

## Faithful port over reinvention

The constants and polygon vertices are copied from the supplied evaluator. The
geometry is defined once in `geometry.py`, then reused by scoring and validation,
so the internal gatekeeper cannot silently disagree with the official evaluator.

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
