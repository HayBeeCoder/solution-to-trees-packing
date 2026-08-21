# M0 — Submission surface, reproducibility, and quality gates

**Score target:** `256.8197122633766779770234` — unchanged.
**Tag on completion:** `v0.2-hygiene`
**Estimated effort:** half a day.
**Start with H0.0** — roll back the in-progress CI work before anything else.

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

## H0.0 — Roll back the in-progress CI work

**Do this before anything else in M0.** Work on GitHub Actions was started under a previous
version of this plan. Continuous integration is now **optional and deferred** — see
"Optional: GitHub Actions" below for the conditions under which it is worth revisiting.

- **Kind:** structural
- **Predicted:** after the rollback, no CI configuration remains, the Gate is green, and the
  score is unchanged.
- **Label:** `git status` clean, `find . -name '*.yml' -path '*workflow*'` empty, score
  unchanged.
- **Falsified if:** any unrelated work is lost in the rollback.

### Step 1 — find out what exists

Do not delete blind. Establish the actual state first:

```bash
git status --porcelain
git log --oneline -n 10
git ls-files | grep -E '^\.github/|workflow|ci\.ya?ml'
ls -la .github/workflows/ 2>/dev/null
git diff HEAD --stat
```

### Step 2 — choose the rollback that matches the state

**If the CI work is uncommitted** (still in the working tree):

```bash
git checkout -- .github 2>/dev/null || true
rm -rf .github
git status --porcelain          # confirm nothing else was touched
```

**If the CI work is committed and is the most recent commit** — keep the changes on disk so
anything useful can be salvaged, then discard:

```bash
git log -1 --stat               # confirm the commit contains ONLY CI files
git reset --soft HEAD~1         # undo the commit, keep files staged
git restore --staged .github
rm -rf .github
```

**If the CI commit is not the tip**, or is mixed with wanted work — revert rather than
rewrite, so no other commit is disturbed:

```bash
git revert --no-commit <ci-sha>
git commit -m "revert: defer CI setup; clean-room reproduction replaces it (H0.0)"
```

**If it was already pushed**, always use `git revert`. Do not force-push — rewriting shared
history costs more than the commit is worth, and a clean revert with a stated reason reads
better to a reviewer than a hole in the history.

### Step 3 — remove the follow-on traces

```bash
grep -rn "actions/\|workflow\|badge\|CI\b" README.md DECISIONS.md documentary.md \
  LAB_NOTEBOOK.md 2>/dev/null
```

Delete any CI badge from `README.md` and any runbook step referencing Actions. If
`.pre-commit-config.yaml` gained CI-only hooks, remove those but **keep** the `pre-push`
stage — H0.4b needs it.

### Step 4 — record it honestly

Add a `LAB_NOTEBOOK.md` entry. This is a REFINE trace, and it is worth keeping rather than
erasing:

> **M0.0 — CI deferred.** Hypothesis: hosted CI provides reviewer-visible evidence of a
> green gate. **Refuted on re-examination**: the deliverable is a Drive folder, so Actions
> history is not visible to the reviewer, and the actual risk — environment assumptions
> that only hold locally — is addressed by clean-room reproduction (H0.4) and a local
> `pre-push` hook (H0.4b). Reverted `<sha>`. Cost: `<time spent>`.

A recorded decision that was reversed for a stated reason is stronger interview evidence
than one that was never questioned.

---

## H0 — Primary hypothesis

> The repository can be made fully self-describing and reproducible from a clean clone,
> without altering a single placement in the generated submission.

**Label:** the Gate is green, a clean-room clone reproduces the score, and
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

### H0.4 — The repository reproduces in a clean room, today

- **Kind:** structural
- **Predicted:** a fresh `git clone` into an empty directory, followed by `uv sync --locked`
  and `make verify`, reproduces `256.8197122633766779770234` on the first attempt.
- **Label:** the score printed by the clean-room run.
- **Falsified if:** any documented command fails, or the score differs by any amount.

This replaces what was previously specified as a CI job, and it is the check that actually
matters. The deliverable is a **Google Drive folder**, per the brief — a reviewer sees files,
not an Actions history. What can sink the submission is an environment assumption that only
holds on the development machine: a `uv` cache, a globally installed package, a Python patch
version, a path that exists locally.

The exposure here is real — `uv`, a pinned `uv.lock`, Python 3.12.9, an optional `viz`
extra, and `reference/evaluator.py` invoked as a subprocess. Any of these can work locally
for the wrong reason.

```bash
rm -rf /tmp/cleanroom && git clone . /tmp/cleanroom
cd /tmp/cleanroom && uv sync --locked && make verify
```

M6 runs this again as the final gate. Running it **now** means an environment defect costs
an hour on day one instead of the submission on day seven.

### H0.4b — The ratchet infrastructure exists locally

- **Kind:** structural
- **Predicted:** a `pre-push` hook runs `make verify` and blocks the push on failure.
- **Label:** manual falsification — break something, attempt a push, confirm it is refused.
- **Falsified if:** the push succeeds with a broken gate.

The Regression Gate (shared contract §4) has no content until M2, when there is a score to
protect. Its *plumbing* belongs here: add the `pre-push` hook to `.pre-commit-config.yaml`
under the `pre-push` stage, calling `make verify`. M2 fills in the score comparison.

This is local and needs no hosting. A hook that refuses the push is stronger protection than
a CI job that reports failure after the push has already landed.

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
- [ ] H0.0 rollback complete: no `.github/workflows/`, no CI badge, no unrelated work lost.
- [ ] Clean-room clone reproduces `256.8197122633766779770234` on first attempt.
- [ ] `pre-push` hook installed and falsified once (broken gate refuses the push).
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

## Optional: GitHub Actions

Deferred, not forbidden. Revisit **only after M2 has landed**, and only if all three hold:

- the repository stays on GitHub *and* the Drive README links to it, so a reviewer can
  actually reach the Actions tab;
- M0–M2 are green and tagged, so the schedule has slack;
- it can be done in under thirty minutes.

What it would add over the local hooks is narrow but real: dated proof that the gate passes
on a machine that has never seen the project, on every commit. That is a stronger claim than
"it passed when I ran it" — but it is a supporting claim, not the argument.

If added, keep it to one workflow: checkout, install `uv`, `uv sync --locked`, run the Gate,
then `make verify`. Do not let a misbehaving runner consume an afternoon that M3 needs.

---

## Notes for the executing agent

The score assertion is the whole point of this milestone. If it moves by even one digit,
something in the "harmless cleanup" was not harmless — stop and diagnose before proceeding.
Record the diagnosis as a REFINE entry; that is exactly the kind of finding the notebook
exists to capture.

Start with H0.0. Rolling back the CI work before touching anything else keeps the revert
diff clean and reviewable; entangling it with the hygiene fixes makes both harder to read.

**M0 is where TDD becomes auditable, so establish the convention here rather than at M1.**
H0.1, H0.2 and H0.3 each introduce a new test file, and each must follow the eight-step loop
in shared contract §2.0: write the test, run it, watch it fail, record the failure message,
then fix the repository. `test_docs_links.py` in particular should be red on first run —
`documentary.md`'s `challenge-files/` references guarantee it. If it comes back green before
you have fixed anything, the test is not walking the files it claims to walk.

Use the two-commit pattern from §2.5 (`test(M0.2): …` then `fix(M0.2): …`) from the very
first sub-hypothesis. Retrofitting commit granularity later is impossible, and it is the
strongest evidence available that the process was real.
