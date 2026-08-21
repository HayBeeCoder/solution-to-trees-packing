# Delegated task documentary

This file records the material actions, decisions, and verification results for
the delegated Christmas Tree Packing task. It is maintained as execution
continues so another person can reconstruct the work without relying on the chat.
`challenge-files/` was the original local workspace path; its committed source
artifacts are preserved under `reference/`.

## 2026-08-20 — initial execution

### Request and source material

- The task was to execute the original plan, now preserved as `reference/plan.md`.
- The supplied plan is an 858-line implementation specification for a typed,
  tested Python project containing only the deterministic grid baseline.
- The supplied challenge files were inspected directly. The official evaluator
  defines a 15-vertex scaled Shapely polygon, Decimal precision 25, scale factor
  `1e15`, coordinate bounds `[-100, 100]`, configurations `1..200`, and the
  `1.1`-spaced grid baseline.
- The evaluator, simple algorithm, and challenge description were supplied. At
  the time of the initial inspection, the referenced `sample_solution.csv` was
  not visible in the local challenge workspace, so no substitute was created.

### Files and structure created

- Created project metadata: `pyproject.toml`, `.python-version`, `.gitignore`,
  and `.pre-commit-config.yaml`.
- Created `reference/` and copied the supplied evaluator, simple algorithm,
  challenge description, and plan there for comparison. The local source files
  were left untouched.
- Created `plan.md` at the repository root as a copy of the original plan.
- Created `data/submissions/.gitkeep`.
- Created the `src/tree_packing/` package with typed modules for configuration,
  geometry, scoring, validation, baseline generation, serialization,
  visualization, and CLI handling.
- Created the planned tests under `tests/`, including a direct polygon parity
  test against `reference/evaluator.py`.
- Created `README.md` and `DECISIONS.md` with the requested runbook and design
  rationale.

### Environment milestone

- The first `uv sync` attempt was blocked because the sandbox could not access
  uv's cache at `/Users/m1/.cache/uv`.
- The same read/install operation was then approved with elevated access.
- `uv sync` completed successfully using CPython 3.12.9, created `.venv` and
  `uv.lock`, and installed the project dependencies and development tools.
- Quality gates and baseline generation had not yet been run at the time of this
  entry.

### Quality and parity milestones

- Ruff initially reported two formatting changes in the package, one unused
  visualization figure variable, and one test assertion style issue. The package
  was formatted and those issues were corrected.
- Strict mypy initially reported six pandas-row typing errors at the boundary
  where CLI and visualization code call the geometry constructor. Numeric row
  fields are now converted to strings before entering the Decimal-based API;
  `uv run mypy src` passes with no issues.
- `uv run ruff format --check src tests` and `uv run ruff check src tests` pass.
- `uv run pytest` passes all 27 tests in 30.83 seconds.
- `uv run tree-packing generate --output data/submissions/baseline.csv` created
  exactly 20,100 data rows plus the CSV header.
- The package CLI evaluated the generated baseline with no overlap errors and
  total score `256.8197122633766779770234`.
- `uv run python reference/evaluator.py data/submissions/baseline.csv --quiet`
  accepted the same submission with no overlaps and displayed
  `256.819712`, agreeing with the package evaluator at the reference command's
  displayed precision.
- To keep the retained reference artifacts and plan documents byte-for-byte
  untouched, Ruff's repository-wide configuration excludes `reference/` and the
  local challenge workspace; project source and tests remain covered by the
  formatting and lint gates.
- Final integrity checks confirm the three supplied reference files copied into
  `reference/` are byte-identical to the supplied source files, and the
  generated CSV has 20,101 lines including its header.
- During the revised focused-label run, concurrent pytest processes briefly
  corrupted the shared generated `.coverage` SQLite artifact. The affected
  validation tests had already passed; after erasing that generated artifact and
  rerunning sequentially, all 4 validation tests passed cleanly. This was logged
  as an execution refinement in `LAB_NOTEBOOK.md`.

## 2026-08-20 — revised-plan verification

- The user provided a revised root `plan.md` and asked for verification that the
  major change was the “agentic as science” part.
- Direct inspection now finds 943 lines versus 858 in the original.
- The diff adds the “Agentic Coding is Science” operating methodology, including
  the six-step hypothesis/generate/run/measure/select/refine loop, explicit
  labels, rules of engagement, per-step scientific implementation order, and a
  critical parity overfitting guard.
- It adds `LAB_NOTEBOOK.md` to the target layout and requires one hypothesis
  entry per implementation step. It also adds a process decision to
  `DECISIONS.md`.
- The geometry, scoring, validation, baseline, serialization, CLI, test values,
  and definition-of-done requirements are unchanged in substance.
- Conclusion: yes, the major functional change is the agentic-as-science process,
  with the notebook and process documentation as its required artifacts.

## 2026-08-20 — sample solution clarification

- In response to the user's question, the earlier execution log was checked:
  `sample_solution.csv` was absent from the initial local-workspace listing.
- A fresh read-only workspace check now finds `reference/sample_solution.csv`,
  766,694 bytes. This file was therefore not observed during the earlier
  adventure and appeared in the workspace afterward (or was synchronized after
  that inspection).

### Revised-plan execution

- Added `LAB_NOTEBOOK.md` with one entry for each of the 14 numbered steps,
  including labels, observed traces, selections, and refinement traces.
- Updated `README.md`, `DECISIONS.md`, and this documentary to link and explain
  the notebook.

## Current status

- Implementation scaffolding: complete.
- Dependency synchronization: complete.
- Revised-plan comparison: complete; the major change is the scientific
  operating methodology plus `LAB_NOTEBOOK.md` and process documentation.
- `LAB_NOTEBOOK.md` is complete with one entry for each of the 14 revised-plan
  steps and a refinement ledger.
- The active root `plan.md` contains the revised methodology; the original
  remains available at `reference/plan.md`.
- Final formatting, linting, strict typing, and pytest gates are green.
- Fresh baseline generation and both internal/reference evaluator checks are
  green with no overlaps.

## Final revised-plan evidence

- `uv sync --locked`: passed; 40 packages resolved and 31 checked.
- Focused labels: configuration (2), geometry/parity (7), scoring (4),
ww
  tests all passed.
- Lazy visualization import passed; without the optional extra, the CLI emitted
  the specified `uv sync --extra viz` installation guidance.
- Exact final Gate: `uv run ruff format .` (22 files unchanged), `uv run ruff
  check .`, `uv run mypy src`, and `uv run pytest` (27 passed) all passed.
- Fresh CSV integrity: 20,101 lines including the header, with 20,100 data
  rows.
- Fresh internal score: `256.8197122633766779770234`.
- Fresh reference evaluator: accepted, no overlaps, displayed `256.819712`.

## 2026-08-20 — local commit hygiene

- Rewrote the previous local implementation commit at the user's request.
- Removed `DECISIONS.md`, `LAB_NOTEBOOK.md`, and `documentary.md` from the
  replacement commit while preserving them on disk.
- Added root-level ignore rules for all three records so they will not be
  accidentally staged or pushed in future commits.
- Recommitted the remaining implementation, tooling, README, active plan, and
  lockfile as `f0cf83f` with message `feat: add verified tree packing baseline
  package`.
- The commit's pre-commit Ruff and mypy hooks passed. The pre-existing unstaged
  parity-test change and untracked `reference/` and `data/` directories were
  preserved outside the commit.

## Next execution entry

When the revised plan is populated, record its line count, a focused diff of its
requirements, the conclusion about what changed, and then continue the quality
gates and any additional implementation it requires.

## 2026-08-21 — M0 hygiene and reproducibility

- Reverted the superseded two-commit hosted-CI experiment without rewriting
  history; no workflow remains.
- Repaired the local quality surface: default pytest no longer creates coverage
  state, `make coverage` reports it on demand, and a thin Makefile provides the
  documented gate, baseline, and verification targets.
- Added a local `pre-push` hook that runs `make verify`. The README now installs
  this hook and uses the Makefile as the single runbook interface.
- Corrected CLI overlap reporting and removed inert Ruff exclusions. The score
  path and submission placements were not changed.
- Recorded red/green TDD evidence for each new structural check in the lab
  notebook. A deliberate temporary Makefile failure was refused by the
  installed pre-push hook and then removed.
- Fresh clone evidence: `uv sync --locked && make verify` installed the locked
  environment, passed all 34 tests, returned the internal score
  `256.8197122633766779770234`, and the official evaluator displayed
  `256.819712` with no overlaps.
