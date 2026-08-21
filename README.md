# Christmas Tree Packing baseline

This repository is a typed, tested port of the supplied Christmas Tree Packing
Challenge boilerplate. It intentionally contains only the deterministic grid
baseline; it does not implement an optimizer.

## Setup

Install [uv](https://docs.astral.sh/uv/) and use Python 3.12 or newer:

```bash
uv sync --locked
uv run pre-commit install --hook-type pre-push
```

Run the quality gates:

```bash
make gate
```

Generate and evaluate the baseline:

```bash
make baseline
make verify
```

`make verify` runs the quality gate, generates the baseline, checks it with the
package evaluator, then checks the written CSV with the official evaluator.
Use `make coverage` when a coverage report is needed; normal test runs do not
write shared coverage state.

The generated CSV contains 20,100 rows, covering every configuration from one
through 200 trees. The optional visualization command requires the extra:

```bash
uv sync --extra viz
uv run tree-packing visualize data/submissions/baseline.csv --n 10
```

The reference challenge files are retained in `reference/` for direct comparison.

## Documentation map

- [Active implementation plan](plan.md): completed baseline-scaffolding plan
  and its scientific execution methodology.
- [Sprint 1 plan](sprints/sprint-1/plan-with-agentic-as-science.md): the
  hypothesis-driven scaffolding methodology adopted by this repository.
- [Sprint 2 programme](sprints/sprint-2/README.md): ordered optimiser milestones.
  Start with the [shared contract](sprints/sprint-2/00-shared-contract.md), then
  work through [M0](sprints/sprint-2/M0-hygiene.md),
  [M1](sprints/sprint-2/M1-geometry-core.md),
  [M2](sprints/sprint-2/M2-free-wins.md),
  [M3](sprints/sprint-2/M3-lattice.md),
  [M4](sprints/sprint-2/M4-compaction.md),
  [M5](sprints/sprint-2/M5-small-n.md), and
  [M6](sprints/sprint-2/M6-ablation-freeze.md).
- [Baseline breakdown](baseline-breakdown.md): detailed architecture, data flow,
  and evaluator walkthrough.
- [Decisions](DECISIONS.md): implementation assumptions and trade-offs.
- [Lab notebook](LAB_NOTEBOOK.md): auditable hypotheses, observations, and
  refinements.
- [Documentary](documentary.md): chronological record of material execution and
  verification milestones.
- [Reference artifacts](reference/): unchanged challenge evaluator, baseline,
  challenge description, and sample submission.
