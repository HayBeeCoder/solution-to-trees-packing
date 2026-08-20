# Christmas Tree Packing: Baseline Implementation Breakdown

This document explains the challenge, the repository, and the complete baseline
execution path. It is written from the code that is actually present in this
folder, with the retained reference evaluator treated as the behavioral source
of truth.

The short version is:

> This repository is a faithful, typed, tested port of a deliberately simple
> grid baseline. It can produce a valid submission and score it, but it does
> not contain a packing optimizer.

The most useful way to read this document is in three passes:

1. Understand the mathematical problem and what a submission means.
2. Follow the data from placements to CSV to polygons to score.
3. Read the modules and tests as concrete implementations of that flow.

The practical walkthrough is near the end under [Running the baseline](#running-the-baseline).

## 1. The repository in one picture

There are two closely related systems in the folder:

```text
Challenge source material
  challenge-files/christmas_tree_packing_challenge.md
  challenge-files/evaluator.py
  challenge-files/simple_algorithm.py
          |
          | retained unchanged for comparison
          v
Reference artifacts
  reference/christmas_tree_packing_challenge.md
  reference/evaluator.py
  reference/simple_algorithm.py
  reference/sample_solution.csv
          |
          | faithful typed decomposition
          v
tree_packing package
  config -> geometry -> scoring / validation
      baseline -> serialization -> CLI
                              |
                              v
                  data/submissions/baseline.csv
```

The core runtime path is:

```text
placements
  -> write_submission()
  -> CSV with id,x,y,deg
  -> load_submission()
  -> DataFrame with n,tree_idx,x,y,deg
  -> validate_submission_frame()
  -> create_tree_polygon() for every tree
  -> STRtree overlap checks
  -> unary_union(...).bounds
  -> square side s_n
  -> s_n^2 / n
  -> sum over n = 1..200
```

The package source lives in [`src/tree_packing`](src/tree_packing). The official
behavior is retained in [`reference`](reference), and the tests live in
[`tests`](tests).

## 2. What challenge is being solved?

### 2.1 The object being packed

Each item is the same 2D polygon shaped like a stylized Christmas tree. A tree
can be moved and rotated. For each tree, the solver chooses:

```text
(x, y, deg)
```

where `x` and `y` are translations and `deg` is a rotation angle in degrees.

The challenge asks for a separate arrangement for every tree count:

```text
n = 1, 2, 3, ..., 200
```

This is important: the 10-tree problem and the 11-tree problem are scored as
independent configurations. The 11-tree layout does not need to contain the
10-tree layout, and the code correctly stores a separate placement list for
each `n`.

### 2.2 Validity constraints

For every configuration:

1. There must be exactly `n` tree records.
2. No two tree polygons may have a positive-area overlap.
3. Trees are allowed to touch along an edge or at a point.
4. Each submitted center coordinate must satisfy `-100 <= x <= 100` and
   `-100 <= y <= 100`.

The coordinate rule is applied to the submitted centers, not to every point of
the transformed polygon. A tree center can be within the bounds while a tip or
branch extends beyond them; that is what the evaluator checks.

The submission must contain one row for each pair `(n, tree_idx)`, where
`tree_idx` runs from `0` to `n - 1`. Therefore the number of data rows is:

```text
1 + 2 + ... + 200
= 200 * 201 / 2
= 20,100
```

### 2.3 Objective function

For a fixed configuration `n`, let:

```text
s_n = side length of the square enclosing all n transformed polygons
```

The contribution of that configuration is:

```text
configuration_score(n) = s_n^2 / n
```

The final objective is:

```text
total_score = sum(s_n^2 / n for n in 1..200)
```

Lower is better.

The evaluator obtains `s_n` from the axis-aligned polygon bounds:

```text
width  = max_x - min_x
height = max_y - min_y
s_n    = max(width, height)
```

So despite the prose calling it a “smallest square,” this implementation does
not search over arbitrary square orientations. It uses the smallest
axis-aligned square whose sides cover the axis-aligned bounding rectangle.

### 2.4 Intuition for why it is an optimization problem

The tree is not a rectangle. Its stepped tiers create opportunities for one
tree to fit near another tree’s narrower region. Rotating a tree may let its
branches interlock with a neighbor, but rotation also changes the global
extreme points that determine the square side.

For a configuration with `n` trees, the search state has `3n` scalar variables:

```text
(x_0, y_0, deg_0, x_1, y_1, deg_1, ..., x_(n-1), y_(n-1), deg_(n-1))
```

The objective is discontinuous or difficult to optimize with ordinary
gradients because a tiny movement can create a collision, change which tree is
the leftmost/rightmost/topmost/bottommost object, or turn a legal touch into
an overlap due to numerical precision. That is why the challenge suggests
derivative-free methods such as simulated annealing or genetic search.

The current repository stops before that stage. Its purpose is to establish a
correct baseline and a trustworthy evaluator-compatible foundation.

## 3. The Christmas-tree polygon

### 3.1 Logical coordinates

The tree is first defined around the origin. Its full height is `1.0`, from
`y = -0.2` at the bottom of the trunk to `y = 0.8` at the tip. Its widest point
is `0.7` units across.

The exact 15 vertices used by the evaluator and by
[`geometry.py`](src/tree_packing/geometry.py) are:

| # | Coordinate | Meaning |
|---:|---|---|
| 1 | `(0.0, 0.8)` | tip |
| 2 | `(0.125, 0.5)` | right top-tier outer corner |
| 3 | `(0.0625, 0.5)` | right top-tier inner corner |
| 4 | `(0.2, 0.25)` | right middle-tier outer corner |
| 5 | `(0.1, 0.25)` | right middle-tier inner corner |
| 6 | `(0.35, 0.0)` | right bottom-tier outer corner |
| 7 | `(0.075, 0.0)` | right trunk top |
| 8 | `(0.075, -0.2)` | right trunk bottom |
| 9 | `(-0.075, -0.2)` | left trunk bottom |
| 10 | `(-0.075, 0.0)` | left trunk top |
| 11 | `(-0.35, 0.0)` | left bottom-tier outer corner |
| 12 | `(-0.1, 0.25)` | left middle-tier inner corner |
| 13 | `(-0.2, 0.25)` | left middle-tier outer corner |
| 14 | `(-0.0625, 0.5)` | left top-tier inner corner |
| 15 | `(-0.125, 0.5)` | left top-tier outer corner |

The path goes from the tip down the right side, around the trunk, and back up
the left side. The pairs of “outer” and “inner” points at the same height are
what make the branch tiers stepped instead of making one smooth triangle.

The dimensions are centralized in [`config.py`](src/tree_packing/config.py):

| Constant | Value | Role |
|---|---:|---|
| `TRUNK_WIDTH` | `0.15` | trunk width |
| `TRUNK_HEIGHT` | `0.2` | trunk height |
| `BASE_WIDTH` | `0.7` | bottom branch width |
| `MID_WIDTH` | `0.4` | middle branch width |
| `TOP_WIDTH` | `0.25` | top branch width |
| `TIP_Y` | `0.8` | tip height |
| `TIER_1_Y` | `0.5` | top-tier ledge height |
| `TIER_2_Y` | `0.25` | middle-tier ledge height |
| `BASE_Y` | `0.0` | branch/trunk join |
| `TRUNK_BOTTOM_Y` | `-0.2` | derived trunk bottom |

The unscaled reference facts tested in [`test_geometry.py`](tests/test_geometry.py)
are:

```text
vertex count = 15
area         = 0.245625
bounds       = (-0.35, -0.2, 0.35, 0.8)
```

The bounds immediately explain the single-tree score: the width is `0.7`, the
height is `1.0`, so a single unrotated tree needs a square of side `1.0` and
contributes `1.0^2 / 1 = 1.0`.

### 3.2 Transformation order

For a requested placement `(x, y, deg)`, the implementation does this:

```text
1. Build the tree at the origin.
2. Rotate the polygon by deg degrees around the origin.
3. Translate the rotated polygon by (x, y).
```

The order matters. Rotating around the origin before translating means `(x, y)`
is the tree’s reference-point translation, not the point around which the
rotation itself occurs. Both the package and the reference evaluator use
Shapely’s `affinity.rotate` followed by `affinity.translate`.

### 3.3 Why the code multiplies coordinates by `1e15`

The reference evaluator defines:

```python
SCALE_FACTOR = Decimal("1e15")
```

It converts the exact decimal dimensions to large floating-point coordinates
before giving them to Shapely. The package keeps that convention exactly:

```text
logical coordinate 0.35
        -> 0.35 * 1e15
        -> Shapely polygon coordinate
```

The scaling is not intended to make the tree physically larger. The scoring
code divides the resulting bounds by the same factor before calculating width
and height. It keeps the package’s geometry operations aligned with the
official harness and reduces the chance that very small separations are lost
before Shapely evaluates intersections.

The constructor accepts `Decimal`, `float`, or `str`. It first applies
`Decimal(str(value))`, which avoids turning a value such as the textual string
`"0.1"` into a binary-float approximation before scaling it.

### 3.4 Single source of truth

[`tree_vertices()`](src/tree_packing/geometry.py) is the one package-level
definition of the 15 scaled vertices. Both scoring and validation call
[`create_tree_polygon()`](src/tree_packing/geometry.py) rather than recreating
the tree independently.

[`test_parity_with_reference.py`](tests/test_parity_with_reference.py) imports
the reference evaluator dynamically and checks that the two polygons are
geometrically equal for origin, translated, and rotated examples. This is an
important guard against subtle errors such as:

- omitting one of the 15 vertices;
- reversing or changing the tier ledges;
- scaling twice;
- rotating after translation instead of before it;
- using a different rotation origin.

## 4. What is in each directory?

| Path | Purpose |
|---|---|
| [`src/tree_packing`](src/tree_packing) | typed reusable implementation |
| [`reference`](reference) | retained evaluator, challenge text, algorithm, and sample CSV |
| [`tests`](tests) | unit, integration, and reference-parity tests |
| [`data/submissions`](data/submissions) | generated submissions; CSVs are ignored |
| [`challenge-files`](challenge-files) | original challenge and planning artifacts present in the workspace |
| [`pyproject.toml`](pyproject.toml) | package metadata, dependencies, CLI entry point, and tool configuration |
| [`uv.lock`](uv.lock) | resolved dependency versions for reproducible setup |
| [`.python-version`](.python-version) | declares Python 3.12 |
| [`.pre-commit-config.yaml`](.pre-commit-config.yaml) | Ruff and mypy hooks |
| [`README.md`](README.md) | concise setup and command runbook |

There are also local process records—`DECISIONS.md`, `LAB_NOTEBOOK.md`, and
`documentary.md`—that explain how the repository was built and verified. They
are intentionally ignored by Git. The `challenge-files/` directory contains
the input artifacts and planning documents rather than runtime package code.

## 5. Module-by-module implementation

### 5.1 `config.py`: shared constants

[`config.py`](src/tree_packing/config.py) prevents the rest of the package from
scattering evaluator constants across multiple files.

It defines:

```text
DECIMAL_PRECISION = 25
SCALE_FACTOR      = Decimal("1e15")
MIN_COORD         = -100
MAX_COORD         = 100
MIN_TREES         = 1
MAX_TREES         = 200
GRID_SPACING      = 1.1
```

It also defines all unscaled tree dimensions listed in the geometry section.
`TRUNK_BOTTOM_Y` is derived from `-TRUNK_HEIGHT`, so changing the trunk height
keeps that relationship explicit.

The module has no functions and no mutable state. It is a constants module, and
the tests verify the values that control precision, bounds, problem size, and
the baseline spacing.

### 5.2 `geometry.py`: canonical polygon construction

[`geometry.py`](src/tree_packing/geometry.py) contains three useful concepts:

1. `Number` — the accepted input type alias (`Decimal | float | str`).
2. `_scaled(value)` — converts an unscaled `Decimal` into Shapely working space.
3. `tree_vertices()` and `create_tree_polygon()` — construct and transform the
   canonical tree.

`tree_vertices()` returns floats because Shapely’s polygon constructor operates
with floating-point coordinates. The values are created from Decimal arithmetic
first, so the intended decimal dimensions are preserved as far as the
reference implementation allows.

`create_tree_polygon(center_x, center_y, angle)`:

```text
cx  = Decimal(str(center_x))
cy  = Decimal(str(center_y))
ang = Decimal(str(angle))
polygon = Polygon(tree_vertices())
rotated = affinity.rotate(polygon, float(ang), origin=(0, 0))
return affinity.translate(rotated,
                          xoff=float(cx * SCALE_FACTOR),
                          yoff=float(cy * SCALE_FACTOR))
```

This function is the boundary between submission-level placement values and
geometry-level Shapely objects.

### 5.3 `baseline.py`: deterministic grid placement

[`baseline.py`](src/tree_packing/baseline.py) deliberately implements the
reference `simple_algorithm.py`, not an optimizer.

The public functions are:

```python
grid_positions(n: int, spacing: float = 1.1)
build_baseline()
```

For `grid_positions(n)`, the algorithm is:

```text
if n <= 0:
    return []

cols = ceil(sqrt(n))
rows = ceil(n / cols)

for row in 0 .. rows - 1:
    for col in 0 .. cols - 1:
        stop once n placements have been emitted

        x = (col - (cols - 1) / 2) * spacing
        y = (row - (rows - 1) / 2) * spacing
        deg = 0.0
```

The grid is centered around the origin. It is “square-ish” because the number
of columns is based on `sqrt(n)`, then rows are chosen to hold all trees.

Examples:

```text
n = 1: cols=1, rows=1
      (0.0, 0.0, 0.0)

n = 4: cols=2, rows=2
      (-0.55, -0.55), (0.55, -0.55)
      (-0.55,  0.55), (0.55,  0.55)

n = 5: cols=3, rows=2
      (-1.1, -0.55), (0.0, -0.55), (1.1, -0.55)
      (-1.1,  0.55), (0.0,  0.55)
```

The tree’s unrotated width is `0.7` and height is `1.0`. A center spacing of
`1.1` therefore leaves roughly `0.4` horizontal clearance and `0.1` vertical
clearance between neighboring axis-aligned trees. Diagonal neighbors are
farther apart in both axes. This is why the grid is safely valid, although it
leaves a lot of unused space.

The comment in the original reference algorithm says “use spacing of `0.8`,”
but the executable assignment is `spacing = 1.1`. The package follows the
executable value. This is a good general lesson for this challenge: the
reference evaluator and executable code outrank an inaccurate comment.

`build_baseline()` simply returns:

```python
{n: grid_positions(n) for n in range(1, 201)}
```

It produces 200 independent lists and exactly 20,100 placements in total.

### 5.4 `serialization.py`: placement data to and from CSV

[`serialization.py`](src/tree_packing/serialization.py) owns the submission
format.

#### Formatting and parsing values

```python
format_value(1.5)       # "s1.5"
parse_value("s-0.2")    # -0.2
parse_value(1.5)        # 1.5
```

The `s` prefix is removed before parsing. The parser also accepts an ordinary
numeric CSV value, matching the permissiveness of the reference evaluator.

#### Writing

`write_submission(solutions, path)` expects a mapping shaped like:

```text
{
    n: [(x, y, deg), (x, y, deg), ...],
    ...
}
```

It loops over `n = 1..200`, enumerates each placement to obtain `tree_idx`, and
writes rows in this order:

```csv
id,x,y,deg
001_0,s0.0,s0.0,s0.0
002_0,s-0.55,s0.0,s0.0
002_1,s0.55,s0.0,s0.0
```

The ID is built as `f"{n:03d}_{t}"`. The output directory is created if
needed, then pandas writes the header and data rows.

One small formatting detail is worth knowing: the package uses Python’s normal
float representation (`f"s{value}"`), while the original
[`reference/simple_algorithm.py`](reference/simple_algorithm.py) formats its
values with six decimal places. Both forms parse to the same intended
coordinates for this baseline; the package’s generated file can visibly
contain values such as `s6.6000000000000005`.

#### Loading

`load_submission(path)` reads `id` as the DataFrame index, splits each ID into
`n` and `tree_idx`, parses the three numeric fields, and returns a normalized
DataFrame with columns:

```text
n, tree_idx, x, y, deg
```

This normalized shape is the common input used by validation, scoring, and
visualization.

### 5.5 `validation.py`: structural and geometric checks

[`validation.py`](src/tree_packing/validation.py) has two layers.

#### Pairwise geometric collision detection

`find_overlapping_pairs(polygons)` uses Shapely’s `STRtree` spatial index.

The naive approach would compare all `n * (n - 1) / 2` pairs. Instead:

1. Put all polygons into an `STRtree`.
2. Query the index for polygons whose bounding boxes could intersect each
   polygon.
3. Ignore self-pairs and pairs already seen.
4. Apply the exact evaluator predicate:

```python
poly_a.intersects(poly_b) and not poly_a.touches(poly_b)
```

`intersects` alone would reject legal touching because touching counts as an
intersection in Shapely. The `not touches` clause distinguishes positive-area
overlap from boundary-only contact.

The function returns index pairs such as `[(0, 1)]`; `has_overlap()` is a
boolean convenience wrapper.

#### Submission-frame checks

`validate_submission_frame(df)` creates the full expected set:

```text
{(n, t) for n in 1..200 for t in 0..n-1}
```

It compares that set with the actual `(n, tree_idx)` pairs and reports missing
or unexpected entries. It also reports any `x` or `y` center outside
`[-100, 100]`.

The function returns human-readable error strings. An empty list means the
frame passed these structural checks.

The implementation intentionally mirrors the reference’s checks. It does not
independently impose an angle limit, and it does not check polygon validity in
the frame validator. The normal baseline path still creates valid polygons and
then runs the overlap check.

### 5.6 `scoring.py`: bounding square and normalized score

[`scoring.py`](src/tree_packing/scoring.py) contains the mathematical scoring
functions:

```python
bounding_box_side(polygons) -> Decimal
configuration_score(side, n) -> Decimal
```

`bounding_box_side()`:

1. Returns Decimal zero for an empty list.
2. Unions the polygons with `unary_union`.
3. Reads Shapely’s `(minx, miny, maxx, maxy)` bounds in scaled space.
4. Converts all bounds back to logical units by dividing by `SCALE_FACTOR`.
5. Computes `width` and `height`.
6. Returns `max(width, height)`.

The module sets the Decimal context precision to 25, matching the reference.
The final arithmetic is therefore Decimal arithmetic even though Shapely’s
polygon predicates use floats internally.

`configuration_score(side, n)` is intentionally small:

```python
return (side * side) / Decimal(n)
```

There is no package-level `total_score()` function. The CLI accumulates one
Decimal configuration score at a time across all 200 configurations.

### 5.7 `visualization.py`: optional inspection aid

[`visualization.py`](src/tree_packing/visualization.py) is not needed to
generate or score a submission. It imports matplotlib inside
`plot_configuration()` so the core package does not require the optional
visualization dependency just to run.

The function:

1. Filters the normalized DataFrame to one `n`.
2. Builds the polygons with the canonical geometry function.
3. Calculates the side and rectangle bounds.
4. Plots each tree in a different viridis color.
5. Draws the axis-aligned red dashed square used by the score.
6. Adds half a unit of visual padding and calls `plt.show()`.

If matplotlib is unavailable, it raises an actionable message telling the user
to run `uv sync --extra viz`.

The square is positioned so that the shorter rectangle dimension is centered
inside it. For example, if width is smaller than height, the extra square width
is split left and right around the polygon bounds.

### 5.8 `cli.py`: orchestration and user interface

[`cli.py`](src/tree_packing/cli.py) exposes the console script declared in
[`pyproject.toml`](pyproject.toml):

```toml
[project.scripts]
tree-packing = "tree_packing.cli:main"
```

The parser has three subcommands.

#### `generate`

```text
tree-packing generate --output path/to/baseline.csv
```

`_generate()` builds the baseline and writes it. It reports the output path and
the expected 20,100 data rows.

#### `evaluate`

```text
tree-packing evaluate path/to/submission.csv
tree-packing evaluate path/to/submission.csv --quiet
```

`_evaluate()` performs the full package-side evaluation:

1. Load and parse the CSV.
2. Reject file-loading errors.
3. Run structural validation.
4. For each `n = 1..200`, construct that configuration’s polygons.
5. Find overlap pairs.
6. Add its bounding-square score to the Decimal total.
7. Print progress every 20 configurations unless quiet.
8. Return a nonzero exit code if overlaps were found; otherwise print the total.

The CLI keeps orchestration here and leaves geometry, validation, scoring, and
serialization as reusable functions.

#### `visualize`

```text
tree-packing visualize path/to/submission.csv --n 10
```

This loads the submission and delegates to the optional matplotlib wrapper.
The `main()` function parses arguments, dispatches on the command, and returns
an integer exit code. The module guard turns that into the process exit status.

### 5.9 `__init__.py` and `py.typed`

[`__init__.py`](src/tree_packing/__init__.py) exposes the package version
`0.1.0`. It deliberately does not import every submodule at package startup.

[`py.typed`](src/tree_packing/py.typed) is the PEP 561 marker that tells type
checkers this package contains type information. The project uses strict mypy
settings, so type annotations are part of the implementation contract rather
than just documentation.

## 6. The reference implementation and how the port relates to it

### 6.1 `reference/evaluator.py`

[`reference/evaluator.py`](reference/evaluator.py) is the official harness
retained for direct comparison. Its major stages are:

```text
load_submission()
  -> validate_submission()
  -> evaluate_submission()
       -> create_tree_polygon()
       -> check_overlap()
       -> calculate_bounding_box_side()
       -> Decimal side^2 / n
  -> print result or reject
```

The package splits those same responsibilities into separate typed modules:

| Reference evaluator | Package port |
|---|---|
| constants | `config.py` |
| `create_tree_polygon` | `geometry.py` |
| `check_overlap` | `validation.py` |
| `calculate_bounding_box_side` | `scoring.py` |
| `parse_submission_value` / loader | `serialization.py` |
| `main` | `cli.py` |

The reference evaluator remains useful because it is the final authority for
acceptance. The package’s parity test and end-to-end comparison prevent a clean
internal abstraction from drifting away from the actual grading behavior.

### 6.2 `reference/simple_algorithm.py`

[`reference/simple_algorithm.py`](reference/simple_algorithm.py) is the source
of the baseline grid. It uses the same `ceil(sqrt(n))`, centered coordinates,
`1.1` spacing, zero rotation, row-major ordering, and full 1..200 generation.

The package version is a typed decomposition:

```text
generate_grid_positions(n)
  -> grid_positions(n)

generate_submission(path)
  -> build_baseline()
  -> write_submission(...)
```

The algorithm is deterministic. Given the same `n` and spacing, it always
returns the same list in the same order.

### 6.3 The sample solution

[`reference/sample_solution.csv`](reference/sample_solution.csv) contains the
same kind of grid submission and has 20,100 data rows. It formats values to six
decimal places. The package-generated baseline is logically equivalent but
uses Python’s direct float string formatting, as described in the serialization
section.

### 6.4 Planning and process artifacts

The retained plans explain why the package has this shape:

- [`reference/plan.md`](reference/plan.md) is the original scaffolding plan.
- The root [`plan.md`](plan.md) is the revised plan, including the
  “agentic coding is science” hypothesis/test/refinement workflow.
- `challenge-files/plan-with-agentic-as-science.md` is the corresponding source
  artifact.
- [`DECISIONS.md`](DECISIONS.md), [`LAB_NOTEBOOK.md`](LAB_NOTEBOOK.md), and
  [`documentary.md`](documentary.md) record design decisions and verification
  history locally.

Those files explain the development process; they are not imported by the
runtime.

## 7. Tests: what each test protects

The suite has 27 passing tests at the time this document was written.

| Test file | What it establishes |
|---|---|
| [`test_config.py`](tests/test_config.py) | precision, scale, bounds, tree range, and spacing are exact |
| [`test_geometry.py`](tests/test_geometry.py) | 15 vertices, valid polygon, known area/bounds, translation, and symmetry |
| [`test_parity_with_reference.py`](tests/test_parity_with_reference.py) | package geometry equals the official geometry for representative placements |
| [`test_scoring.py`](tests/test_scoring.py) | empty case, single-tree side/score, and normalization formula |
| [`test_validation.py`](tests/test_validation.py) | identical trees overlap, distant trees do not, singleton is safe, frame errors are reported |
| [`test_baseline.py`](tests/test_baseline.py) | exact placement counts, empty `n=0`, grid validity for sampled values, all 200 configurations |
| [`test_serialization.py`](tests/test_serialization.py) | prefix round-trip, plain-float tolerance, full 20,100-row write/load round-trip |
| [`test_integration.py`](tests/test_integration.py) | generated baseline is structurally valid and small configurations score without overlap |
| [`conftest.py`](tests/conftest.py) | shared origin-tree fixture |

The test strategy is intentionally layered:

1. Cheap constants and pure-function tests catch local mistakes.
2. Geometry tests check closed-form facts such as area and bounds.
3. The parity test checks against the retained ground truth.
4. Serialization tests cover the complete row count without requiring all
   20,100 polygons to be repeatedly scored.
5. Integration tests exercise all configuration keys and the full data path,
   while limiting expensive geometric scoring to `n <= 20`.

The configured coverage report includes CLI and visualization code as largely
manual paths, so total statement coverage is lower than the coverage of the
pure core modules. That is deliberate: the tests focus on deterministic
behavior and the CLI/reference commands provide end-to-end checks.

## 8. Tooling and dependency model

[`pyproject.toml`](pyproject.toml) declares Python `>=3.12` and the runtime
dependencies:

```text
pandas >= 2.2
shapely >= 2.0
```

The optional `viz` extra adds matplotlib. Development dependencies provide
pytest, coverage, Ruff, mypy, pandas stubs, and pre-commit.

The project uses a `src/` layout and Hatchling for packaging. `uv.lock` records
the resolved environment. The configured quality gates are:

```text
uv run ruff format .
uv run ruff check .
uv run mypy src
uv run pytest
```

The pre-commit file runs Ruff formatting/linting and strict mypy on source
files. Ruff is configured to exclude the preserved reference/challenge
artifacts and local planning records from Python discovery; the package and
tests remain covered by the project checks.

## 9. Running the baseline

### 9.1 Set up

From the repository root:

```bash
uv sync
uv run pre-commit install
```

Python 3.12 is selected by [`.python-version`](.python-version).

### 9.2 Generate a submission

```bash
uv run tree-packing generate --output data/submissions/baseline.csv
```

The generated CSV contains:

```text
header + 20,100 data rows
IDs 001_0 through 200_199, grouped by configuration
zero rotation for every tree
centered 1.1-spaced grid positions
```

CSV files under `data/submissions/` are ignored by Git so generated outputs do
not accidentally become source artifacts.

### 9.3 Evaluate with the package port

```bash
uv run tree-packing evaluate data/submissions/baseline.csv
```

The known generated baseline result is:

```text
TOTAL SCORE: 256.8197122633766779770234
```

There are no overlap errors.

### 9.4 Cross-check with the official evaluator

```bash
uv run python reference/evaluator.py data/submissions/baseline.csv
```

The reference evaluator accepts the same file and displays:

```text
TOTAL SCORE: 256.819712
```

The difference in displayed digits is formatting; the package’s Decimal total
and the reference evaluator agree to the precision shown by the reference
command.

### 9.5 Visualize one configuration

Install the optional extra and render a configuration:

```bash
uv sync --extra viz
uv run tree-packing visualize data/submissions/baseline.csv --n 10
```

Good first configurations to inspect are `1`, `4`, `10`, `50`, `100`, and
`200`. The visualization makes the unused gaps in the baseline obvious.

## 10. Baseline behavior and useful measured intuition

The following values come from the generated baseline. Width and height are
the actual polygon bounding rectangle dimensions after converting back from
scaled Shapely coordinates.

| `n` | width | height | square side | `s_n^2 / n` |
|---:|---:|---:|---:|---:|
| 1 | 0.7 | 1.0 | 1.0 | 1.0 |
| 2 | 1.8 | 1.0 | 1.8 | 1.62 |
| 3 | 1.8 | 2.1 | 2.1 | 1.47 |
| 4 | 1.8 | 2.1 | 2.1 | 1.1025 |
| 5 | 2.9 | 2.1 | 2.9 | 1.682 |
| 10 | 4.0 | 3.2 | 4.0 | 1.6 |
| 50 | 8.4 | 7.6 | 8.4 | approximately 1.4112 |
| 100 | 10.6 | 10.9 | 10.9 | 1.1881 |
| 200 | 16.1 | 15.3 | 16.1 | approximately 1.29605 |

These numbers illustrate several properties:

- Adding one tree does not necessarily increase the side smoothly because the
  rectangular grid changes shape at square-root thresholds.
- The side is the larger of width and height, so improving only one dimension
  may not improve the score.
- The division by `n` rewards layouts that grow sublinearly as more trees are
  added, but the square still punishes large gaps.
- The grid’s score is a correctness baseline, not an estimate of the best
  possible score. Its regular spacing ignores the tree’s narrow trunk, branch
  ledges, symmetry, and useful rotations.

The baseline’s coordinate extrema are roughly `[-7.7, 7.7]` in `x` and
`[-7.15, 7.15]` in `y` across all 200 configurations, comfortably within the
center-coordinate limits.

## 11. A recommended way to learn the codebase

If the goal is to make the implementation make sense rather than merely run
it, use this sequence.

### Step 1: establish the one-tree mental model

Run or inspect:

```python
tree = create_tree_polygon(0, 0, 0)
```

Reason from its bounds:

```text
width  = 0.7
height = 1.0
side   = 1.0
score  = 1.0
```

Then try `create_tree_polygon(5, 0, 45)` and note that translation moves the
whole polygon while the angle changes its bounds.

### Step 2: trace one generated row

Start at `grid_positions(2)`:

```text
(-0.55, 0.0, 0.0)
( 0.55, 0.0, 0.0)
```

Follow those values into `write_submission()`, observe the IDs `002_0` and
`002_1`, then follow them back through `load_submission()` into the normalized
DataFrame.

### Step 3: trace one evaluated configuration

For `n=2`, the evaluator:

1. creates two transformed polygons;
2. asks the STRtree for possible neighbors;
3. finds no positive-area overlap;
4. obtains width `1.8` and height `1.0`;
5. chooses side `1.8`;
6. adds `1.8^2 / 2 = 1.62`.

This single example covers almost the entire runtime path.

### Step 4: compare package and reference

Read the corresponding functions side by side:

```text
reference/evaluator.py:create_tree_polygon
src/tree_packing/geometry.py:create_tree_polygon

reference/evaluator.py:check_overlap
src/tree_packing/validation.py:find_overlapping_pairs

reference/evaluator.py:calculate_bounding_box_side
src/tree_packing/scoring.py:bounding_box_side
```

The package is easier to extend because those concerns are separated, but the
reference is the authority when the two appear to differ.

### Step 5: use the tests as executable explanations

Read the tests in this order:

```text
test_config.py
test_geometry.py
test_scoring.py
test_validation.py
test_baseline.py
test_serialization.py
test_parity_with_reference.py
test_integration.py
```

Each test file answers a focused question and gives a concrete expected value.

## 12. How a future optimizer would fit

The clean extension point is not to rewrite the evaluator. It is to add an
optimizer that produces the same `dict[int, list[Placement]]` shape consumed by
`write_submission()`.

A sensible staged approach is:

1. Keep `geometry.py`, `validation.py`, `scoring.py`, and `serialization.py`
   unchanged as the correctness kernel.
2. Add an `optimizer.py` that solves one `n` at a time.
3. Seed each `n` with the current grid, plus staggered or rotated alternatives.
4. Represent a candidate as the `3n` vector of positions and angles.
5. Reject any candidate with an evaluator-defined overlap before accepting it.
6. Minimize `side^2` for that fixed `n`; the `/ n` factor is constant during
   that subproblem.
7. Save the best valid placement independently for each `n`.
8. Re-run the exact package checks and the official reference evaluator on the
   final CSV.

Useful candidate moves include moving one tree, changing one angle, moving a
cluster, adding a tree to an `n - 1` solution as an initial guess, and
re-centering the final arrangement. Multiple random seeds would be important
because a single local search can get trapped in a poor layout.

The collision rule must remain:

```python
intersects and not touches
```

During search, a small safety margin is prudent because an intended exact touch
can become a numerical overlap after serialization. Final acceptance should
always use the exact evaluator-compatible geometry, not a looser optimizer-only
approximation.

## 13. Important implementation gotchas

These are the details most likely to cause confusion when modifying the code.

### The configurations are independent

Do not assume `build_baseline()[n + 1]` extends `build_baseline()[n]`. Each grid
is recomputed from scratch, and that is valid because the challenge scores each
`n` independently.

### The score uses polygon bounds, not polygon area

The tree’s area (`0.245625`) is a geometry sanity check, not the score. The
score is driven by the side of the enclosing square, which is determined by
extreme coordinates.

### The square is axis-aligned

The code does not compute a minimum-area arbitrarily rotated square. A future
optimizer must improve the axis-aligned width and height that this evaluator
uses.

### Touching is legal

`intersects()` includes touching. Only the combination
`intersects() and not touches()` means “invalid overlap” here.

### Scaling occurs before Shapely operations

Do not scale a polygon twice, and do not forget to divide bounds by the scale
when calculating a user-facing side length.

### Rotation is in degrees and happens before translation

Shapely’s `affinity.rotate` expects degrees by default. The code uses origin
`(0, 0)` and then translates by the requested center values.

### The `s` prefix is a file-format convention

It is not part of the numeric value. `parse_value()` removes it, and the
reference parser accepts unprefixed values too. Keeping the prefix makes the
output match the documented submission style.

### The center bounds are not polygon bounds

Validation checks the submitted `x` and `y` fields. It does not require every
transformed vertex to lie within `[-100, 100]`.

### The baseline is intentionally not competitive

All angles are zero, all rows use a regular spacing, and no branch interlocking
is attempted. Its purpose is to prove that the representation, geometry,
collision rule, scoring, and output format work together.

### The reference code beats comments

The `0.8` spacing comment in the simple algorithm conflicts with its actual
`1.1` assignment. The tests and package follow the executable assignment.

### The package mirrors reference permissiveness

The structural validator compares expected and actual ID sets and checks center
coordinates. It does not add a separate angle-range rule or a separate explicit
row-count assertion. The normal writer produces exactly the expected rows, and
the reference evaluator is the final acceptance check.

## 14. Final mental model

Think of the repository as a small compiler and verifier for geometric
solutions:

```text
configuration dictionary
  -- baseline.py --> placements
  -- serialization.py --> submission CSV
  -- serialization.py --> normalized DataFrame
  -- geometry.py --> exact scaled polygons
  -- validation.py --> legal or overlapping arrangement
  -- scoring.py --> one Decimal score per configuration
  -- cli.py --> total score and exit status
```

The baseline solves the engineering foundation of the challenge:

- the tree shape is exact;
- transformations match the official evaluator;
- every configuration and row is generated;
- touching and overlap semantics match Shapely/reference behavior;
- the bounding-square score is reproduced;
- the output can be visualized and independently cross-checked.

What remains unsolved is the actual optimization problem: finding much tighter
arrangements for each of the 200 independent configurations. That is the next
layer to build on top of this baseline, not something already hidden inside
the current implementation.
