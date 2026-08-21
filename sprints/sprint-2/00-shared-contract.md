# Shared Contract — binding on every milestone

This document holds the rules, values, schemas, and conventions that apply to all
milestones. Milestone documents assume it and do not repeat it. Read it before M0.

---

## 0. Scope of the programme

### In scope

- A packing optimiser for all 200 configurations, replacing the deterministic grid.
- A run ledger that makes solutions reproducible, restartable, and comparable.
- An ablation study over stored runs (M6).
- Incremental updates to `README.md`, `DECISIONS.md`, `LAB_NOTEBOOK.md`, and
  `baseline-breakdown.md` at every milestone.

### Explicitly out of scope

- Any modification to `reference/evaluator.py`, `reference/simple_algorithm.py`,
  `reference/christmas_tree_packing_challenge.md`, or `reference/sample_solution.csv`.
  These are the ground truth and must remain byte-identical to the supplied files.
- Any change to the submission format, the coordinate bounds, or the scoring formula.
- Genetic algorithms over the raw placement genome (see §7, rejected with reasons).
- CMA-ES or any optimiser requiring a dependency outside `scipy` (see §7).

---

## 1. Guiding principles

These extend, and do not replace, the five principles in the root `plan.md`.

1. **Two-tier geometry, one direction of trust.** A fast NumPy path exists for *search*;
   the Shapely path in `geometry/` remains authoritative for *validation and scoring*. The
   fast path may never decide validity. This rule is the single most important structural
   constraint in the programme and is enforced by an import-linter rule in M1.
2. **Always shippable.** After every milestone the repository must be one command away
   from a valid, scored, submittable CSV. The score may only ever go down.
3. **Runs are immutable; the ledger is derived.** A strategy run is never overwritten. The
   best-known solution is the arg-min over stored runs. This is what makes M6's ablation a
   query rather than a re-run.
4. **Validate after serialisation, never before.** Two lossy conversions sit between the
   optimiser's in-memory floats and the geometry that gets scored
   (`float → str → float → Decimal`). The gatekeeper reads the written CSV from disk.
5. **One hypothesis, one variable.** If a run changes two things, it has measured nothing.
6. **No hidden state.** Strategies are pure functions of `(n, config, seed)`. Every
   stochastic component takes an explicit seed recorded in the run manifest.
7. **Red before green, then refactor.** No implementation code is written before a test
   exists, has been **run**, and has been **observed failing** for the expected reason. The
   observed failure message is recorded in the notebook. Once green, the refactor step is
   mandatory, not optional. This is the TDD half of §2 and it is auditable — see §2.5.

---

## 2. Operating methodology — "Agentic Coding is Science", with sub-hypotheses

The root `plan.md` §1a defines the six-step loop and the rules of engagement. They carry
over, with one step **split** (see §2.0). Two extensions apply to the optimiser, because
optimiser work differs from porting work in one crucial respect: **there is no longer a
known-correct answer to port against.** The evaluator can tell us whether a layout is
*valid*, and what it *scores*, but not whether a better layout exists. Hypotheses therefore
become genuinely falsifiable rather than merely confirmatory, and must be stated with
predicted numbers.

### 2.0 The loop, with GENERATE split for TDD

The root plan's `GENERATE` step reads "produce the candidate module/tests" — module and
tests together. That is compatible with writing the implementation first and the test
afterwards, which is not test-driven development. For structural sub-hypotheses the step is
split into three, giving an eight-step loop:

| # | Step | What happens | Evidence recorded |
|---|---|---|---|
| 1 | **HYPOTHESIZE** | State the claim, its kind, and the label that decides it | Claim + label |
| 2 | **GENERATE-TEST** | Write the test **only**. No implementation | Test file path |
| 3 | **OBSERVE-RED** | Run it. Confirm it fails, **and fails for the expected reason** | The failure message, verbatim |
| 4 | **GENERATE-CODE** | Write the minimum implementation that could pass | Files touched |
| 5 | **OBSERVE-GREEN** | Run the Gate | Pass counts, timings |
| 6 | **REFACTOR** | Clean up under green tests: naming, duplication, boundaries | What changed, or "none needed" |
| 7 | **MEASURE / SELECT** | Compare traces to the label; keep only if fully green | Label result |
| 8 | **REFINE** | On failure, diagnose *why the hypothesis was wrong*, restate, return to 1 | Root cause |

Step 3 is the one most easily skipped and the one that carries the most information. A test
that has never been red proves nothing — it may be asserting a tautology, testing the wrong
module, or silently skipped by a collection error. **Confirm the failure reason, not merely
the failure.** A test failing with `ImportError` is not evidence that the assertion is
sound.

Step 6 exists because red-green alone produces working code that accumulates duplication.
"No spaghetti" is a property maintained continuously under green tests, not one restored in
a cleanup pass at the end. If nothing needs refactoring, record `none needed` — an empty
answer is a valid observation, an absent one is a skipped step.

**Empirical sub-hypotheses use steps 1, 4–8 only.** You cannot write a failing test for "SA
reaches density 0.60" — the equivalent discipline is the mandatory `Falsified if` clause in
§2.2, which fixes the refutation condition before the measurement is taken, exactly as
`OBSERVE-RED` fixes it before the implementation is written.

Prefix each working turn with the current step, e.g. `**[OBSERVE-RED]**`, extending the root
plan's rule of engagement.

### 2.1 Hypothesis structure

Each milestone carries one **primary hypothesis** (H*n*) decomposed into **sub-hypotheses**
(H*n*.1, H*n*.2, …). A sub-hypothesis is the unit of the six-step loop: one test file, one
implementation, one notebook entry, one commit. The primary hypothesis is only settled when
every sub-hypothesis is green *and* the milestone exit gate passes.

Sub-hypotheses come in two kinds, and they are labelled differently:

- **Structural** — "this component behaves as specified". Label: a named test file with
  exact expected values. These are the TDD units. Failure means a bug.
- **Empirical** — "this approach achieves *X*". Label: a measured number from the official
  evaluator, with a stated prediction. Failure means the *hypothesis* was wrong, which is a
  result, not a bug. Record it and refine; do not quietly retune until it passes.

Distinguishing these is not bookkeeping. Treating an empirical failure as a bug leads to
tuning against a specific measurement until it passes, which is overfitting.

### 2.2 Sub-hypothesis template

```markdown
### H<n>.<k> — <one-line claim>

- **Kind:** structural | empirical
- **Predicted:** <exact value, or predicted range with units>
- **Label:** <test file / gate / measured quantity that decides it>
- **Falsified if:** <the concrete observation that would refute it>
```

`Falsified if` is mandatory on empirical sub-hypotheses. A hypothesis with no stated
refutation condition is not a hypothesis.

### 2.3 Notebook entry template (extends the root plan's template)

```markdown
## M<n>.<k> — <component / concern>

- **Hypothesis:** <claim> — kind: <structural|empirical>, label: <label>
- **Predicted:** <number or range>
- **Test written:** <test file path>                      # structural only
- **Red observed:** <verbatim failure message, and why it is the expected reason>
- **Generated:** <files touched>
- **Green observed:** <pass counts, timings>
- **Refactored:** <what changed under green tests, or "none needed">
- **Measured:** <label result; for empirical, predicted vs actual side by side>
- **Selected / Refined:** <kept / rejected + root cause + corrected hypothesis>
```

`Red observed` is mandatory on every structural entry and is what makes the TDD claim
auditable rather than asserted. Omit the field and the entry is incomplete; write
"not observed" and the sub-hypothesis is not done.

For empirical entries, drop `Test written`, `Red observed` and `Green observed`, and always
record predicted and actual side by side, **including when the prediction was wrong**. A
notebook of only confirmed predictions is not evidence of method; it is evidence of
retrospective editing.

### 2.4 Result classes at MEASURE

Three outcomes must be distinguished, because they demand different responses:

| Class | Meaning | Response |
|---|---|---|
| **Confirmed** | Improvement, for the predicted reason | Select; proceed |
| **Anomalous** | Improvement, for a *different* reason than predicted | **Investigate before selecting.** Usually a measurement artefact or a constraint hole |
| **Refuted** | No improvement, or prediction missed | Record; refine; do not retune silently |

The Anomalous class exists because of a real incident in this project's history: an
optimiser reported a lattice density of `0.877` while the official evaluator measured
`0.327` with 29 overlapping pairs. The improvement was real in the optimiser's own terms
and entirely fictional in the evaluator's. See §8.

### 2.5 TDD is auditable, not asserted

A methodology built on falsifiability cannot contain an unfalsifiable claim about its own
process. "We practised TDD" must be checkable from the repository by someone who was not
present. Three mechanisms make it so, and all three are part of every milestone's exit gate:

**Commit granularity.** Each structural sub-hypothesis produces **two commits**:

```
test(M1.4): add lattice neighbour enumeration regression case   # red
feat(M1.4): enumerate neighbours by distance over reduced basis # green
```

The test commit contains only files under `tests/`. This is the strongest available
evidence — `git log --diff-filter=A --name-only` shows, per sub-hypothesis, that the test
file existed before the implementation. Refactoring goes in a third commit
(`refactor(M1.4): …`) when there is anything to record.

**Notebook `Red observed` fields.** Every structural entry carries the verbatim failure
message from step 3. The exit-gate check is mechanical: the count of `Red observed` fields
in `LAB_NOTEBOOK.md` equals the count of structural sub-hypotheses in the milestone.

**Mutation spot-check, once per milestone.** Pick one component. Introduce a deliberate
defect — flip a comparison, drop a term, return a constant. Confirm the suite goes red.
Revert. Record it. This tests the tests, which nothing else in the programme does: a suite
that stays green under a real defect is decorative regardless of its coverage number, and
coverage percentage measures execution, not assertion.

One caveat worth stating in `DECISIONS.md` rather than hiding: the existing 27 tests were
written alongside their modules during the scaffolding phase, not test-first. Claiming
retrospective TDD for them would be false. The honest position is that TDD begins at M0 and
is auditable from that tag forward — and a reviewer who checks will find the claim matches
the history exactly, which is worth considerably more than an unverifiable claim about the
whole repository.

---

## 3. Target repository layout

The current flat `src/tree_packing/*.py` layout is correct for eight modules and would
become spaghetti at twenty-five. The optimiser is introduced as sub-packages with explicit
boundaries. **Public import paths of existing modules must not change** — `geometry.py`
becomes `geometry/` with re-exports in `__init__.py`, so `from tree_packing.geometry import
create_tree_polygon` continues to work and no existing test needs editing.

```text
src/tree_packing/
    __init__.py
    config.py                  # unchanged; extended with optimiser constants
    py.typed

    geometry/                  # M1 — the Geometric Core
        __init__.py            # re-exports create_tree_polygon, tree_vertices
        core.py                # moved verbatim from geometry.py; AUTHORITATIVE
        fast.py                # NumPy vertex transform; SEARCH ONLY
        decomposition.py       # exact 4-piece convex decomposition
        neighbours.py          # circumradius + Gauss-reduced lattice enumeration

    scoring.py                 # unchanged
    serialization.py           # unchanged
    baseline.py                # unchanged; kept as the reference point

    validation/                # M1 — the Defensive Gatekeeper
        __init__.py            # re-exports find_overlapping_pairs, has_overlap, …
        overlap.py             # moved verbatim from validation.py
        clearance.py           # minimum pairwise separation reporting
        gatekeeper.py          # end-to-end check of a CSV read back from disk

    optimize/                  # M2+ — the Optimisation Engine
        __init__.py
        types.py               # Layout, Placement, StrategyResult (all frozen)
        base.py                # Strategy protocol + registry
        ledger.py              # immutable run store + derived arg-min
        postprocess/           # M2 — universal passes
            rotation.py
            insertion.py
            ratchet.py
        strategies/
            grid.py            # M2 — tight rectangular grid
            lattice.py         # M3 — parametric double lattice
            compaction.py      # M4 — container-shrinking local minimiser
            annealing.py       # M3/M4 — SA and basin-hopping drivers
            exact_small.py     # M5 — n ≤ 20

    visualization.py           # extended in M6 with figure export
    cli.py                     # extended per milestone

tests/
    unit/                      # existing tests move here unchanged
    property/                  # M1+ — hypothesis-based invariants
    golden/                    # M1+ — parity against reference/evaluator.py
    regression/                # M2+ — score ratchet and clearance floor

artifacts/                     # gitignored except best_scores.json
    runs/<run_id>/
        manifest.json
        layouts.jsonl
    ledger.json
    best_scores.json           # COMMITTED — the regression gate's expectations

plans/                         # this directory
docs/
    figures/                   # M6 — committed PNGs referenced by the docs
```

**Boundary rules, enforced mechanically in M1:**

- Nothing outside `geometry/` may construct a tree polygon or apply a rotation.
- `optimize/` may import `geometry.fast`; `validation/` may not.
- `validation/` may import `geometry.core`; nothing in `validation/` may import
  `geometry.fast`.
- `serialization.py` imports neither.

Add `import-linter` to the dev dependency group and encode these as contracts in
`pyproject.toml`. A boundary that is only documented is a boundary that will be crossed.

---

## 4. The Gate

Unchanged from the root plan, plus two additions from M0 onward:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run lint-imports          # added M1
uv run pytest                # coverage moved to a separate target; see M0
```

**The Regression Gate** (content added M2; plumbing from M0). Runs behind `make verify`
and is enforced by a local `pre-push` hook. Hosted CI is optional — see M0's appendix:

```bash
uv run tree-packing solve --output artifacts/current.csv
uv run tree-packing gatekeep artifacts/current.csv --against artifacts/best_scores.json
```

It fails if any of the following hold:

- total score is greater than the recorded best,
- any configuration's minimum pairwise clearance is below `CLEARANCE_EPS`,
- monotonicity `s_n ≤ s_{n+1}` is violated for any `n`,
- the official `reference/evaluator.py` reports any overlap.

---

## 5. Known-good values

The root plan's table stands. These are added, and every one was measured against the
repository's own code or the official evaluator. **Do not change any of these without
recomputing and recording the recomputation in the notebook.**

| Quantity | Value | Source |
|---|---|---|
| Tree area (unscaled) | `0.245625` | shoelace; matches existing `test_geometry.py` |
| Convex hull area | `0.365` | measured |
| Circumradius (origin to tip) | `0.8` | measured; drives neighbour enumeration |
| Overlap-possible centre distance | `< 1.6` | `2 × circumradius` |
| Exact convex decomposition | 4 pieces, disjoint, union-exact | measured |
| Grid baseline total score | `256.8197122633766779770234` | repository CLI |
| Reference evaluator display | `256.819712` | `reference/evaluator.py` |
| Optimal single-tree side `s₁` | `0.81317279836452966` at `45.0°` | measured via `geometry.py` |
| Score term at `n=1`, rotated | `0.66125` | `s₁²/1` |
| Score term at `n=1`, baseline | `1.0` | existing test |
| Best rectangular grid, all 200 | `157.986` | enumeration over column counts |
| Theoretical floor (ρ = 1) | `49.125` | `200 × 0.245625` |
| Feasible double-lattice density | `0.6054` | SA search, zero overlap penalty |
| Lattice term, n = 50 / 100 / 200 | `0.49422` / `0.49045` / `0.43088` | evaluator-verified, 0 overlaps |

### 5.1 The score identity

With `A = 0.245625` and `ρ_n` the packing density of configuration `n`:

```
s_n² / n  =  A / ρ_n        ⟹        Score  =  A · Σ (1 / ρ_n)
```

The normalisation cancels `n` exactly. **All 200 configurations carry equal weight.** This
is counter-intuitive and it is the single most important framing in the project: the task
is not "pack 200 trees well", it is "achieve high density at every scale". Every milestone
target below is derived from a density claim via this identity.

### 5.2 Precision budget

`SCALE_FACTOR = 1e15` makes every canonical vertex an exactly-representable integer
(`0.8 → 8e14`, `0.0625 → 6.25e13`), all below `2⁵³ ≈ 9.007e15`. It does **not** add
precision — doubles have fixed relative precision. Consequences:

- Only rotation introduces error, at roughly `1e-16` in problem units.
- Translation is exact provided `|centre| < 9.007` and the emitted value has ≤ 15 decimal
  places. **Centre every layout on the origin.** At `n = 200` the half-extent is ≈ 4.6, so
  this holds comfortably — but only if layouts are centred.
- Exact contact is unattainable in floating point. `CLEARANCE_EPS = 1e-9` sits seven orders
  above the noise floor and costs ≈ `1.6e-9` in score at `n = 1`. It is derived, not
  guessed.

---

## 6. Ledger and run-store schema

`artifacts/runs/<run_id>/manifest.json`:

```json
{
  "run_id": "20260821T0914-lattice-s3",
  "strategy": "lattice",
  "params": {"pitch": 0.71, "row_height": 1.14, "shear": -0.71},
  "seed": 3,
  "git_sha": "c72431e",
  "started_at": "2026-08-21T09:14:02Z",
  "wall_clock_s": 184.2,
  "budget": {"kind": "evaluations", "value": 20000},
  "experiment": false,
  "n_range": [21, 200]
}
```

`artifacts/runs/<run_id>/layouts.jsonl` — one JSON object per configuration:

```json
{"n": 57, "side": 4.9711, "score_term": 0.4335, "min_clearance": 3.2e-09,
 "placements": [[0.0, 0.0, 45.0], ...]}
```

`artifacts/ledger.json` is **derived**, never hand-edited:

```json
{"57": {"run_id": "20260821T0914-lattice-s3", "score_term": 0.4335}}
```

**Promotion rule.** A layout enters the ledger for configuration `n` only if
`score_term` is strictly lower than the incumbent **and** `min_clearance ≥ CLEARANCE_EPS`
**and** `manifest.experiment` is `false`. A layout scoring `0.4331` at clearance `1e-16` is
a *worse* observation than one scoring `0.4335` at `1e-9`, because it is one rounding
change from an invalid submission. Clearance is a label, not a diagnostic.

**Canonicalisation before promotion.** The tree polygon is mirror-symmetric about `x = 0`,
verified: `mirror(P) ≡ P` and `mirror(rot θ) ≡ rot(−θ)`. Every layout therefore has a
mirror twin with an identical score. Canonicalise on write — reflect the layout if the
signed sum of its angles is negative — so multi-start does not rediscover twins and the M6
ablation does not count them as distinct solutions.

---

## 7. Algorithm selection, with reasons

The challenge document's own tips list simulated annealing, genetic algorithms, gradient-free
methods, and basin-hopping. This programme uses three of the four. The allocation is
evidence-based, not preference:

| Sub-problem | Dimensionality | Method | Milestone |
|---|---|---|---|
| Lattice parameters | 5 | **Simulated annealing** (`scipy.optimize.dual_annealing`), ≥ 5 seeds | M3 |
| Window truncation / cell occupancy | discrete | **Simulated annealing** | M3 |
| Layout refinement, boundary | 3n | **Basin-hopping** with compaction as the local minimiser | M4 |
| Small-n layouts | 3n, n ≤ 20 | **Basin-hopping** + symmetric seeding | M5 |
| Coarse sweeps, regression runs | 5 | **Differential evolution** (lowest variance) | M3, optional |

**Head-to-head evidence** at an equal 500-evaluation budget on the lattice objective:

| Method | best ρ | worst ρ |
|---|---|---|
| `dual_annealing` (SA) | **0.6720** | 0.4542 |
| `differential_evolution` | 0.5525 | 0.5176 |
| `basinhopping` (generic local minimiser) | 0.5283 | 0.0000 |

SA has the highest peak and the highest variance — manage it with seed count, not by
switching method. DE is the most consistent, which makes it the right choice for
reproducible sweeps. Basin-hopping failed outright on one seed **because it was given a
generic local minimiser**; its entire value is the local minimiser, which is why M4 pairs
it with compaction rather than Nelder-Mead. Two seeds is not a study — re-run this
comparison under the M6 protocol before citing it as a finding.

**Genetic algorithms are rejected**, and the rejection must be written up in `DECISIONS.md`
rather than omitted, because the challenge document suggests them. The reason is specific:
crossover has no valid semantics for packing. Splicing the left half of layout A with the
right half of layout B produces overlaps along the seam every time, so a repair operator
dominates and the genetic operators stop doing work. SA and basin-hopping cover the same
stochastic-search ground with valid operators.

**CMA-ES is rejected** on maintainability grounds: it requires a dependency outside
`scipy` for an unmeasured gain over SA.

---

## 8. Failure register — carry these forward

Two failures already occurred in this project's analysis and both belong in
`DECISIONS.md` and the interview narrative. They are worth more than a clean record.

**8.1 The constraint-completeness failure.** A lattice search reported cell density
`0.877`; the official evaluator measured `0.327` with 29 overlapping pairs. Root cause: the
feasibility check enumerated neighbours over a ±2 *lattice-index* window, while the true
violating neighbour sat at index offset `(Δi, Δj) = (4, 2)` — pulled geometrically close by
the lattice shear. The optimiser did not solve the problem; it found the hole in the
constraint set. **Fix, mandatory in M1:** enumerate candidate neighbours by *geometric
distance* (`< 1.6`) over a **Gauss-reduced basis**, never by index window.

**8.2 The unjustified-default failure.** Differential evolution was chosen for the lattice
search because it was the quickest thing to reach for, not because it was compared against
the methods the challenge document names. When finally measured, SA beat it. **Fix:** every
optimiser choice in this programme carries a measurement or an explicit "not yet measured"
tag.

---

## 9. Documentation duties at every milestone

These are part of the exit gate, not an afterthought. The brief asks for documented
assumptions, design decisions, and trade-offs, and judges "engineering approach" directly.

| File | Duty at every milestone |
|---|---|
| `LAB_NOTEBOOK.md` | One entry per sub-hypothesis, using §2.3. Written at the time, never reconstructed |
| `DECISIONS.md` | One short section per irreversible choice made in that milestone |
| `README.md` | Runbook updated so a clean clone reproduces the new commands |
| `baseline-breakdown.md` | Extended with the new modules, keeping its module-by-module structure |
| `documentary.md` | Dated entry: what was done, what was verified, what was left |
| `plans/README.md` | Status column updated to `DONE (<tag>, score <value>)` |

**Milestone M0 additionally repairs three existing documentation defects.**

---

## 10. Mapping to the assessment criteria

The brief names six areas plus an interview stage. Every milestone contributes to at least
one; the mapping below should be reproduced in `DECISIONS.md` so reviewers can navigate it.

| Criterion | Where it is earned |
|---|---|
| **Technical quality & problem solving** | M2–M5: `256.82 → ≤ 82`, each step measured against the official evaluator |
| **Architecture** | M1's two-tier geometry rule and boundary contracts; M6's ledger-as-derived-view |
| **Code quality** | Existing gates preserved and extended: `mypy --strict`, ruff, import-linter, property tests |
| **Maintainability** | Sub-packages with enforced boundaries; frozen config; no magic numbers; seeded determinism |
| **Engineering approach** | `LAB_NOTEBOOK.md` sub-hypothesis chain including refuted predictions; the §8 failure register |
| **Communication** | M6: ablation table, per-`n` strategy heatmap, figures, and a written trade-off ranking |
| **Interview readiness** | M6's presentation checklist; the two failures in §8 are the strongest material available |

A reviewer who reads only `DECISIONS.md` and the M6 results section should be able to
reconstruct the entire programme. Write for that reader.
