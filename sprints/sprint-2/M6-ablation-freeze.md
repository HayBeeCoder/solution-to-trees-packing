# M6 — Ablation study, figures, and freeze

**Score target:** none. This milestone adds no score and carries several assessment criteria
outright.
**Tag on completion:** `v1.0-submission`
**Estimated effort:** one day. **Not optional.**

Read `00-shared-contract.md` first, particularly §10 (assessment mapping).

---

## Why this milestone exists

The brief states that the panel is *"equally interested in understanding how you think as we
are in the final solution itself"* and that strong candidates *"critically evaluate their
own work and discuss opportunities for improvement."* Those are not satisfied by a low
score. They are satisfied by evidence — and the evidence is an ablation study, a per-`n`
strategy attribution, and an honest ranking of what was left undone.

The ablation is nearly free because of a decision made in M1: runs are immutable and the
ledger is a derived arg-min. Leave-one-out attribution is a **query over stored results**,
not a re-run.

---

## H6 — Primary hypothesis

> Every score claim in the submission can be attributed to a specific component, and every
> component's marginal contribution can be measured from already-stored runs without new
> computation.

**Label:** a complete ablation table with marginal contributions, produced by querying
`artifacts/runs/` and recomputing the ledger arg-min under exclusions.

**Falsified if:** any component's contribution requires a fresh optimisation run to measure.
That would mean the run store is incomplete, which is itself the finding.

---

## Sub-hypotheses

### H6.1 — The harness is frozen before measurement begins

- **Kind:** structural
- **Predicted:** no change to `geometry/`, `validation/`, `scoring.py`, or the evaluator
  invocation for the duration of the milestone.
- **Label:** `git diff v0.7-small-n..HEAD -- src/tree_packing/geometry src/tree_packing/validation src/tree_packing/scoring.py` is empty.
- **Falsified if:** any of those paths changes.

An ablation measured against a moving harness measures nothing. Freeze first, measure second.

### H6.2 — Leave-one-out attribution is a query

- **Kind:** structural
- **Predicted:** excluding any strategy from the ledger arg-min and recomputing the total
  completes in seconds and requires no optimiser invocation.
- **Label:** wall-clock of `tree-packing ablate --exclude <strategy>`.
- **Falsified if:** any exclusion requires re-running a strategy.

Add `tree-packing ablate` reading `artifacts/runs/`. Output shape:

| Component removed | Total score | Marginal cost |
|---|---|---|
| *(none — full portfolio)* | *X* | — |
| Lattice (M3) | *X + a* | *+a* |
| Compaction (M4) | *X + b* | *+b* |
| Global rotation (M2) | *X + c* | *+c* |
| Small-`n` search (M5) | *X + d* | *+d* |

### H6.3 — Post-process contributions interact and must be measured factorially

- **Kind:** empirical
- **Predicted:** the individual contributions of rotation, ratchet and compaction do **not**
  sum to their joint contribution; compaction absorbs a substantial part of what rotation
  would otherwise give.
- **Label:** a 2³ factorial over the three flags at fixed seeds.
- **Falsified if:** individual contributions sum to the joint contribution within `0.5`
  points, meaning the components are genuinely independent.

Either outcome is a result. Independence is the less likely and the more interesting.
One-at-a-time ablation would report both cases identically, which is precisely why the
factorial design is used.

### H6.4 — A proxy configuration set ranks strategies faithfully

- **Kind:** empirical
- **Predicted:** ranking strategies on `n ∈ {1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 200}`
  reproduces the full-200 ranking.
- **Label:** Spearman correlation between proxy and full rankings, over ≥ 4 strategies.
- **Falsified if:** the rankings disagree on any adjacent pair.

If falsified, the proxy needs to be larger — and that is worth knowing and stating, because
every future iteration on this codebase would otherwise be tuning against a misleading
signal.

### H6.5 — Every stochastic claim carries variance

- **Kind:** structural
- **Predicted:** every reported stochastic result has ≥ 5 seeds with median and range.
- **Label:** an audit of the notebook and the results section.
- **Falsified if:** any single-seed result is reported as a finding.

A single lucky seed promoted to a headline is the packing equivalent of reporting
best-of-twenty test accuracy. This audit also applies retroactively to the head-to-head in
shared contract §7, which was run at two seeds and must be either re-run or explicitly
labelled preliminary.

### H6.6 — The figures carry the argument

- **Kind:** structural
- **Predicted:** six figures, committed under `docs/figures/`, each referenced from the
  results section.
- **Label:** files exist, are referenced, and regenerate from a documented command.
- **Falsified if:** any figure cannot be regenerated.

1. Score term `s_n²/n` across all 200, with the theoretical floor `A = 0.245625` and the
   naive baseline as reference lines.
2. Achieved density `ρ_n` against `n`, with the asymptotic lattice density marked.
3. Per-`n` strategy-win heatmap — **the strongest single figure**, because it demonstrates
   the portfolio was necessary rather than assumed.
4. Clearance histogram across all configurations.
5. Score trajectory by milestone tag: `256.82 → 157.99 → … → final`.
6. Rendered layouts for `n ∈ {1, 5, 20, 100, 200}`.

### H6.7 — A clean clone reproduces the submission

- **Kind:** structural
- **Predicted:** `git clone && make submission && make verify` reproduces the exact score on
  a machine that has never seen the project.
- **Label:** execution on a fresh clone in a clean container.
- **Falsified if:** the score differs, or any documented command fails.

This is the last gate before submission and the one most likely to fail, because it exercises
every assumption about the environment that local development hides.

---

## Documentation duties

Beyond the standard duties in shared contract §9, this milestone produces the
interview-facing material:

- **`RESULTS.md`** — new. Executive summary (final score against `256.82` shipped baseline,
  `157.99` competent grid, and the `49.125` floor), the ablation table, the factorial
  interaction result, the six figures, and a ranked list of what would come next with
  expected score delta per engineering day.
- **`DECISIONS.md`** — add the ablation protocol (budget parity, seed counts, proxy
  validation) and the §10 assessment mapping so a reviewer can navigate the repository by
  criterion.
- **`LAB_NOTEBOOK.md`** — a closing entry summarising the refuted hypotheses across all
  milestones. **Refuted predictions are the most valuable content in the notebook** and
  should be easy to find, not buried.
- **`README.md`** — final runbook verified against H6.7.

---

## Interview presentation checklist

Five things to foreground, in this order:

1. **The score identity.** `Score = A · Σ(1/ρ_n)`: the normalisation cancels `n`, so all 200
   configurations carry equal weight. Say this in the first thirty seconds; it demonstrates
   you understood the metric rather than merely optimising against it.
2. **The four-piece exact convex decomposition**, and everything it unlocks — penetration
   depth with analytic gradients, which is what makes compaction a descent.
3. **`SCALE_FACTOR` makes vertices exactly-representable integers.** It does not "add
   precision". This is how `CLEARANCE_EPS = 1e-9` was *derived* rather than guessed.
4. **The bounding box is axis-aligned, so global rotation is free.** `s₁ = 0.813173` at 45°,
   not `1.0`.
5. **The constraint-completeness failure** (shared contract §8.1). An optimiser reported
   density `0.877`; the evaluator measured `0.327` with 29 overlapping pairs; root cause was
   a ±2 lattice-index window missing a violating neighbour at `(4, 2)` under shear; fixed by
   geometric enumeration over a Gauss-reduced basis.

Item 5 is the strongest material available. It shows an optimiser exploiting a hole in a
constraint set, a validation harness catching it, and a specific structural fix — which is
exactly the self-evaluation the brief asks for, evidenced rather than claimed.

---

## Exit gate

- [ ] Harness frozen; the H6.1 diff is empty.
- [ ] Ablation table complete, produced entirely by query.
- [ ] 2³ factorial run and its interaction result recorded.
- [ ] Proxy-set validation performed.
- [ ] Variance audit passed; no single-seed findings reported.
- [ ] Six figures committed and regenerable.
- [ ] **TDD audit:** every structural sub-hypothesis has a `test(...)` commit preceding its
      `feat(...)` commit, and a `Red observed` field in `LAB_NOTEBOOK.md`.
- [ ] **Mutation spot-check** performed on one component and recorded.
- [ ] `RESULTS.md` written.
- [ ] Clean-clone reproduction verified in a fresh container.
- [ ] Final submission CSV committed under `data/submissions/`.
- [ ] `reference/evaluator.py`: zero overlaps, final score recorded everywhere it is quoted.
- [ ] `plans/README.md` all statuses `DONE`.
- [ ] Tagged `v1.0-submission` with the final score in the annotation.

---

## Notes for the executing agent

Reserve this milestone's full day and write no optimiser code during it. The temptation on
the last day is always to chase two more points; resist it. A score of 82 with a rigorous
ablation and an honest failure register will assess better than 78 with a README, because
four of the six named criteria — architecture, maintainability, engineering approach, and
communication — are earned here and nowhere else.
