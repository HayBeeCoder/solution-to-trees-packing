# Lab notebook

This ledger applies the “Agentic Coding is Science” workflow from `plan.md`.
Each entry states the hypothesis, its label, the observed trace, and the
selection decision. The
first entries are reconstructed from the work already completed before the
revised plan was populated; subsequent refinements are recorded explicitly.

## Step 1 — project bootstrap

- **Hypothesis:** `uv sync` will resolve the declared project and create a usable
  Python 3.12 environment and lockfile — label: `uv sync` exit code 0.
- **Generated:** `pyproject.toml`, `.python-version`, `.gitignore`,
  `.pre-commit-config.yaml`.
- **Observed:** The first run could not access uv’s external cache in the
  sandbox. The same command with approved cache access created `.venv`, resolved
  40 packages, and installed successfully using CPython 3.12.9.
- **Measured:** Green after the environment-access correction; `uv.lock` exists.
- **Selected / Refined:** Selected the declared dependency set. Refined the
  execution environment by allowing the required uv cache access.

## Step 2 — preserve reference inputs

- **Hypothesis:** The supplied evaluator, simple algorithm, and challenge
  description can be retained unchanged under `reference/` — label: bytewise
  `cmp` checks and importability.
- **Generated:** `reference/evaluator.py`, `reference/simple_algorithm.py`,
  `reference/christmas_tree_packing_challenge.md`, and `reference/plan.md`.
- **Observed:** The three supplied source files compare byte-for-byte with their
  copies. At the time this step was first executed, the referenced
  `sample_solution.csv` was not visible in the local challenge workspace, so it
  was not invented. A later workspace check found the supplied file under
  `reference/`.
- **Measured:** Green for the available reference artifacts.
- **Selected / Refined:** Selected the copies and recorded the file's actual
  availability at each inspection time rather than fabricating a source of
  truth.

## Step 3 — package marker

- **Hypothesis:** The `tree_packing` package and PEP 561 marker will import from
  the installed project — label: `import tree_packing` and `mypy src`.
- **Generated:** `src/tree_packing/__init__.py` and `src/tree_packing/py.typed`.
- **Observed:** The package is exercised by all tests and the CLI; strict mypy
  later reports no issues across nine source modules.
- **Measured:** Green.
- **Selected / Refined:** Selected the package layout and marker.

## Step 4 — constants

- **Hypothesis:** The configuration constants can be copied verbatim from the
  evaluator and simple algorithm — label: `tests/test_config.py` and Gate.
- **Generated:** `src/tree_packing/config.py` and `tests/test_config.py`.
- **Observed:** Tests assert the Decimal scale, precision, coordinate bounds,
  tree range, and grid spacing; the complete suite passes.
- **Measured:** Green; exact constant assertions pass.
- **Selected / Refined:** Selected the constants without numeric reinterpretation.

## Step 5 — geometry and parity

- **Hypothesis:** One canonical scaled polygon will reproduce the evaluator,
  including area, bounds, translation, and rotations — label:
  `tests/test_geometry.py`, `tests/test_parity_with_reference.py`, and Gate.
- **Generated:** `src/tree_packing/geometry.py` and geometry/parity tests.
- **Observed:** The polygon has 15 vertices, area `0.245625`, bounds
  `(-0.35, -0.2, 0.35, 0.8)`, and `our.equals(theirs)` passes for translated and
  rotated examples.
- **Measured:** Green; the overfitting guard is green.
- **Selected / Refined:** Selected the port as the single geometry source.

## Step 6 — scoring

- **Hypothesis:** Bounding-square side and `s_n^2 / n` scoring will reproduce the
  known one-tree and normalization values — label: `tests/test_scoring.py` and
  Gate.
- **Generated:** `src/tree_packing/scoring.py` and scoring tests.
- **Observed:** Empty side is zero, one-tree side and score are approximately
  `1.0`, and `2^2 / 4` is exactly `1.0`.
- **Measured:** Green.
- **Selected / Refined:** Selected Decimal score accumulation and evaluator scale
  conversion.

## Step 7 — validation

- **Hypothesis:** STRtree candidate pairs plus `intersects`/`touches` will flag
  true overlaps while allowing distant trees — label: `tests/test_validation.py`
  and Gate.
- **Generated:** `src/tree_packing/validation.py` and overlap/frame tests.
- **Observed:** Identical trees produce pair `(0, 1)`; far-apart and singleton
  cases are clear; missing and out-of-bounds frame entries are reported.
- **Measured:** Green.
- **Selected / Refined:** Selected the faithful overlap predicate.

## Step 8 — baseline

- **Hypothesis:** The centered 1.1-spaced grid will produce exactly `n` trees,
  cover all 200 configurations, and avoid sampled overlaps — label:
  `tests/test_baseline.py` and Gate.
- **Generated:** `src/tree_packing/baseline.py` and baseline tests.
- **Observed:** Counts for sampled values are exact, sampled grids are
  overlap-free, and the baseline total is 20,100 placements.
- **Measured:** Green.
- **Selected / Refined:** Selected the deterministic grid; no optimizer was added.

## Step 9 — serialization

- **Hypothesis:** The `s`-prefixed CSV format will round-trip all 20,100 baseline
  placements — label: `tests/test_serialization.py` and Gate.
- **Generated:** `src/tree_packing/serialization.py` and serialization tests.
- **Observed:** Prefix formatting/parsing works, plain floats are tolerated, and
  write-then-load returns 20,100 rows with all configurations present.
- **Measured:** Green.
- **Selected / Refined:** Selected the official `id`, `x`, `y`, `deg` layout.

## Step 10 — optional visualization

- **Hypothesis:** Matplotlib can remain optional because the core module imports
  without it and the renderer can raise a clear installation message — label:
  lazy-import/manual CLI check and `mypy src`.
- **Generated:** `src/tree_packing/visualization.py`.
- **Observed:** The module is not imported by core package startup; the wrapper
  guards matplotlib and points to `uv sync --extra viz` when absent. Strict mypy
  passes.
- **Measured:** Green for the core/no-extra path; GUI rendering is intentionally
  not exercised in the headless quality run.
- **Selected / Refined:** Selected a thin optional wrapper.

## Step 11 — CLI

- **Hypothesis:** The project entry point will generate and evaluate a complete
  submission — label: manual `generate` then `evaluate`.
- **Generated:** `src/tree_packing/cli.py` and the `[project.scripts]` entry point.
- **Observed:** Generation wrote 20,100 rows. Evaluation reported no overlaps and
  total score `256.8197122633766779770234`.
- **Measured:** Green.
- **Selected / Refined:** Selected the thin argparse orchestration over module logic.

## Step 12 — integration

- **Hypothesis:** The complete baseline will be structurally valid across all 200
  configurations and finite/overlap-free for small `n` — label:
  `tests/test_integration.py` and Gate.
- **Generated:** Integration tests.
- **Observed:** The full test suite reports 27 passed; small `n=1..20` scoring
  and overlap checks pass.
- **Measured:** Green.
- **Selected / Refined:** Selected the fast structural/full small-n split.

## Step 13 — documentation

- **Hypothesis:** A clean clone can reproduce setup, gates, generation, and both
  evaluators from `README.md` — label: manual runbook inspection and successful
  execution of every documented command.
- **Generated:** `README.md` and `DECISIONS.md`.
- **Observed:** The documented `uv sync`, quality tools, generation, internal
  evaluation, and reference evaluation all completed successfully.
- **Measured:** Green for the documented core flow.
- **Selected / Refined:** Selected concise runbook documentation and explicit
  trade-off records.

## Step 14 — final end-to-end gate

- **Hypothesis:** The complete system will remain green under repository-wide
  format/lint, strict mypy, pytest, and the reference evaluator — label: full
  Gate plus reference cross-check.
- **Generated:** Final integrated workspace and `data/submissions/baseline.csv`.
- **Observed:** Repository-wide Ruff format check and lint pass; mypy passes;
  pytest reports 27 passed; the generated CSV has 20,100 data rows; both
  evaluators accept it with no overlaps. The reference displays `256.819712`,
  matching the internal Decimal score to displayed precision.
- **Measured:** Green.
- **Selected / Refined:** Selected the complete baseline implementation.

## Refinement traces

- **Environment refinement:** uv cache permission failure → approved cache access
  → successful sync.
- **Formatting refinement:** Ruff found two package formatting changes → applied
  Ruff formatting → format check passed.
- **Lint refinement:** Ruff found an unused visualization figure and a test
  assertion style issue → removed the unused binding and rewrote the assertion →
  lint passed.
- **Typing refinement:** mypy found six pandas row-type mismatches → converted
  loaded numeric fields to strings at the geometry API boundary → strict mypy
  passed.
- **Repository-gate refinement:** Ruff considered preserved Markdown plan content
  as Python code blocks → excluded reference/challenge artifacts and documentary
  files from Ruff discovery while retaining source/test coverage → repository
  gate passed without modifying preserved artifacts.
- **Focused-label refinement:** Concurrent pytest processes raced over the shared
  pytest-cov `.coverage` SQLite file and produced an internal coverage-combine
  error after validation assertions passed → erased the generated coverage file,
  serialized the affected pytest run, and obtained 4 passed.

## M0.1 — tracked files must not be ignored

- **Hypothesis:** `.gitignore` can exclude only untracked/generated artifacts;
  no tracked path will match an ignore rule — kind: structural, label:
  `tests/unit/test_repo_hygiene.py`.
- **Predicted:** `git ls-files -ci --exclude-standard` has no output.
- **Test written:** `tests/unit/test_repo_hygiene.py`.
- **Red observed:** `AssertionError: Tracked files matched by ignore rules:\nplan.md\nreference/plan.md`.
- **Generated:** `.gitignore` removes record/plan/sprint ignores and adds only
  generated run-artifact ignores.
- **Green observed:** `uv run pytest tests/unit/test_repo_hygiene.py` — 1 passed
  in 0.09s.
- **Refactored:** none needed.
- **Measured:** `git ls-files -ci --exclude-standard` is empty.
- **Selected / Refined:** kept; H0.1 confirmed.

## M0.2 — documented paths resolve from a clean clone

- **Hypothesis:** Every relative Markdown link and explicit repository path refers
  to a file available from Git — kind: structural, label:
  `tests/unit/test_docs_links.py`.
- **Predicted:** no missing or untracked documented paths.
- **Test written:** `tests/unit/test_docs_links.py`.
- **Red observed:** `AssertionError: Documented paths do not exist:
  ['challenge-files', 'challenge-files/christmas_tree_packing_challenge.md',
  'challenge-files/evaluator.py', 'challenge-files/plan-with-agentic-as-science.md',
  'challenge-files/plan.md', 'challenge-files/sample_solution.csv',
  'challenge-files/simple_algorithm.py']`.
- **Generated:** test only; documentation repair pending.
- **Green observed:** `uv run pytest tests/unit/test_docs_links.py` — 1 passed
  in 3.73s.
- **Refactored:** the first test version checked only local existence and passed
  because the local challenge workspace existed outside Git; refined it to
  require Git tracking.
- **Measured:** all committed Markdown paths now resolve in a clean clone.
- **Selected / Refined:** kept; H0.2 confirmed.

## M0.3 — README is the documentation entry point

- **Hypothesis:** Every project Markdown document is reachable directly from
  `README.md` — kind: structural, label: `tests/unit/test_docs_links.py`.
- **Predicted:** the README has no missing one-hop project-document links.
- **Test written:** `tests/unit/test_docs_links.py`.
- **Red observed:** `AssertionError: README does not link project documents:
  ['baseline-breakdown.md', 'documentary.md', 'plan.md']`.
- **Generated:** test only; documentation map pending.
- **Green observed:** `uv run pytest tests/unit/test_docs_links.py` — 2 passed
  in 3.55s.
- **Refactored:** excluded prospective Sprint 2 plans from present-state code-path
  checks because they intentionally name modules scheduled for M1–M6; the
  README reachability assertion still covers every sprint document.
- **Measured:** the README links every non-reference project Markdown document.
- **Selected / Refined:** kept; H0.3 confirmed.

## M0.4 — CI runs the Gate and reference evaluator

- **Hypothesis:** GitHub Actions has independent quality-gate and baseline
  reference-evaluator jobs — kind: structural, label:
  `tests/unit/test_ci_workflow.py` and a GitHub Actions run.
- **Predicted:** the workflow contains locked sync, the four Gate commands, and
  baseline generation followed by `reference/evaluator.py`.
- **Test written:** `tests/unit/test_ci_workflow.py`.
- **Red observed:** `FileNotFoundError: [Errno 2] No such file or directory:
  '/Users/m1/Documents/__ai__/trees-packing/.github/workflows/ci.yml'`.
- **Generated:** test only; workflow pending.
- **Green observed:** `uv run pytest tests/unit/test_ci_workflow.py` — 1 passed
  in 0.07s.
- **Refactored:** none needed; the two workflow jobs mirror the Gate and isolate
  the reference-evaluator check.
- **Measured:** local workflow contract is green; remote Actions status is
  pending until the branch is pushed.
- **Selected / Refined:** kept locally; CI run pending external publication.
