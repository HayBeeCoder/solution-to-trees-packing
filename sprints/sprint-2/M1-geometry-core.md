# M1 — Fast geometry core, clearance instrumentation, run ledger

**Score target:** `256.8197122633766779770234` — unchanged.
**Tag on completion:** `v0.3-core`
**Estimated effort:** one to one and a half days.

Read `00-shared-contract.md` first. §3 (layout), §5 (known-good values), §6 (ledger schema)
and §8.1 (the constraint-completeness failure) are all load-bearing here.

---

## Why this milestone exists

The current geometry path costs **89.1 µs per polygon**, measured on this repository's own
`create_tree_polygon`. One feasibility check at `n = 100` costs about 2.2 ms. A simulated
annealing run needing 10⁵ evaluations across 200 configurations will not finish. Nothing in
M2–M5 is reachable until this is fixed.

Three other things must exist before an optimiser does, and none of them can be
retro-fitted safely: clearance instrumentation, sound neighbour enumeration, and the run
ledger. Like M0, this milestone changes no output.

---

## H1 — Primary hypothesis

> The geometry layer can be made roughly twenty times faster for search, instrumented with
> clearance reporting, and given sound neighbour enumeration, while the scored output
> remains bit-identical to M0's.

**Label:** the Gate is green, and `uv run tree-packing evaluate` still reports exactly
`256.8197122633766779770234`.

---

## Sub-hypotheses

### H1.1 — The flat modules can become sub-packages without breaking a single import

- **Kind:** structural
- **Predicted:** every existing test passes **unedited**.
- **Label:** `uv run pytest` with zero changes to any file under `tests/`.
- **Falsified if:** any existing test requires modification.

Move `geometry.py → geometry/core.py` and `validation.py → validation/overlap.py`, then
re-export from each `__init__.py`:

```python
# src/tree_packing/geometry/__init__.py
from tree_packing.geometry.core import create_tree_polygon, tree_vertices

__all__ = ["create_tree_polygon", "tree_vertices"]
```

Use `git mv` so the history follows the file. The constraint that existing tests remain
untouched is the proof that the refactor is behaviour-preserving — if a test needs editing,
the public API changed, and that is a different and larger decision.

Move existing tests into `tests/unit/` in the same commit. That is a path change, not a
content change, and does not violate the constraint above.

### H1.2 — A NumPy transform is ~18× faster and stays within the precision budget

- **Kind:** empirical
- **Predicted:** ≥ 15× speed-up; maximum vertex deviation from the Shapely path
  ≤ `1e-14` in problem units.
- **Label:** `tests/property/test_fast_geometry_parity.py` over 10,000 random
  `(x, y, θ)` triples; a benchmark recorded in the notebook.
- **Falsified if:** the speed-up is under 10×, or any deviation exceeds `1e-12`.

The prototype measured **4.86 µs/call against 89.1 µs/call — 18.3×** — with a maximum
vertex deviation of `0.25` scaled units, i.e. `2.5e-16` in problem units. That is seven
orders below `CLEARANCE_EPS`.

```python
# src/tree_packing/geometry/fast.py
"""Vectorised vertex transform for SEARCH ONLY.

This module is NOT authoritative. It is deliberately not bit-identical to
`geometry.core`; deviations of order 1e-16 in problem units are expected and
acceptable because every candidate is re-validated through `core` before it can
enter the ledger. Never import this module from `validation/`.
"""
```

Write that docstring first. It is the only thing standing between this optimisation and a
silently invalid submission.

The base vertex array is cached at module import from `tree_vertices()` — **not**
re-derived from literals. There must remain exactly one place where the tree's shape is
written down.

### H1.3 — The four-piece convex decomposition is exact

- **Kind:** structural
- **Predicted:** four pieces; all convex; pairwise disjoint; union symmetric-difference to
  the canonical polygon below `1e-15`; areas summing to `0.245625`.
- **Label:** `tests/unit/test_decomposition.py`.
- **Falsified if:** any of the four properties fails.

The pieces are the trunk rectangle, two trapezoidal bands, and the tip triangle:

| Piece | Vertices | Area |
|---|---|---|
| Trunk | `(±0.075, −0.2)`, `(±0.075, 0.0)` | `0.030000` |
| Bottom band | `(±0.35, 0.0)`, `(±0.1, 0.25)` | `0.112500` |
| Middle band | `(±0.2, 0.25)`, `(±0.0625, 0.5)` | `0.065625` |
| Tip | `(±0.125, 0.5)`, `(0.0, 0.8)` | `0.037500` |

All four properties were verified during planning. This decomposition is what makes M4's
compaction tractable: penetration depth between two trees becomes sixteen convex–convex
tests with analytic gradients, instead of one non-convex problem with none.

### H1.4 — Neighbour enumeration is geometric, not combinatorial

- **Kind:** structural
- **Predicted:** for any lattice basis, the enumerator returns every translation with
  norm `< 1.6`, including those at large index offsets under shear.
- **Label:** `tests/unit/test_neighbours.py`, containing an explicit regression case built
  from the §8.1 failure — a sheared basis whose violating neighbour sits at index offset
  `(4, 2)`.
- **Falsified if:** the enumerator misses any short vector, or a lattice it passes as
  feasible is rejected by `reference/evaluator.py` on a materialised patch.

Implement Lagrange–Gauss basis reduction, then enumerate over a bounded index range on the
**reduced** basis, filtering by Euclidean norm. Assert reduction correctness directly:
`|b| ≥ |a|` and `|2·(a·b)| ≤ a·a`.

This sub-hypothesis exists solely because of a real failure. Write the regression test
before the implementation and watch it fail — a regression test that has never been red is
not a regression test.

### H1.5 — Clearance is measurable, and it is a label

- **Kind:** structural
- **Predicted:** `min_clearance` for the grid baseline at `n = 4` equals the grid gap to
  within `1e-12`; for two touching trees it is `0.0`; for overlapping trees it is negative.
- **Label:** `tests/unit/test_clearance.py`.
- **Falsified if:** any of the three cases is wrong, or the sign convention is inconsistent.

Add `validation/clearance.py` exposing `min_pairwise_clearance(polygons) -> Decimal`, using
`STRtree` to prune to candidate pairs and Shapely `distance` for separation. Negative values
signal penetration and must be reported, not clamped — a gatekeeper that cannot distinguish
"passed by 1e-16" from "passed by 1e-9" cannot do its job.

### H1.6 — The gatekeeper reads from disk

- **Kind:** structural
- **Predicted:** a CSV whose in-memory layout is valid but whose serialised form is not is
  correctly **rejected**.
- **Label:** `tests/unit/test_gatekeeper.py` with a deliberately constructed adversarial
  case — two trees placed at exactly `CLEARANCE_EPS / 2` separation, serialised with a
  format that rounds them into contact.
- **Falsified if:** the gatekeeper passes a submission the official evaluator rejects.

`validation/gatekeeper.py` reads the written CSV, parses with the same `float(value[1:])`
semantics as the evaluator, rebuilds through `geometry.core`, and reports per-configuration
side, score term, overlap pairs, and minimum clearance. Add `tree-packing gatekeep` to the
CLI.

### H1.7 — Boundary rules are enforced by tooling, not documentation

- **Kind:** structural
- **Predicted:** `lint-imports` passes; an experimental import of `geometry.fast` from
  `validation/` fails it.
- **Label:** `uv run lint-imports`, plus a manual falsification check — add the forbidden
  import, confirm the tool goes red, remove it.
- **Falsified if:** the contract passes with the forbidden import present.

Add `import-linter` to the dev group and encode §3's boundary rules in `pyproject.toml`.
Perform the falsification check and record it in the notebook: an unfalsified guard is an
unverified guard.

### H1.8 — The ledger is immutable and its arg-min is derived

- **Kind:** structural
- **Predicted:** writing two runs for the same `n` leaves both on disk; the ledger reflects
  the better; a run marked `experiment: true` never enters the ledger; a run with
  `min_clearance` below `CLEARANCE_EPS` never enters the ledger even if its score is lower.
- **Label:** `tests/unit/test_ledger.py`.
- **Falsified if:** any run is overwritten, or either exclusion rule fails.

Implement `optimize/ledger.py` and `optimize/types.py` per §6. `Layout` and `Placement` are
frozen dataclasses — the optimiser will hold thousands of candidates concurrently and
mutable shared state is how those become silently entangled.

Include canonicalisation on write (§6). Seed the ledger from the M0 baseline so it is
populated for all 200 configurations from day one, and the invariant in §1.2 holds
throughout.

---

## Exit gate

- [ ] Gate green, now including `uv run lint-imports`.
- [ ] Every pre-existing test passes **unedited** (path moves only).
- [ ] Fast-vs-Shapely parity within `1e-14` over 10,000 random triples.
- [ ] Benchmark recorded in `LAB_NOTEBOOK.md`: before and after µs/call, and the ratio.
- [ ] `test_neighbours.py` contains the `(4, 2)` regression case and it was observed red
      before the fix.
- [ ] The import-linter falsification check was performed and recorded.
- [ ] Ledger seeded with all 200 baseline configurations.
- [ ] `uv run tree-packing evaluate` reports **exactly** `256.8197122633766779770234`.
- [ ] `uv run tree-packing gatekeep data/submissions/baseline.csv` agrees, and reports a
      per-configuration minimum clearance.
- [ ] **TDD audit:** every structural sub-hypothesis has a `test(...)` commit preceding its
      `feat(...)` commit, and a `Red observed` field in `LAB_NOTEBOOK.md`.
- [ ] **Mutation spot-check** performed on one component and recorded.
- [ ] Documentation duties per shared contract §9, including a new
      `baseline-breakdown.md` section for the `geometry/`, `validation/` and `optimize/`
      packages.
- [ ] Tagged `v0.3-core`.

---

## Notes for the executing agent

The two-tier geometry rule is the architectural spine of everything that follows. If you
find yourself wanting to use the fast path "just for this one check" inside `validation/`,
that is the exact failure the rule exists to prevent. `lint-imports` will stop you; do not
add an exemption.

Add `numpy` and `scipy` to the runtime dependencies in this milestone. `scipy` is not used
until M3, but adding both here means `uv.lock` changes once rather than twice, and the
lockfile diff stays legible.
