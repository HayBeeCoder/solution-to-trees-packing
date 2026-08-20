# M0 — Submission surface, CI, and quality gates

**Score target:** `256.8197122633766779770234` — unchanged.
**Tag on completion:** `v0.2-hygiene`
**Estimated effort:** half a day.

Read `00-shared-contract.md` first.

---

## Why this milestone exists

The repository currently contains excellent work that a reviewer cannot fully see or trust:
documentation that contradicts the ignore rules, paths that do not resolve from a clean
clone, and no continuous integration. None of this affects the score, and all of it affects
four of the six assessment criteria.

M0 changes no algorithm and must change no output. Its exit gate asserts the score is
**identical**, not improved.

---

## H0 — Primary hypothesis

> The repository can be made fully self-describing and CI-verified from a clean clone,
> without altering a single placement in the generated submission.

**Label:** the Gate is green, CI passes on a clean checkout, and
`uv run tree-packing evaluate` reports exactly `256.8197122633766779770234`.

---

## Sub-hypotheses

### H0.1 — The ignore rules can be made consistent with the tracked tree

- **Kind:** structural
- **Predicted:** `git status --ignored --porcelain` lists no tracked file as ignored.
- **Label:** a new `tests/unit/test_repo_hygiene.py` assertion, plus manual `git check-ignore`.
- **Falsified if:** any tracked path is still matched by a `.gitignore` pattern.

`.gitignore` currently carries:

```
# Local execution records; never commit these files.
/DECISIONS.md
/LAB_NOTEBOOK.md
/documentary.md
**/plan.md
```

All four are now tracked. Git honours the tracking, so nothing breaks — but a reviewer
reading `.gitignore` sees a rule stating these must never be committed, sitting next to the
committed files. Delete the block and its comment. Keep `data/submissions/*.csv`,
`challenge-files/`, and the tooling caches.

Add instead:

```
artifacts/runs/
artifacts/ledger.json
artifacts/*.csv
!artifacts/best_scores.json
```

### H0.2 — Every documented path resolves from a clean clone

- **Kind:** structural
- **Predicted:** zero dead relative links across all committed Markdown.
- **Label:** a link-checking test in `tests/unit/test_docs_links.py` that walks every
  Markdown file, extracts relative links and inline code paths matching `^[\w./-]+\.(md|py|csv|toml)$`,
  and asserts each exists.
- **Falsified if:** any referenced path is missing.

Known offenders: `documentary.md` and `baseline-breakdown.md` reference `challenge-files/`,
which does not exist in the repository — it was the local working directory during the
original execution. Do **not** create the directory. Rewrite the references to point at
`reference/`, and add one sentence at the top of `documentary.md` explaining that
`challenge-files/` was the local workspace path and that its contents are preserved under
`reference/`. Preserving the honest history is better than rewriting it silently.

### H0.3 — The README is a complete entry point

- **Kind:** structural
- **Predicted:** every committed Markdown document is reachable from `README.md` in one hop.
- **Label:** extend `test_docs_links.py` with a reachability assertion.
- **Falsified if:** `baseline-breakdown.md`, `documentary.md`, or `plans/` is unreachable.

Add a "Documentation map" section to `README.md` with a one-line description of each
document's purpose and audience. `baseline-breakdown.md` is 1,122 lines and currently
unreachable from the entry point — it is the most substantial artefact in the repository.

### H0.4 — The Gate runs in CI on a clean checkout

- **Kind:** structural
- **Predicted:** a GitHub Actions workflow passes on `main` in under five minutes.
- **Label:** a green Actions run.
- **Falsified if:** any gate step fails, or the run exceeds ten minutes.

Create `.github/workflows/ci.yml`: checkout, install `uv`, `uv sync --locked`, then the
Gate. Add a second job that runs `uv run tree-packing generate` and pipes the result through
`reference/evaluator.py --quiet`, asserting the exit code is zero. This is the job that will
become the Regression Gate in M2, so structure it as a separate job now.

### H0.5 — Coverage no longer races, and the Gate is faster

- **Kind:** structural
- **Predicted:** `uv run pytest` completes measurably faster than the recorded 30.83 s, with
  no `.coverage` artefact written.
- **Label:** wall-clock from the test run; absence of `.coverage`.
- **Falsified if:** coverage is still produced by the default `pytest` invocation.

`pyproject.toml` currently sets `addopts = "-ra -q --cov=tree_packing --cov-report=term-missing"`.
`LAB_NOTEBOOK.md`'s final refinement trace records concurrent pytest processes corrupting
the shared `.coverage` SQLite file. Remove `--cov` from `addopts` and add a dedicated
target. Coverage is a reporting concern, not a gate concern; making it default couples every
test invocation to a shared mutable file.

### H0.6 — A Makefile gives the runbook one interface

- **Kind:** structural
- **Predicted:** `make gate`, `make baseline`, `make verify`, `make coverage` all succeed.
- **Label:** manual execution of each target; README updated to use them.
- **Falsified if:** any target fails or duplicates logic that lives elsewhere.

Targets should be thin wrappers over the existing `uv run` commands, not a second source of
truth. `make verify` runs the internal evaluator *and* the reference evaluator and compares.

### H0.7 — Dead code and lint noise are removed

- **Kind:** structural
- **Predicted:** the Gate stays green after the cleanup.
- **Label:** the Gate.
- **Falsified if:** any gate step regresses.

Two specific items:

- `cli.py::_evaluate` contains `overlap_errors.extend((n, len(pairs)) for _ in [0])`. This
  is a single append written as a generator over a one-element list. Replace with
  `overlap_errors.append((n, len(pairs)))`. Also correct the reporting: the "… and N more"
  line counts `overlap_configurations` while the loop iterates `overlap_errors`. Make both
  refer to the same collection.
- `[tool.ruff] extend-exclude` lists `"plan.md"` and `"documentary.md"`. Ruff does not lint
  Markdown; these entries are inert. Keep `"reference"` and `"challenge-files"`, drop the
  Markdown entries, and add `"plans"`.

---

## Exit gate

- [ ] Gate green: `ruff format --check`, `ruff check`, `mypy src`, `pytest`.
- [ ] CI green on a clean checkout of `main`.
- [ ] `git status --ignored` shows no tracked file matched by an ignore rule.
- [ ] `tests/unit/test_docs_links.py` passes; zero dead relative links.
- [ ] Every committed Markdown document is reachable from `README.md`.
- [ ] `uv run tree-packing evaluate data/submissions/baseline.csv` reports
      **exactly** `256.8197122633766779770234`.
- [ ] `uv run python reference/evaluator.py data/submissions/baseline.csv` reports
      `256.819712`, no overlaps.
- [ ] **TDD audit:** every structural sub-hypothesis has a `test(...)` commit preceding its
      `feat(...)` commit, and a `Red observed` field in `LAB_NOTEBOOK.md`.
- [ ] **Mutation spot-check** performed on one component and recorded.
- [ ] `LAB_NOTEBOOK.md` has one entry per sub-hypothesis H0.1–H0.7.
- [ ] `DECISIONS.md` gains a section on the ignore-rule repair and the coverage decoupling.
- [ ] `documentary.md` gains a dated M0 entry.
- [ ] `plans/README.md` M0 status updated.
- [ ] Tagged `v0.2-hygiene` with the score in the annotation.

---

## Notes for the executing agent

The score assertion is the whole point of this milestone. If it moves by even one digit,
something in the "harmless cleanup" was not harmless — stop and diagnose before proceeding.
Record the diagnosis as a REFINE entry; that is exactly the kind of finding the notebook
exists to capture.

**M0 is where TDD becomes auditable, so establish the convention here rather than at M1.**
H0.1, H0.2 and H0.3 each introduce a new test file, and each must follow the eight-step loop
in shared contract §2.0: write the test, run it, watch it fail, record the failure message,
then fix the repository. `test_docs_links.py` in particular should be red on first run —
`documentary.md`'s `challenge-files/` references guarantee it. If it comes back green before
you have fixed anything, the test is not walking the files it claims to walk.

Use the two-commit pattern from §2.5 (`test(M0.2): …` then `fix(M0.2): …`) from the very
first sub-hypothesis. Retrofitting commit granularity later is impossible, and it is the
strongest evidence available that the process was real.
