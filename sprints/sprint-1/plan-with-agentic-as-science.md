# Implementation Plan — Christmas Tree Packing Challenge (Scaffolding Only)

> **Audience:** a delegated implementation model (e.g. Claude Sonnet) that will build the
> repository exactly as described here.
> **Author intent:** stand up a clean, production-quality Python project that *replicates the
> boilerplate* provided in the challenge (`evaluator.py`, `simple_algorithm.py`,
> `christmas_tree_packing_challenge.md`) with proper tooling, structure, and tests.
>
> **This is an explicit non-goal document for optimization.** Do **not** implement simulated
> annealing, genetic algorithms, bottom-left fill, or any packing heuristic beyond the naive
> grid baseline that already ships in `simple_algorithm.py`. The deliverable is *infrastructure
> and a verified baseline*, nothing more.

---

## 0. Scope

### In scope
- A `uv`-managed Python project with `pyproject.toml`.
- Linting + formatting (`ruff`), type checking (`mypy --strict`), pre-commit hooks.
- A `src/` layout package `tree_packing` that cleanly separates:
  geometry, scoring, validation, baseline generation, serialization, and a CLI.
- A faithful port of the official evaluator logic so our internal gatekeeper agrees with
  `evaluator.py` byte-for-byte on geometry and overlap decisions.
- A full `pytest` suite (unit + integration) with concrete, pre-computed expected values.
- A `README.md` runbook and a short `DECISIONS.md` capturing assumptions/trade-offs.

### Explicitly out of scope
- Any packing optimizer or metaheuristic.
- Any change to the scoring formula or tree geometry.
- Producing a competitive submission. The only generated submission is the grid baseline.

---

## 1. Guiding principles

1. **Single source of truth for geometry.** The tree polygon is defined in exactly one place
   (`geometry.py`). Scoring and validation both import it. This guarantees the internal
   validator cannot disagree with the official evaluator about whether trees overlap.
2. **Faithful port, not a reinterpretation.** Constants (`SCALE_FACTOR = Decimal('1e15')`,
   `getcontext().prec = 25`, bounds `[-100, 100]`, the 15 vertices, and the grid `spacing = 1.1`)
   must be copied exactly from the boilerplate. Do not "improve" numeric handling.
3. **Pure functions, explicit types.** Every public function is typed and side-effect free
   except the serializer (file I/O) and the CLI (argument parsing / printing).
4. **Determinism.** The baseline is fully deterministic; tests assert exact/near-exact values.
5. **No hidden state.** No module-level mutable globals beyond immutable constants.

---

## 1a. Operating methodology — "Agentic Coding is Science"

The delegated model must build this repository as a **scientific process**, not straight-line
typing. Every module is a *hypothesis* about how to reproduce the official evaluator's behaviour;
the tests, quality gates, and the parity check against `reference/evaluator.py` are the *labels*
that confirm or falsify it. This project is unusually well-suited to the method because the ground
truth already exists — we are porting a known-correct harness, so "does it match?" is objectively
measurable.

### Core paradigms (mindset)
- **Code is data.** Treat each generated module and each test run as an observation, not a finished
  product. A failing `mypy`/`pytest`/parity run is a data point about the hypothesis, not a
  personal error to apologize for.
- **The agent is a stochastic generator.** Output can overfit (e.g. a port that passes one test but
  drifts from the evaluator geometry), generalize, or regress. Guard against overfitting with the
  parity test (§5.9) and the known-good values table (§8).
- **Evals are labels.** The gate — `ruff format --check`, `ruff check`, `mypy --strict`, `pytest` —
  plus the reference cross-check, is the supervision signal. A green gate is a correct label; a red
  gate is a corrective label. Do not advance a step on an unlabeled (untested) module.

### The six-step loop (run once per numbered step in §6)
1. **HYPOTHESIZE** — State plainly what should work and why, and *name the label that will decide
   it* (which test file / gate / known-good value). No code yet.
2. **GENERATE** — Produce the candidate module/tests from the hypothesis (the reference
   implementations in §4/§5 are the intended target).
3. **RUN / OBSERVE** — Execute the gate in the sandbox; capture the actual traces, not a guess at
   them.
4. **MEASURE** — Compare traces to the labels: does it lint, type-check, and pass every listed
   assertion with the exact expected values?
5. **SELECT** — Keep the candidate only if fully labeled green; otherwise reject it.
6. **REFINE** — On failure, diagnose *why the hypothesis was wrong* (e.g. vertex order flipped,
   scale applied twice, `touches` vs `intersects` confused), state a corrected hypothesis, and
   return to step 1. Never patch blindly.

### Rules of engagement (for the delegated model)
- Never jump to **Generate** without an explicit, written **Hypothesis** naming its label.
- On a red gate at **Run/Observe** or **Measure**, do not apologize-and-guess. Go to **Refine**,
  explain the root cause, and state the new hypothesis *before* regenerating.
- Prefix each working turn with the current phase, e.g. `**[HYPOTHESIZE]**`, `**[MEASURE]**`.
- Record every hypothesis and its outcome in `LAB_NOTEBOOK.md` (see §2, §7) so the process is
  reviewable at the interview.

---

## 2. Target repository layout

```
tree-packing/
├── pyproject.toml
├── uv.lock                      # generated by `uv lock` / `uv sync`
├── .python-version              # "3.12"
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
├── DECISIONS.md                 # assumptions & trade-offs (interview-facing)
├── LAB_NOTEBOOK.md              # hypothesis ledger: one entry per §6 loop iteration
├── plan.md                      # this file
├── data/
│   └── submissions/             # generated CSVs land here (git-ignored)
│       └── .gitkeep
├── src/
│   └── tree_packing/
│       ├── __init__.py
│       ├── py.typed             # PEP 561 marker (mypy strict)
│       ├── config.py            # all constants (scale, bounds, tree dims)
│       ├── geometry.py          # canonical tree polygon (port of evaluator)
│       ├── scoring.py           # bounding box side + per-config + total score
│       ├── validation.py        # overlap detection + submission validation
│       ├── baseline.py          # naive grid placement (port of simple_algorithm)
│       ├── serialization.py     # s-prefixed CSV read/write
│       ├── visualization.py     # optional matplotlib rendering (thin wrapper)
│       └── cli.py               # argparse entry point: generate / evaluate / visualize
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_config.py
    ├── test_geometry.py
    ├── test_scoring.py
    ├── test_validation.py
    ├── test_baseline.py
    ├── test_serialization.py
    └── test_integration.py
```

Keep the original boilerplate files (`evaluator.py`, `simple_algorithm.py`,
`christmas_tree_packing_challenge.md`, `sample_solution.csv`) untouched at the repo root under a
`reference/` folder so reviewers can diff our port against the source of truth.

---

## 3. Environment & tooling

### 3.1 `pyproject.toml`

Create it verbatim (bump patch versions only if resolution fails):

```toml
[project]
name = "tree-packing"
version = "0.1.0"
description = "Scaffolding and verified baseline for the Christmas Tree Packing Challenge."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "pandas>=2.2",
    "shapely>=2.0",
]

[project.optional-dependencies]
viz = ["matplotlib>=3.8"]

[project.scripts]
tree-packing = "tree_packing.cli:main"

[dependency-groups]
dev = [
    "pytest>=8.2",
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "mypy>=1.11",
    "pandas-stubs",
    "pre-commit>=3.8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/tree_packing"]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM", "PTH", "RUF"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]        # asserts are expected in tests

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true
disallow_untyped_defs = true
ignore_missing_imports = true   # shapely ships partial stubs

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q --cov=tree_packing --cov-report=term-missing"
```

### 3.2 Other config files

`.python-version`
```
3.12
```

`.gitignore`
```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
data/submissions/*.csv
```

`.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies: [pandas-stubs]
        args: [--strict]
        files: ^src/
```

### 3.3 Bootstrap commands (document these in README)

```bash
# 1. create the project & virtualenv
uv sync                       # resolves deps, creates .venv, writes uv.lock

# 2. install git hooks
uv run pre-commit install

# 3. quality gates
uv run ruff format .
uv run ruff check .
uv run mypy src
uv run pytest

# 4. produce the baseline submission
uv run tree-packing generate --output data/submissions/baseline.csv

# 5. score it with our port (and cross-check against the reference evaluator)
uv run tree-packing evaluate data/submissions/baseline.csv
uv run python reference/evaluator.py data/submissions/baseline.csv
```

---

## 4. Module specifications (reference implementations)

The code below is the intended implementation. It is a direct, typed port of the boilerplate.
Implement it as written; only adjust imports/formatting if `ruff`/`mypy` demand it.

### 4.1 `src/tree_packing/config.py`

```python
"""Immutable constants shared across the package.

Every numeric constant is copied verbatim from the official ``evaluator.py`` and
``simple_algorithm.py`` so that our tooling matches the grading harness exactly.
"""

from __future__ import annotations

from decimal import Decimal

# --- Precision -------------------------------------------------------------
DECIMAL_PRECISION = 25
SCALE_FACTOR = Decimal("1e15")

# --- Coordinate bounds enforced by the evaluator ---------------------------
MIN_COORD = -100
MAX_COORD = 100

# --- Configuration range ---------------------------------------------------
MIN_TREES = 1
MAX_TREES = 200

# --- Baseline grid ---------------------------------------------------------
GRID_SPACING = 1.1

# --- Tree geometry (unscaled, centred on the origin) -----------------------
TRUNK_WIDTH = Decimal("0.15")
TRUNK_HEIGHT = Decimal("0.2")
BASE_WIDTH = Decimal("0.7")
MID_WIDTH = Decimal("0.4")
TOP_WIDTH = Decimal("0.25")

TIP_Y = Decimal("0.8")
TIER_1_Y = Decimal("0.5")
TIER_2_Y = Decimal("0.25")
BASE_Y = Decimal("0.0")
TRUNK_BOTTOM_Y = -TRUNK_HEIGHT
```

### 4.2 `src/tree_packing/geometry/core.py`

```python
"""Canonical Christmas-tree polygon construction.

Faithful re-implementation of ``create_tree_polygon`` from the official evaluator.
This is the single source of truth for the tree shape; scoring and validation both
import ``create_tree_polygon`` from here.
"""

from __future__ import annotations

from decimal import Decimal

from shapely import affinity
from shapely.geometry import Polygon

from tree_packing import config

_HALF = Decimal("2")
_QUARTER = Decimal("4")

Number = Decimal | float | str


def _scaled(value: Decimal) -> float:
    """Lift an unscaled decimal coordinate into Shapely's working space."""
    return float(value * config.SCALE_FACTOR)


def tree_vertices() -> list[tuple[float, float]]:
    """The 15 tree vertices in scaled space, starting at the tip, going clockwise."""
    return [
        (_scaled(Decimal("0.0")), _scaled(config.TIP_Y)),                    # tip
        (_scaled(config.TOP_WIDTH / _HALF), _scaled(config.TIER_1_Y)),       # R top outer
        (_scaled(config.TOP_WIDTH / _QUARTER), _scaled(config.TIER_1_Y)),    # R top inner
        (_scaled(config.MID_WIDTH / _HALF), _scaled(config.TIER_2_Y)),       # R mid outer
        (_scaled(config.MID_WIDTH / _QUARTER), _scaled(config.TIER_2_Y)),    # R mid inner
        (_scaled(config.BASE_WIDTH / _HALF), _scaled(config.BASE_Y)),        # R base
        (_scaled(config.TRUNK_WIDTH / _HALF), _scaled(config.BASE_Y)),       # R trunk top
        (_scaled(config.TRUNK_WIDTH / _HALF), _scaled(config.TRUNK_BOTTOM_Y)),  # R trunk bottom
        (_scaled(-(config.TRUNK_WIDTH / _HALF)), _scaled(config.TRUNK_BOTTOM_Y)),  # L trunk bottom
        (_scaled(-(config.TRUNK_WIDTH / _HALF)), _scaled(config.BASE_Y)),    # L trunk top
        (_scaled(-(config.BASE_WIDTH / _HALF)), _scaled(config.BASE_Y)),     # L base
        (_scaled(-(config.MID_WIDTH / _QUARTER)), _scaled(config.TIER_2_Y)), # L mid inner
        (_scaled(-(config.MID_WIDTH / _HALF)), _scaled(config.TIER_2_Y)),    # L mid outer
        (_scaled(-(config.TOP_WIDTH / _QUARTER)), _scaled(config.TIER_1_Y)), # L top inner
        (_scaled(-(config.TOP_WIDTH / _HALF)), _scaled(config.TIER_1_Y)),    # L top outer
    ]


def create_tree_polygon(center_x: Number, center_y: Number, angle: Number) -> Polygon:
    """Return a tree polygon at ``(center_x, center_y)`` rotated by ``angle`` degrees.

    Rotation is applied about the origin first, then translation — matching the
    official evaluator exactly.
    """
    cx = Decimal(str(center_x))
    cy = Decimal(str(center_y))
    ang = Decimal(str(angle))

    polygon = Polygon(tree_vertices())
    rotated = affinity.rotate(polygon, float(ang), origin=(0, 0))
    return affinity.translate(
        rotated,
        xoff=float(cx * config.SCALE_FACTOR),
        yoff=float(cy * config.SCALE_FACTOR),
    )
```

### 4.3 `src/tree_packing/scoring.py`

```python
"""Bounding-box and score computation (port of the evaluator's scoring path)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, getcontext

from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from tree_packing import config

getcontext().prec = config.DECIMAL_PRECISION


def bounding_box_side(polygons: Sequence[BaseGeometry]) -> Decimal:
    """Side length of the smallest *square* enclosing all polygons (unscaled)."""
    if not polygons:
        return Decimal("0")

    minx, miny, maxx, maxy = unary_union(list(polygons)).bounds
    width = Decimal(str(maxx)) / config.SCALE_FACTOR - Decimal(str(minx)) / config.SCALE_FACTOR
    height = Decimal(str(maxy)) / config.SCALE_FACTOR - Decimal(str(miny)) / config.SCALE_FACTOR
    return max(width, height)


def configuration_score(side: Decimal, n: int) -> Decimal:
    """Normalized score s_n^2 / n for one configuration."""
    return (side * side) / Decimal(n)
```

### 4.4 `src/tree_packing/validation/overlap.py`

```python
"""Overlap detection and submission-level validation (port of evaluator checks)."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from tree_packing import config


def find_overlapping_pairs(polygons: Sequence[BaseGeometry]) -> list[tuple[int, int]]:
    """Return index pairs (i, j) that intersect without merely touching."""
    if len(polygons) <= 1:
        return []

    index = STRtree(list(polygons))
    pairs: list[tuple[int, int]] = []
    for i, poly in enumerate(polygons):
        for j in index.query(poly):
            if j <= i:
                continue
            if poly.intersects(polygons[j]) and not poly.touches(polygons[j]):
                pairs.append((i, j))
    return pairs


def has_overlap(polygons: Sequence[BaseGeometry]) -> bool:
    return len(find_overlapping_pairs(polygons)) > 0


def validate_submission_frame(df: pd.DataFrame) -> list[str]:
    """Structural validation: completeness of (n, tree_idx) and coordinate bounds.

    Returns a list of human-readable error strings (empty == valid).
    """
    errors: list[str] = []

    expected = {(n, t) for n in range(config.MIN_TREES, config.MAX_TREES + 1) for t in range(n)}
    actual = set(zip(df["n"], df["tree_idx"], strict=True))

    if missing := expected - actual:
        errors.append(f"Missing {len(missing)} tree entries, e.g. {sorted(missing)[:5]}")
    if extra := actual - expected:
        errors.append(f"Unexpected {len(extra)} tree entries, e.g. {sorted(extra)[:5]}")

    out_of_bounds = df[
        (df["x"] < config.MIN_COORD)
        | (df["x"] > config.MAX_COORD)
        | (df["y"] < config.MIN_COORD)
        | (df["y"] > config.MAX_COORD)
    ]
    if len(out_of_bounds) > 0:
        errors.append(
            f"{len(out_of_bounds)} trees outside [{config.MIN_COORD}, {config.MAX_COORD}]"
        )

    return errors
```

### 4.5 `src/tree_packing/baseline.py`

```python
"""Naive grid baseline (port of ``simple_algorithm.py``). No optimization."""

from __future__ import annotations

import math

from tree_packing import config

Placement = tuple[float, float, float]  # (x, y, deg)


def grid_positions(n: int, spacing: float = config.GRID_SPACING) -> list[Placement]:
    """Place ``n`` trees on a centred square-ish grid with zero rotation."""
    if n <= 0:
        return []

    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    placements: list[Placement] = []
    for row in range(rows):
        for col in range(cols):
            if len(placements) >= n:
                break
            x = (col - (cols - 1) / 2) * spacing
            y = (row - (rows - 1) / 2) * spacing
            placements.append((x, y, 0.0))
    return placements


def build_baseline() -> dict[int, list[Placement]]:
    """All 200 grid configurations keyed by tree count."""
    return {n: grid_positions(n) for n in range(config.MIN_TREES, config.MAX_TREES + 1)}
```

### 4.6 `src/tree_packing/serialization.py`

```python
"""Read/write the s-prefixed submission CSV format."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from tree_packing import config

Placement = tuple[float, float, float]


def format_value(value: float) -> str:
    """Numeric -> submission string, e.g. 1.5 -> 's1.5'."""
    return f"s{value}"


def parse_value(value: str | float) -> float:
    """Submission string -> float, tolerating the 's' prefix."""
    if isinstance(value, str) and value.startswith("s"):
        return float(value[1:])
    return float(value)


def write_submission(solutions: Mapping[int, Sequence[Placement]], path: str | Path) -> None:
    """Serialize {n: [(x, y, deg), ...]} to the official CSV layout."""
    rows = [
        {
            "id": f"{n:03d}_{t}",
            "x": format_value(x),
            "y": format_value(y),
            "deg": format_value(deg),
        }
        for n in range(config.MIN_TREES, config.MAX_TREES + 1)
        for t, (x, y, deg) in enumerate(solutions[n])
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["id", "x", "y", "deg"]).to_csv(out, index=False)


def load_submission(path: str | Path) -> pd.DataFrame:
    """Parse a submission CSV into columns: n, tree_idx, x, y, deg."""
    df = pd.read_csv(path, index_col="id")
    records = []
    for idx, row in df.iterrows():
        n_str, t_str = str(idx).split("_")
        records.append(
            {
                "n": int(n_str),
                "tree_idx": int(t_str),
                "x": parse_value(row["x"]),
                "y": parse_value(row["y"]),
                "deg": parse_value(row["deg"]),
            }
        )
    return pd.DataFrame(records)
```

### 4.7 `src/tree_packing/visualization.py`

Thin, optional wrapper around matplotlib. Guard the import so the core package never hard-depends
on `viz`. Implement `plot_configuration(df: pd.DataFrame, n: int) -> None` mirroring the evaluator's
`visualize_configuration` (draw each polygon and the red dashed bounding square). Raise a clear
`ImportError` message pointing to `uv sync --extra viz` if matplotlib is missing.

### 4.8 `src/tree_packing/cli.py`

`argparse` with three subcommands. Keep it thin — all logic lives in the modules above.

```
tree-packing generate  [--output PATH]        # build grid baseline -> write_submission
tree-packing evaluate  SUBMISSION [--quiet]   # load -> validate frame -> per-n overlap + score
tree-packing visualize SUBMISSION --n N       # delegate to visualization.plot_configuration
```

`evaluate` must:
1. `load_submission` then `validate_submission_frame`; abort with exit code 1 on structural errors.
2. For each `n` in 1..200, build polygons via `create_tree_polygon`, collect `find_overlapping_pairs`.
3. If any overlaps: print offending `n` values, exit code 1.
4. Otherwise sum `configuration_score(bounding_box_side(polys), n)` and print the total.

`main()` returns an `int` exit code and is the `[project.scripts]` entry point.

---

## 5. Test plan

All expected numeric values below were computed from the reference geometry and are exact unless
marked approximate. Tests must live in `tests/` and pass under `uv run pytest`.

### 5.1 `tests/conftest.py`

```python
import pytest
from tree_packing.geometry import create_tree_polygon


@pytest.fixture
def origin_tree():
    return create_tree_polygon(0, 0, 0)
```

### 5.2 `tests/test_config.py`
- `SCALE_FACTOR == Decimal("1e15")` and `DECIMAL_PRECISION == 25`.
- Bounds are exactly `-100` / `100`; tree range is `1` / `200`; `GRID_SPACING == 1.1`.

### 5.3 `tests/test_geometry.py`

```python
from decimal import Decimal
from tree_packing.config import SCALE_FACTOR
from tree_packing.geometry import create_tree_polygon, tree_vertices


def test_has_fifteen_vertices():
    assert len(tree_vertices()) == 15


def test_polygon_is_valid(origin_tree):
    assert origin_tree.is_valid


def test_unscaled_area(origin_tree):
    area = origin_tree.area / float(SCALE_FACTOR) ** 2
    assert area == pytest.approx(0.245625, rel=1e-9)  # exact tree area


def test_unscaled_bounds(origin_tree):
    minx, miny, maxx, maxy = (Decimal(str(b)) / SCALE_FACTOR for b in origin_tree.bounds)
    assert (minx, miny, maxx, maxy) == (
        Decimal("-0.35"), Decimal("-0.2"), Decimal("0.35"), Decimal("0.8"),
    )


def test_translation_moves_centroid():
    a = create_tree_polygon(0, 0, 0)
    b = create_tree_polygon(5, 0, 0)
    shift = (b.centroid.x - a.centroid.x) / float(SCALE_FACTOR)
    assert shift == pytest.approx(5.0, rel=1e-9)


def test_vertical_symmetry(origin_tree):
    minx, _, maxx, _ = origin_tree.bounds
    assert (minx + maxx) == pytest.approx(0.0, abs=1.0)  # symmetric about x=0
```
(Add `import pytest` at the top.)

### 5.4 `tests/test_scoring.py`

```python
from decimal import Decimal
from tree_packing.geometry import create_tree_polygon
from tree_packing.scoring import bounding_box_side, configuration_score


def test_single_tree_side_is_one():
    side = bounding_box_side([create_tree_polygon(0, 0, 0)])
    assert abs(side - Decimal("1.0")) < Decimal("1e-9")


def test_single_tree_score_is_one():
    side = bounding_box_side([create_tree_polygon(0, 0, 0)])
    assert abs(configuration_score(side, 1) - Decimal("1.0")) < Decimal("1e-9")


def test_empty_returns_zero():
    assert bounding_box_side([]) == Decimal("0")


def test_score_normalizes_by_n():
    assert configuration_score(Decimal("2.0"), 4) == Decimal("1.0")  # 2^2 / 4
```

### 5.5 `tests/test_validation.py`

```python
from tree_packing.geometry import create_tree_polygon
from tree_packing.validation import find_overlapping_pairs, has_overlap


def test_identical_trees_overlap():
    polys = [create_tree_polygon(0, 0, 0), create_tree_polygon(0, 0, 0)]
    assert has_overlap(polys)
    assert find_overlapping_pairs(polys) == [(0, 1)]


def test_far_apart_trees_do_not_overlap():
    polys = [create_tree_polygon(0, 0, 0), create_tree_polygon(5, 0, 0)]
    assert not has_overlap(polys)


def test_single_polygon_never_overlaps():
    assert find_overlapping_pairs([create_tree_polygon(0, 0, 0)]) == []
```

Add a submission-frame test that builds a tiny valid frame and asserts
`validate_submission_frame` flags out-of-bounds coordinates and missing entries.

### 5.6 `tests/test_baseline.py`

```python
from tree_packing.baseline import build_baseline, grid_positions
from tree_packing.geometry import create_tree_polygon
from tree_packing.validation import has_overlap


def test_single_tree_at_origin():
    assert grid_positions(1) == [(0.0, 0.0, 0.0)]


def test_zero_returns_empty():
    assert grid_positions(0) == []


def test_count_matches_n():
    for n in (1, 2, 7, 25, 100, 200):
        assert len(grid_positions(n)) == n


def test_grid_never_overlaps():
    for n in (1, 2, 4, 9, 16, 25):
        polys = [create_tree_polygon(x, y, d) for x, y, d in grid_positions(n)]
        assert not has_overlap(polys)


def test_build_baseline_covers_all_configs():
    baseline = build_baseline()
    assert sorted(baseline) == list(range(1, 201))
    assert sum(len(v) for v in baseline.values()) == 20100
```

### 5.7 `tests/test_serialization.py`

```python
from tree_packing.serialization import format_value, load_submission, parse_value, write_submission


def test_format_round_trip():
    assert parse_value(format_value(-0.123456)) == -0.123456


def test_parse_tolerates_plain_float():
    assert parse_value(1.5) == 1.5


def test_write_then_load(tmp_path):
    solutions = {n: [(0.0, 0.0, 0.0)] * n for n in range(1, 201)}
    out = tmp_path / "sub.csv"
    write_submission(solutions, out)
    df = load_submission(out)
    assert len(df) == 20100
    assert set(df["n"]) == set(range(1, 201))
    row = df[(df["n"] == 3) & (df["tree_idx"] == 2)].iloc[0]
    assert (row["x"], row["y"], row["deg"]) == (0.0, 0.0, 0.0)
```

### 5.8 `tests/test_integration.py`

End-to-end on the generated baseline, but **restrict the heavy overlap/score loop to small n**
(1..20) to keep CI fast; assert the whole frame is structurally valid across all 200.

```python
from decimal import Decimal
from tree_packing.baseline import build_baseline
from tree_packing.geometry import create_tree_polygon
from tree_packing.scoring import bounding_box_side, configuration_score
from tree_packing.serialization import load_submission, write_submission
from tree_packing.validation import find_overlapping_pairs, validate_submission_frame


def test_baseline_is_structurally_valid(tmp_path):
    out = tmp_path / "baseline.csv"
    write_submission(build_baseline(), out)
    df = load_submission(out)
    assert validate_submission_frame(df) == []


def test_baseline_small_n_no_overlap_and_scores(tmp_path):
    out = tmp_path / "baseline.csv"
    write_submission(build_baseline(), out)
    df = load_submission(out)

    total = Decimal("0")
    for n in range(1, 21):
        cfg = df[df["n"] == n]
        polys = [create_tree_polygon(r.x, r.y, r.deg) for r in cfg.itertuples()]
        assert find_overlapping_pairs(polys) == []
        total += configuration_score(bounding_box_side(polys), n)

    assert total > 0
    # n=1 contributes exactly 1.0
    n1 = df[df["n"] == 1]
    side = bounding_box_side([create_tree_polygon(r.x, r.y, r.deg) for r in n1.itertuples()])
    assert abs(configuration_score(side, 1) - Decimal("1.0")) < Decimal("1e-9")
```

### 5.9 Parity test (optional but recommended)

Add `test_parity_with_reference.py` that imports `reference/evaluator.py`'s `create_tree_polygon`
and asserts our polygon and theirs are geometrically equal (`our.equals(theirs)`), proving the
port is faithful. This is the strongest guarantee for the interview.

---

## 6. Implementation order — one scientific loop per step

Each numbered step is **one full iteration** of the six-step loop from §1a. Run them strictly in
order. A step is not "done" until its **label** (the named gate/test) is green; only then may the
next hypothesis begin. Log each iteration in `LAB_NOTEBOOK.md`.

### Per-step loop template (apply to every step below)

```
[HYPOTHESIZE] <what should work> — decided by <the named label: gate / test file / known-good value>
[GENERATE]    <the module + its tests, targeting §4 / §5>
[RUN/OBSERVE] uv run ruff format --check . && uv run ruff check . && uv run mypy src && uv run pytest <scope>
[MEASURE]     lint clean? types clean? every listed assertion green with the exact expected values?
[SELECT]      keep iff fully green; else reject the candidate
[REFINE]      on red: state the root cause + corrected hypothesis, return to HYPOTHESIZE
```

The **Gate** referenced everywhere is:
`uv run ruff format . && uv run ruff check . && uv run mypy src && uv run pytest`

### The steps (each = one iteration)

| # | Hypothesis (what should work) | Label that decides it |
|---|---|---|
| 1 | `uv sync` resolves deps and creates `.venv` + `uv.lock`; scaffold files are well-formed. | `uv sync` exits 0; `uv run python -c "import shapely, pandas"` |
| 2 | The four boilerplate files sit unchanged under `reference/` for diffing. | `git diff` shows no content change; files import cleanly |
| 3 | The `tree_packing` package is importable with `py.typed`. | `uv run python -c "import tree_packing"`; `mypy src` finds the marker |
| 4 | `config.py` exposes every constant verbatim from the boilerplate. | `test_config.py` + Gate |
| 5 | `geometry.py` reproduces the evaluator's polygon exactly. | `test_geometry.py` **and** the §5.9 parity test + Gate |
| 6 | `scoring.py` yields `s_1 = 1.0`, `score(n=1) = 1.0`, `2²/4 = 1.0`. | `test_scoring.py` + Gate |
| 7 | `validation.py` flags true overlaps and clears touching/far-apart trees. | `test_validation.py` + Gate |
| 8 | `baseline.py` grid is complete (20100) and overlap-free for sampled n. | `test_baseline.py` + Gate |
| 9 | `serialization.py` round-trips the s-prefixed format losslessly. | `test_serialization.py` + Gate |
| 10 | `visualization.py` imports lazily and fails loudly without `viz`. | manual: run with/without `--extra viz`; `mypy src` |
| 11 | `cli.py` `generate`/`evaluate` run end-to-end via `[project.scripts]`. | manual `generate` then `evaluate` on the output |
| 12 | The full baseline is structurally valid; small-n scores are finite. | `test_integration.py` + Gate |
| 13 | Docs reproduce the flow from a clean clone. | manual walk-through of README runbook |
| 14 | The whole system is green end-to-end. | **full Gate** + reference cross-check (§8) |

**Overfitting guard (step 5 is the critical one).** A port can pass `test_geometry.py` while still
diverging from the evaluator (wrong winding, double-scaling, off-by-one vertex). The parity test in
§5.9 is the label that catches this — treat a green unit test *without* a green parity test as an
**unlabeled** result and do not SELECT it.

---

## 7. `DECISIONS.md` content (interview-facing)

Capture, in short prose:
- **Faithful port over reinvention** — why constants are copied verbatim and geometry lives in one
  module (guarantees internal validator == official evaluator).
- **`src/` layout + `uv`** — isolation, reproducible lockfile, single entry point.
- **Decimal + `1e15` scale factor** — why sub-unit coordinates are lifted before hitting Shapely's
  float64 predicates, and how this protects overlap decisions from floating-point noise.
- **Scope boundary** — deliberately no optimizer; the grid baseline is the reference point a future
  optimizer would be measured against. Note the score-weighting `s_n^2 / n` as the metric an
  optimizer would target, without implementing one.
- **Testing philosophy** — exact expected values where the math is closed-form (`area = 0.245625`,
  `s_1 = 1.0`), small-`n` integration to keep CI fast, and a parity test against the reference.
- **Process: "Agentic Coding is Science" (§1a)** — the build was run as hypothesis → generate →
  run/observe → measure → select → refine, with the quality gate and reference parity acting as the
  labels. Point reviewers to `LAB_NOTEBOOK.md` as evidence of disciplined, falsifiable engineering
  rather than guess-and-check.

### `LAB_NOTEBOOK.md` template (one entry per §6 iteration)

```markdown
## Step <n> — <module / concern>

- **Hypothesis:** <what should work> — label: <test file / gate / known-good value>
- **Generated:** <files touched>
- **Observed:** <key trace: pass/fail counts, error type if any>
- **Measured:** <label result — green/red, which assertions>
- **Selected / Refined:** <kept, or root cause + corrected hypothesis>
```

Keep entries terse. The value is the *chain of reasoning*, especially any REFINE loops — a recorded
failure that was diagnosed and fixed is stronger interview evidence than a clean first pass.

---

## 8. Definition of Done (acceptance checklist)

- [ ] `uv sync` succeeds and produces `uv.lock`.
- [ ] `uv run ruff format --check .` reports no changes needed.
- [ ] `uv run ruff check .` passes with zero findings.
- [ ] `uv run mypy src` passes under `--strict`.
- [ ] `uv run pytest` passes with 100% of listed tests green.
- [ ] `uv run tree-packing generate --output data/submissions/baseline.csv` writes exactly
      20,100 data rows + header.
- [ ] `uv run tree-packing evaluate data/submissions/baseline.csv` reports **no overlaps** and a
      finite total score.
- [ ] `uv run python reference/evaluator.py data/submissions/baseline.csv` agrees (no overlaps;
      same score to full Decimal precision).
- [ ] `README.md` runbook reproduces the whole flow from a clean clone.
- [ ] No packing optimizer of any kind is present.

---

### Known-good reference values (do not change without recomputing)

| Quantity | Value |
|---|---|
| Tree vertex count | 15 |
| Unscaled tree area | 0.245625 |
| Unscaled bounds (minx, miny, maxx, maxy) | (-0.35, -0.2, 0.35, 0.8) |
| Single-tree square side `s_1` | 1.0 |
| Score contribution at `n=1` | 1.0 |
| Total baseline rows | 20100 |
| Grid spacing | 1.1 (zero overlaps for all n) |