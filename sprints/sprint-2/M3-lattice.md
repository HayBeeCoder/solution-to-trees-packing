# M3 — The double-lattice backbone

**Score target:** ≤ 110, from ≤ 160.
**Tag on completion:** `v0.5-lattice`
**Estimated effort:** two days. This is the largest single win in the programme.

Read `00-shared-contract.md` first, particularly §7 (algorithm selection) and §8.1 (the
constraint-completeness failure, which happened on exactly this sub-problem).

---

## Why this milestone exists

180 of the 200 configurations have `n ≥ 21`. Because the score identity gives every
configuration equal weight (shared contract §5.1), those 180 dominate the total. A
parametric lattice searches **five** continuous parameters regardless of whether `n` is 21
or 200, instead of `3n = 600` raw degrees of freedom — and its interior feasibility is
proved once on the fundamental cell rather than re-checked per tree.

The corollary is that all remaining loss moves to the boundary, and the boundary is where
the difficulty goes. Plan for that: H3.4 is not an afterthought.

---

## H3 — Primary hypothesis

> A double lattice of upright and 180°-inverted trees, with parameters found by simulated
> annealing, achieves an asymptotic density of at least `0.60` and reduces the total score
> below 110 when truncated to a square window and boundary-compacted.

**Label:** total score from `reference/evaluator.py`; per-configuration achieved density.

**Falsified if:** asymptotic density is below `0.55`, or the total exceeds 120.

**Anomaly watch.** If measured density exceeds `0.75`, treat the result as Anomalous (shared
contract §2.4) and materialise before believing it. A density of `0.877` was reported once
by an optimiser exploiting a hole in the constraint set; the evaluator measured `0.327`.

---

## Sub-hypotheses

### H3.1 — Feasibility of a lattice is decided on the fundamental cell

- **Kind:** structural
- **Predicted:** a lattice passing the internal feasibility check also passes
  `reference/evaluator.py` on a materialised 7 × 7 patch, for every basis tested including
  strongly sheared ones.
- **Label:** `tests/property/test_lattice_feasibility.py` — generate random bases, check
  internally, materialise, cross-check.
- **Falsified if:** any internally-feasible lattice produces an overlap on the patch.

This is the single most important test in the milestone. It is the direct guard against the
§8.1 failure, and it must use `geometry.neighbours` from M1 — geometric distance over a
Gauss-reduced basis, never an index window.

Parameterise as `a = (p, 0)`, `b = (q, h)` with `p, h > 0` (without loss of generality),
plus the inverted partner offset `(u, v)`. Five parameters. Density is `2A / (p·h)`.

Exploit the mirror symmetry established in M1: `mirror(rot θ) ≡ rot(−θ)`, so the pair
`(θ₁, θ₂)` and `(−θ₁, −θ₂)` share a no-fit polygon. Upright-versus-inverted is the only
genuinely distinct pairing class, which is *why* the double lattice is the natural motif
rather than an arbitrary choice.

### H3.2 — Simulated annealing finds a lattice with density ≥ 0.60

- **Kind:** empirical
- **Predicted:** best-of-five-seeds asymptotic density ≥ `0.60`; median ≥ `0.55`.
  A feasible lattice at `0.6054` has already been found and evaluator-verified, so `0.60`
  is a floor, not a stretch.
- **Label:** cell density from the search, then confirmed by materialisation.
- **Falsified if:** best-of-five is below `0.55`.

Use `scipy.optimize.dual_annealing`, five seeds minimum, each recorded as its own run in the
ledger. SA had the highest peak *and* the highest variance in the head-to-head (shared
contract §7); manage that with seed count, not by switching method.

Include an explicit clearance term in the objective so the optimum lands at
`CLEARANCE_EPS` rather than at exact contact. A previous search reached density `0.7086` at
an overlap area of `1.9e-9` — mathematically touching, practically invalid — and its
parameters were lost because there was no run store. Both problems are fixed here: the
clearance term prevents the first, the M1 ledger prevents the second.

### H3.3 — Window truncation is a searchable sub-problem

- **Kind:** structural
- **Predicted:** for each `n`, sliding a square window over the infinite tiling and
  binary-searching its side yields a valid `n`-tree selection.
- **Label:** `tests/unit/test_truncation.py` — every `n` in `21..200` yields exactly `n`
  trees with no overlaps.
- **Falsified if:** any `n` fails to produce a valid selection.

Selecting which `n` cells of an infinite tiling to occupy is discrete. Slide a candidate
square over the tiling, count fully-contained trees, binary-search the side, then refine
the choice of *which* trees with simulated annealing over swap moves — there is no
continuous local minimiser here, which is why basin-hopping does not apply and SA does.

### H3.4 — Boundary loss is large, n-dependent, and worth attacking

- **Kind:** empirical
- **Predicted:** achieved density falls well short of the asymptotic value, by roughly 18%
  at `n = 50` and 6% at `n = 200`.
- **Label:** achieved density per `n`, compared against the cell density.
- **Falsified if:** the gap is under 3% at `n = 50` — which would mean truncation is
  already near-optimal and M4's boundary work is unnecessary.

Measured evidence from a `0.6054` lattice, evaluator-verified with zero overlaps:

| n | side | term `s_n²/n` | achieved ρ | loss vs `0.6054` |
|---|---|---|---|---|
| 50 | `4.97103` | `0.49422` | `0.4970` | 18% |
| 100 | `7.00324` | `0.49045` | `0.5008` | 17% |
| 200 | `9.28306` | `0.43088` | `0.5701` | 6% |

Two things to read from this. Boundary loss shrinks as `n` grows, exactly as the
surface-to-area ratio predicts. And the `n = 200` term is *better* than `n = 100`'s,
meaning truncation quality is lumpy rather than smooth — some `n` land on clean window
boundaries and some do not. That lumpiness is the target of M4's boundary compaction.

**Record the per-`n` loss curve.** It is the input that sizes M4, and it makes an excellent
figure for M6.

### H3.5 — Interior trees need no per-tree validation

- **Kind:** structural
- **Predicted:** validating only trees within `1.6` of the window boundary gives the same
  verdict as validating all pairs, at a fraction of the cost.
- **Label:** `tests/property/test_interior_shortcut.py` — both methods agree on 200 random
  truncations.
- **Falsified if:** the verdicts ever differ.

Interior trees are feasible by construction from H3.1. This is what makes `n = 200`
tractable. The final gatekeeper still validates every pair on the serialised CSV — the
shortcut is a search optimisation, never a validation one.

### H3.6 — The lattice composes with M2's post-processes

- **Kind:** empirical
- **Predicted:** applying rotation, insertion and the ratchet to lattice layouts yields a
  further 2–6 point improvement over the raw lattice.
- **Label:** total score with and without the post-process pass, same lattice, same seeds.
- **Falsified if:** the post-processes produce less than `0.5` of improvement, which would
  indicate the lattice already sits at a rotational optimum.

This is a genuine ablation and its result goes straight into M6's table. Run it as a
controlled pair: one variable, two runs.

---

## Exit gate

- [ ] Gate green.
- [ ] `test_lattice_feasibility.py` passes on strongly sheared random bases.
- [ ] Best-of-five-seeds asymptotic density ≥ `0.60`, all five runs in the ledger.
- [ ] Every `n` in `21..200` yields a valid truncation.
- [ ] `reference/evaluator.py`: zero overlaps, total ≤ 110.
- [ ] Minimum clearance ≥ `CLEARANCE_EPS` everywhere.
- [ ] Per-`n` boundary-loss curve recorded in the notebook.
- [ ] H3.6's controlled pair run and recorded.
- [ ] `artifacts/best_scores.json` updated; Regression Gate green.
- [ ] **TDD audit:** every structural sub-hypothesis has a `test(...)` commit preceding its
      `feat(...)` commit, and a `Red observed` field in `LAB_NOTEBOOK.md`.
- [ ] **Mutation spot-check** performed on one component and recorded.
- [ ] `DECISIONS.md`: why SA over DE (with the head-to-head numbers); why GA was rejected;
      why feasibility is decided geometrically rather than by index window, citing §8.1.
- [ ] Tagged `v0.5-lattice`.

---

## Notes for the executing agent

Two failure modes have already occurred on this exact sub-problem. Both are cheap to
re-introduce and expensive to detect:

1. **Believing the optimiser's own density.** Materialise and cross-check with the official
   evaluator before promoting anything. The internal number is a hypothesis; the evaluator's
   is the label.
2. **Losing good parameters.** Every run — including refuted ones — goes into the ledger
   with its full parameter set. The `0.7086` result is gone forever because it was printed
   rather than stored.

If SA plateaus near `0.583`, that is the Kuperberg double-lattice bound applied to the
tree's **convex hull** (`√3/2 × 0.673`). Hitting it means the lattice is packing hulls, not
trees, and the next hypothesis writes itself: exploit the two re-entrant shoulder notches at
`y = 0.25` and `y = 0.5` so a neighbour's tier seats into them. The already-verified
`0.6054` exceeds that bound, so some interlocking is being found — the question is how much
more is available.
