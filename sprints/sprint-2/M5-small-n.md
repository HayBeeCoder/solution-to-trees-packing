# M5 — Dedicated search for n ≤ 20

**Score target:** ≤ 82, from ≤ 85.
**Tag on completion:** `v0.7-small-n`
**Estimated effort:** one day. **This milestone is optional under time pressure.**

Read `00-shared-contract.md` first, particularly §5.1 and §6 on canonicalisation.

---

## Why this milestone exists, and why it is optional

Small `n` are structurally the worst configurations. The grid baseline achieves `ρ₁ = 0.246`
against an asymptotic `0.57`+, because boundary effects dominate when there is almost
nothing *but* boundary. They are also the configurations where near-optimality is actually
reachable: at `n ≤ 20` the search space is 60 dimensions, not 600, and exhaustive or
near-exhaustive methods apply.

But there are only 20 of them, and the score identity weights every configuration equally.
The total available here is a few points, against the 180 configurations M3 and M4 address.
Absolute slack is punished ~17.5× harder at `n = 1` than at `n = 200`
(`∂(s_n²/n)/∂s = 2s_n/n ∝ n^{-1/2}`), which is why the gains are real — but they are
bounded.

Ship M6 over M5 if the calendar is tight. A polished ablation study is worth more to the
assessment than two points of score.

---

## H5 — Primary hypothesis

> For `n ≤ 20`, symmetric seeding plus basin-hopping with compaction achieves densities
> materially above what the lattice-plus-post-process pipeline produces, reducing the total
> by 2–4 points.

**Label:** per-configuration score terms for `n ∈ [1, 20]`, before and after.

**Falsified if:** the improvement across all twenty configurations is under `0.5` points.

---

## Sub-hypotheses

### H5.1 — n ≤ 3 can be solved to near-provable optimality

- **Kind:** empirical
- **Predicted:** `n = 1` term is exactly `0.66125` (already established in M2 and not
  improvable — it is the true minimal enclosing square of a single tree). `n = 2` and
  `n = 3` improve by at least 5% over the M4 pipeline.
- **Label:** exhaustive search on a fine `(angle, position)` grid, then continuous polish;
  compared against M4's terms.
- **Falsified if:** exhaustive search fails to beat the pipeline at `n = 2` or `n = 3`,
  which would suggest the pipeline is already optimal there.

At `n ≤ 3` the space is small enough for a grid search fine enough to be convincing.
Document the grid resolution and the resulting confidence — "exhaustive to 0.1° and 0.001
units" is a defensible claim; "optimal" is not.

### H5.2 — Symmetric seeding halves the search space and helps

- **Kind:** empirical
- **Predicted:** mirror-symmetric seeds reach a given score in roughly half the evaluations
  of random seeds, for at least half the `n` in `[4, 20]`.
- **Label:** evaluations-to-target, symmetric versus random seeding, ≥ 5 seeds each.
- **Falsified if:** symmetric seeding is not faster for any `n`.

The tree is mirror-symmetric about `x = 0` (verified in M1), so constraining a layout to be
mirror-symmetric reduces variables from `3n` to roughly `3⌈n/2⌉` — 60 to 33 at `n = 20`. Odd
`n` places one tree on the axis.

**Use it as a seed generator, not a constraint.** Optimal packings frequently break
symmetry, so a symmetric layout is a good starting point and a bad final answer. The
distinction matters: constrain the search and you will systematically miss the optimum.

### H5.3 — Multi-start basin-hopping beats a single long run

- **Kind:** empirical
- **Predicted:** 20 starts of budget `B/20` beat one start of budget `B`, at equal total
  wall-clock, for most `n` in `[4, 20]`.
- **Label:** best-of-run score at equal wall-clock, ≥ 5 seeds.
- **Falsified if:** the single long run wins for more than half the `n` tested.

Small-`n` packing landscapes are rugged with many shallow basins; breadth usually beats
depth. If falsified, that is a genuine finding about the landscape and belongs in the
write-up.

### H5.4 — Canonicalisation prevents duplicate-optimum waste

- **Kind:** structural
- **Predicted:** with canonicalisation on, distinct solutions found per `n` drops
  noticeably, while best score is unchanged.
- **Label:** count of distinct canonical layouts, with and without.
- **Falsified if:** canonicalisation changes the best score at any `n` — it must not, since
  a mirror twin scores identically.

Every layout has a mirror twin with identical score (shared contract §6). Without
canonicalisation, multi-start rediscovers twins and the M6 ablation counts them as distinct
solutions.

The falsification condition is the important one here: if canonicalisation changes a score,
the canonicalisation is buggy.

---

## Exit gate

- [ ] Gate green.
- [ ] `reference/evaluator.py`: zero overlaps, total ≤ 82.
- [ ] `n = 1` term remains exactly `0.66125`.
- [ ] Minimum clearance ≥ `CLEARANCE_EPS` everywhere.
- [ ] Search resolution for `n ≤ 3` documented with an explicit confidence claim.
- [ ] Symmetric-versus-random seeding comparison recorded, ≥ 5 seeds.
- [ ] Canonicalisation verified score-neutral at every `n`.
- [ ] `artifacts/best_scores.json` updated; Regression Gate green.
- [ ] **TDD audit:** every structural sub-hypothesis has a `test(...)` commit preceding its
      `feat(...)` commit, and a `Red observed` field in `LAB_NOTEBOOK.md`.
- [ ] **Mutation spot-check** performed on one component and recorded.
- [ ] `DECISIONS.md`: symmetry as seed rather than constraint, and why.
- [ ] Tagged `v0.7-small-n`.

---

## Notes for the executing agent

If time is short, the highest-value fragment of this milestone is H5.1 alone — `n ≤ 3` is a
few hours of work and produces the cleanest claim in the entire submission: near-provable
optimality on a subset, with a stated search resolution. That is worth more in the interview
than a slightly better aggregate score with no provable component.

Do not let `n = 1` regress. It is exactly `0.66125` and any change means a bug upstream.
