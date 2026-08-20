# M4 — Compaction and basin-hopping

**Score target:** ≤ 85, from ≤ 110.
**Tag on completion:** `v0.6-compaction`
**Estimated effort:** one and a half to two days.

Read `00-shared-contract.md` first, particularly §7 on why basin-hopping failed once and
what fixes it.

---

## Why this milestone exists

M3 established that boundary loss is roughly 18% at `n = 50` and 6% at `n = 200`. That loss
is not a lattice problem — the lattice interior is already locally optimal by construction —
it is a *ragged edge* problem. Compaction is the tool for ragged edges, and it is the single
most broadly applicable component in the programme: it improves any layout regardless of
which strategy produced it.

The second purpose is to give basin-hopping a fair test. In the head-to-head it was handed a
generic local minimiser and failed outright on one seed. Its entire value is the local
minimiser; paired with compaction it becomes the canonical perturb-and-settle packing
algorithm the challenge document names.

---

## H4 — Primary hypothesis

> Container-shrinking compaction, using the four-piece convex decomposition for penetration
> depth, recovers most of the boundary loss identified in M3; wrapped in basin-hopping it
> reduces the total score below 85.

**Label:** total score from `reference/evaluator.py`; achieved density per `n` compared
against M3's boundary-loss curve.

**Falsified if:** the total exceeds 95, or compaction recovers less than a third of the
measured boundary loss at `n = 50`.

---

## Sub-hypotheses

### H4.1 — Penetration depth is computable and differentiable via the decomposition

- **Kind:** structural
- **Predicted:** for two overlapping trees, the reported depth and direction, applied as a
  translation, separates them to within `1e-12`; for disjoint trees the depth is zero.
- **Label:** `tests/unit/test_penetration.py`, including cases where the overlap involves a
  re-entrant shoulder notch rather than a convex face.
- **Falsified if:** applying the correction fails to separate, or the direction is wrong for
  any notch case.

Sixteen convex–convex tests per tree pair, using M1's four-piece decomposition. The maximum
over pieces gives depth; the corresponding axis gives direction. Both have closed forms for
convex polygons, which is what turns compaction into a descent rather than a random walk.

The notch cases are where a naive implementation breaks. Write those tests first.

### H4.2 — Container-shrinking compaction converges without overlap

- **Kind:** structural
- **Predicted:** from any valid layout, compaction terminates with a valid layout of side
  less than or equal to the input, with clearance ≥ `CLEARANCE_EPS`.
- **Label:** `tests/property/test_compaction_invariants.py` over 100 random valid starts.
- **Falsified if:** it ever returns an invalid layout, or fails to terminate within its
  iteration budget.

Shrink the square container by a small factor, resolve resulting penetrations by moving
trees along the negative gradient of total penetration depth, and repeat until shrinking
fails. Restore the last valid state on failure.

The invariant "never returns invalid" is what allows compaction to be applied unconditionally
as a post-process. It must hold on the property test before compaction is wired anywhere
else.

### H4.3 — Boundary-only compaction is sufficient for lattice layouts

- **Kind:** empirical
- **Predicted:** compacting only trees within `1.6` of the boundary recovers at least 80% of
  what full compaction recovers, at roughly a fifth of the cost at `n = 200`.
- **Label:** score and wall-clock, boundary-only versus full, same layouts.
- **Falsified if:** boundary-only recovers under 50% of the full gain.

Interior lattice trees are already locally optimal, so moving them is mostly wasted work.
If falsified, that is informative in itself — it would mean the lattice interior is *not* at
a local optimum and H3.2's parameters are worth revisiting.

### H4.4 — Basin-hopping with compaction beats compaction alone

- **Kind:** empirical
- **Predicted:** a 3–8 point improvement over pure compaction at equal wall-clock.
- **Label:** total score, ≥ 5 seeds, median with range, equal wall-clock per `n`.
- **Falsified if:** the median improvement is under 1 point, or variance across seeds
  exceeds the improvement.

`scipy.optimize.basinhopping` with compaction as `minimizer_kwargs`, Metropolis acceptance
on the resulting side length. This is the pairing the algorithm was designed for.

**Budget parity is mandatory.** Comparing a 60-second basin-hopping run against a 2-second
compaction run measures compute, not algorithms. State the budget in the notebook entry.

### H4.5 — Aspect rebalancing recovers wasted width

- **Kind:** empirical
- **Predicted:** 1–3 points across all 200 configurations.
- **Label:** score with and without the pass.
- **Falsified if:** under `0.3` of improvement, meaning layouts are already square.

The objective is `max(w, h)²`. A layout measuring `8.0 × 9.0` is scored as `9.0` and throws
away a full unit of width. When `w ≠ h` after compaction, the shorter axis has genuinely
free space: re-seed against a square container of side `max(w, h) − δ` and retry.

### H4.6 — Compaction improves layouts from every strategy

- **Kind:** empirical
- **Predicted:** applying compaction to the M2 grid layouts also improves them, by 5–15
  points.
- **Label:** M2 layouts before and after compaction.
- **Falsified if:** the grid improves by under 2 points.

This is a check that compaction is genuinely general rather than tuned to lattice output. It
also produces a second independent strategy line for M6's per-`n` heatmap, which is what
demonstrates the portfolio was necessary rather than assumed.

---

## Exit gate

- [ ] Gate green.
- [ ] Compaction never returns an invalid layout across 100 random starts.
- [ ] Penetration tests pass, including all shoulder-notch cases.
- [ ] `reference/evaluator.py`: zero overlaps, total ≤ 85.
- [ ] Minimum clearance ≥ `CLEARANCE_EPS` everywhere.
- [ ] Basin-hopping run at ≥ 5 seeds with equal wall-clock; median and range recorded.
- [ ] Boundary-loss recovery measured against M3's curve and recorded.
- [ ] `artifacts/best_scores.json` updated; Regression Gate green.
- [ ] **TDD audit:** every structural sub-hypothesis has a `test(...)` commit preceding its
      `feat(...)` commit, and a `Red observed` field in `LAB_NOTEBOOK.md`.
- [ ] **Mutation spot-check** performed on one component and recorded.
- [ ] `DECISIONS.md`: why basin-hopping's local minimiser is the whole point, citing the
      earlier failure where a generic minimiser produced a zero-density seed.
- [ ] Tagged `v0.6-compaction`.

---

## Notes for the executing agent

Compaction is where floating-point discipline earns its keep. Trees will be driven into near
contact deliberately, so `CLEARANCE_EPS` stops being a comfortable margin and becomes the
active constraint. Two rules:

- Compaction runs on the fast geometry path; **every** promoted result is re-validated
  through `geometry.core` on the serialised CSV. The two-tier rule is not negotiable here.
- Watch the clearance histogram, not only the minimum. A layout whose clearances cluster at
  `1e-9` is at the constraint boundary everywhere and is fragile; one with a long tail above
  `1e-6` has room. Both pass the gate; they are not equally good.
