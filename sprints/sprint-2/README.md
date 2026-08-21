# Optimisation Programme — Plan Index

`plan.md` at the repository root specified the **scaffolding** and has been fully executed:
a typed, tested port of the official harness plus a deterministic grid baseline scoring
`256.8197122633766779770234`. It explicitly excluded an optimiser.

This directory specifies the **optimiser**. It is deliberately split into one document per
milestone so that each is a single, self-contained unit of work with its own hypothesis,
tests, exit gate, and git tag. Read `00-shared-contract.md` first; it holds every rule,
value, and schema the milestones share, so the milestone files never repeat them.

## How to use these documents

1. Read `00-shared-contract.md` in full. It is binding on every milestone.
2. Open the lowest-numbered milestone whose status below is not `DONE`.
3. Execute it under the six-step loop defined in the shared contract.
4. Do not begin milestone *k+1* until milestone *k*'s exit gate is green and tagged.

Milestones are strictly ordered. The ordering is not arbitrary — M2 must precede M3 or
the lattice will appear to deliver gains that the global rotation pass actually paid for,
and the M6 ablation will be confounded before it starts.

## Milestones

| # | Document | Theme | Score target | Status |
|---|---|---|---|---|
| M0 | [`M0-hygiene.md`](M0-hygiene.md) | Submission surface, clean-room repro, gates | `256.8197…` (unchanged) | DONE (`v0.2-hygiene`, `256.8197122633766779770234`) |
| M1 | [`M1-geometry-core.md`](M1-geometry-core.md) | Fast geometry, clearance, run ledger | `256.8197…` (unchanged) | DONE (`v0.3-core`, `256.8197122633766779770234`) |
| M2 | [`M2-free-wins.md`](M2-free-wins.md) | Tight grid, rotation, insertion, ratchet | ≤ 160 | TODO |
| M3 | [`M3-lattice.md`](M3-lattice.md) | Double-lattice backbone, n ≥ 21 | ≤ 110 | TODO |
| M4 | [`M4-compaction.md`](M4-compaction.md) | Compaction + basin-hopping | ≤ 85 | TODO |
| M5 | [`M5-small-n.md`](M5-small-n.md) | Dedicated search for n ≤ 20 | ≤ 82 | TODO |
| M6 | [`M6-ablation-freeze.md`](M6-ablation-freeze.md) | Ablation study, figures, freeze | — | TODO |

Update the Status column as part of each milestone's exit gate. `TODO` → `IN PROGRESS` →
`DONE (<tag>, score <value>)`.

## Test-driven development

Structural sub-hypotheses follow the eight-step loop in `00-shared-contract.md` §2.0:
write the test, run it, **observe it fail for the expected reason**, then implement, then
refactor under green tests. Each produces two commits — `test(...)` before `feat(...)` —
so a reviewer can verify test-first from `git log` without having been present.

Empirical sub-hypotheses cannot be test-driven; their equivalent discipline is the
mandatory `Falsified if` clause, which fixes the refutation condition before the
measurement is taken.

Every milestone exit gate carries a TDD audit and a mutation spot-check. See §2.5.

## Two milestones that change the score by zero

M0 and M1 are deliberately score-neutral, and their exit gates assert **identical** output
rather than improved output. This is the point: they are the milestones where a regression
would otherwise be invisible. M1 in particular replaces the geometry hot path, and the only
safe way to do that is to prove byte-equivalent scoring before anything depends on it.

## Time budget guidance

If the remaining calendar is tight, the milestones degrade gracefully in this order:
M5 is optional (worth ~2–4 points), M4 can ship with compaction but without basin-hopping,
and M3 can ship with a single hand-tuned lattice rather than a searched one. M0, M1, M2 and
M6 are not optional — M0 and M6 carry the assessment criteria that have nothing to do with
score, and M1/M2 are prerequisites for everything else being trustworthy.
