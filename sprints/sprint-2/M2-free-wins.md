# M2 — Tight grid and the universal post-processes

**Score target:** ≤ 160, from `256.8197…`.
**Tag on completion:** `v0.4-free-wins`
**Estimated effort:** one day.

Read `00-shared-contract.md` first, particularly §5.1 (the score identity) and §6
(promotion rule).

---

## Why this milestone exists, and why it precedes the lattice

Everything here is cheap, deterministic, and applies to *every* layout the programme will
ever produce. If M3's lattice is built first, the lattice appears to deliver gains that the
global rotation pass actually paid for, and M6's ablation is confounded before it starts.
Ordering is a measurement decision, not a convenience.

This is also the milestone that establishes the **honest baseline**. Reporting a final
improvement against the artificially sparse `1.1`-pitch grid would overstate the result; a
senior reviewer will notice. The comparison that matters is against a competent grid, and
that number is `157.986`.

---

## H2 — Primary hypothesis

> A tight rectangular grid plus three deterministic post-processes — global rotation,
> upward insertion, and the downward ratchet — reduces the total score below 160 with no
> stochastic search whatsoever.

**Label:** `tree-packing solve` output scored by `reference/evaluator.py`, zero overlaps,
minimum clearance ≥ `CLEARANCE_EPS` for all 200 configurations.

**Falsified if:** the total exceeds 165, or any configuration fails the gatekeeper.

---

## Sub-hypotheses

### H2.1 — The strategy interface supports a portfolio without special cases

- **Kind:** structural
- **Predicted:** the grid baseline, re-expressed as a `Strategy`, reproduces
  `256.8197122633766779770234` exactly.
- **Label:** `tests/unit/test_strategy_registry.py` plus a full-run score comparison.
- **Falsified if:** the re-expressed baseline scores differently by any amount.

Define in `optimize/base.py`:

```python
class Strategy(Protocol):
    name: str
    def solve(self, n: int, ctx: SolveContext) -> Layout | None: ...
```

Returning `None` means "this strategy does not apply at this `n`" — the mechanism by which
M5's small-`n` search and M3's lattice coexist without either knowing about the other. A
registry maps names to instances; the CLI's `solve` command runs the requested set and
promotes results through the ledger.

Wrapping the existing baseline as the first `Strategy` is the test of the interface. If the
abstraction requires the baseline to change, the abstraction is wrong.

### H2.2 — A tight rectangular grid scores 157.986

- **Kind:** empirical
- **Predicted:** `157.986`, ± `0.01`.
- **Label:** total score from `reference/evaluator.py`.
- **Falsified if:** the result differs by more than `0.5`, or any overlap appears.

For each `n`, choose the column count `c` minimising `max(c · 0.7, ⌈n/c⌉ · 1.0)`; place
trees on a `0.7 × 1.0` pitch centred on the origin, plus `CLEARANCE_EPS`. The tree's
axis-aligned extents are exactly `0.7 × 1.0`, so this is the densest possible axis-aligned
non-rotated arrangement.

This is a strong test of the whole measurement chain: it is a closed-form prediction with no
free parameters, computed independently of the implementation. If the implementation
disagrees with `157.986`, the implementation is wrong.

### H2.3 — Global rotation is a free scalar, worth exactly 0.33875 at n = 1

- **Kind:** empirical
- **Predicted:** `n = 1` term falls from `1.0` to `0.66125`; `s₁ = 0.81317279836452966`
  at `45.0°`. Total improvement across all 200 configurations: 1–4 points.
- **Label:** per-configuration score terms from the gatekeeper.
- **Falsified if:** the `n = 1` term is not `0.66125` to six decimal places.

The bounding box is axis-aligned, so rotating an entire layout by `θ ∈ [0°, 90°)` is a free
scalar to minimise. Implement `postprocess/rotation.py` with a coarse sweep followed by
golden-section refinement, applied to every layout before promotion.

The `n = 1` value was measured against this repository's own `geometry.py` and is exact to
the precision shown. It is the canary for the whole submission: a pipeline that does not
find it is not searching orientation at all.

Note that rotation gains are largest at small `n` and shrink as the layout approaches
square. Expect most of the benefit below `n ≈ 10`.

### H2.4 — Upward insertion sometimes costs nothing

- **Kind:** empirical
- **Predicted:** for at least 15 of 200 configurations, tree `n+1` fits inside the existing
  square, giving `s_{n+1} = s_n` and a term reduction of `n/(n+1)`.
- **Label:** count of zero-growth insertions, logged per run.
- **Falsified if:** fewer than 5 configurations admit a zero-growth insertion.

The challenge document's fourth tip suggests exactly this. Implement
`postprocess/insertion.py`: given a valid `n`-layout, search the feasible region inside its
existing bounding square for a placement of one more tree. Chain while it keeps succeeding.

This pass cannot produce an invalid layout — it only adds to a configuration already known
feasible — which makes it the safest score in the programme.

The predicted count is genuinely uncertain and depends on how ragged the grid's corners
are. Record the actual count; it is a useful input to M3's truncation design.

### H2.5 — The downward ratchet propagates improvements for free

- **Kind:** structural
- **Predicted:** after the pass, `s_n ≤ s_{n+1}` holds for all `n`, and no configuration's
  score term increases.
- **Label:** `tests/regression/test_monotonicity.py`.
- **Falsified if:** monotonicity fails anywhere, or any term regresses.

A valid `n+1` layout contains a valid `n` layout by deleting a tree, so `s_n ≤ s_{n+1}` is a
theorem, not an aspiration — a violation means the ledger holds a worse-than-necessary
solution somewhere. Implement `postprocess/ratchet.py`: for each `n`, take the best layout
of any `m > n`, delete the `(m − n)` trees contributing most to the extremal boundary, then
re-run rotation.

Run both directions and let the ledger take the arg-min. Insertion and the ratchet find
different things.

### H2.6 — The regression gate makes the score monotone across the project

- **Kind:** structural
- **Predicted:** CI fails on a deliberately introduced score regression.
- **Label:** manual falsification — push a branch with a worsened constant, confirm CI red,
  revert.
- **Falsified if:** CI passes with the regression present.

Commit `artifacts/best_scores.json` with M2's per-configuration terms and total. Wire the
Regression Gate (shared contract §4) into the CI job created in M0. Perform the
falsification check and record it. From this milestone on, the total score can never
silently increase — which is what protects M3–M5 from late refactors.

---

## Exit gate

- [ ] Gate green, including `lint-imports`.
- [ ] `uv run tree-packing solve --output data/submissions/current.csv` succeeds.
- [ ] `reference/evaluator.py` accepts it, zero overlaps, total ≤ 160.
- [ ] Minimum clearance ≥ `CLEARANCE_EPS` for all 200 configurations.
- [ ] `n = 1` term is exactly `0.66125`.
- [ ] Monotonicity `s_n ≤ s_{n+1}` holds for all `n`.
- [ ] `artifacts/best_scores.json` committed; Regression Gate live in CI and falsified once.
- [ ] Zero-growth insertion count recorded in the notebook.
- [ ] **TDD audit:** every structural sub-hypothesis has a `test(...)` commit preceding its
      `feat(...)` commit, and a `Red observed` field in `LAB_NOTEBOOK.md`.
- [ ] **Mutation spot-check** performed on one component and recorded.
- [ ] `LAB_NOTEBOOK.md` entries for H2.1–H2.6, each with predicted and actual side by side.
- [ ] `DECISIONS.md`: why M2 precedes M3 (measurement confounding); why the honest baseline
      is `157.986` rather than `256.82`.
- [ ] Tagged `v0.4-free-wins` with the score in the annotation.

---

## Notes for the executing agent

H2.2 is a closed-form prediction and H2.3 is exact to sixteen digits. Together they
constitute an end-to-end test of the measurement chain built in M0 and M1. If either misses,
do not proceed to M3 — a measurement chain that cannot reproduce a closed-form answer cannot
be trusted to evaluate a stochastic one.

H2.4's prediction is the weakest in this milestone and is expected to be the one that
misses. That is fine. Record the actual number and treat it as data for M3.
