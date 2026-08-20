---
title: "Christmas Tree Packing Challenge"
subtitle: "A 2D Polygon Packing Optimization Problem"
geometry: margin=2.5cm
fontsize: 11pt
---

# Problem Description

## The Challenge

In this optimization problem, you must help pack Christmas tree toys into the smallest possible 2-dimensional square parcel. The goal is to find the smallest square box that can fit shipments containing between 1 and 200 trees.

You must solve **200 separate packing problems**: one for each value of $n$ from 1 to 200, where $n$ is the number of trees to pack. For each configuration, you need to determine the position $(x, y)$ and rotation angle (in degrees) for each tree such that:

1. No two trees overlap
2. All trees fit within a square bounding box
3. The square bounding box is as small as possible

## The Goal

Find the optimal packing solution that minimizes the total score across all 200 configurations.

---

# The Christmas Tree Shape

Each Christmas tree is an identical polygon with the following structure:

- **Trunk**: A rectangle at the bottom (width: 0.15, height: 0.2)
- **Three tiers of branches**: Each tier is wider than the one above
  - Bottom tier: width 0.7
  - Middle tier: width 0.4
  - Top tier: width 0.25
- **Tip**: A point at the top (y = 0.8)

## Tree Polygon Vertices

The tree polygon is defined by the following vertices, starting from the tip and going clockwise. The tree is centered at the origin $(0, 0)$ before any rotation or translation is applied:

| Vertex | X Coordinate | Y Coordinate | Description |
|--------|-------------|--------------|-------------|
| 1 | 0.0 | 0.8 | Tip |
| 2 | 0.125 | 0.5 | Right top tier outer |
| 3 | 0.0625 | 0.5 | Right top tier inner |
| 4 | 0.2 | 0.25 | Right middle tier outer |
| 5 | 0.1 | 0.25 | Right middle tier inner |
| 6 | 0.35 | 0.0 | Right bottom tier |
| 7 | 0.075 | 0.0 | Right trunk top |
| 8 | 0.075 | -0.2 | Right trunk bottom |
| 9 | -0.075 | -0.2 | Left trunk bottom |
| 10 | -0.075 | 0.0 | Left trunk top |
| 11 | -0.35 | 0.0 | Left bottom tier |
| 12 | -0.1 | 0.25 | Left middle tier inner |
| 13 | -0.2 | 0.25 | Left middle tier outer |
| 14 | -0.0625 | 0.5 | Left top tier inner |
| 15 | -0.125 | 0.5 | Left top tier outer |

## Tree Dimensions Summary

| Dimension | Value |
|-----------|-------|
| Total height (tip to trunk bottom) | 1.0 |
| Maximum width (bottom tier) | 0.7 |
| Trunk width | 0.15 |
| Trunk height | 0.2 |

## Visual Representation

```
         *           <- Tip (0, 0.8)
        /|\
       / | \         <- Top tier (width 0.25)
      /  |  \
     /   |   \
    /----+----\      <- y = 0.5
   /     |     \
  /      |      \    <- Middle tier (width 0.4)
 /-------+-------\   <- y = 0.25
/        |        \
+-----------------+  <- Base of tree (y = 0)
         |
        | |          <- Trunk (width 0.15)
        | |
        +-+          <- Bottom of trunk (y = -0.2)
```

---

# Evaluation Criteria

## Scoring Formula

Submissions are evaluated on the **sum of the normalized area** of the square bounding box for each puzzle configuration.

For each $n$-tree configuration:

1. Calculate $s_n$ = the side length of the smallest square that bounds all $n$ trees
2. Calculate the normalized score: $\frac{s_n^2}{n}$

The **total score** is:

$$\text{Score} = \sum_{n=1}^{200} \frac{s_n^2}{n}$$

**Lower scores are better.**

## Example

If you pack 4 trees into a square with side length 2.0:

- Contribution to score: $\frac{2.0^2}{4} = \frac{4.0}{4} = 1.0$

If you pack 10 trees into a square with side length 3.5:

- Contribution to score: $\frac{3.5^2}{10} = \frac{12.25}{10} = 1.225$

## Constraints

1. **No overlapping trees**: Trees may touch but not overlap. Submissions with overlapping trees are invalid.
2. **Coordinate bounds**: All tree positions $(x, y)$ must satisfy $-100 \leq x \leq 100$ and $-100 \leq y \leq 100$.

---

# Submission Format

## File Structure

Your submission must be a CSV file with the following format:

- **Header row**: `id,x,y,deg`
- **Data rows**: One row per tree, for all configurations from 1 to 200

## ID Format

The `id` column identifies which tree in which configuration:

- Format: `NNN_T` where:
  - `NNN` = zero-padded configuration number (001 to 200)
  - `T` = tree index within that configuration (0 to n-1)

Examples:
- `001_0` = Tree 0 in the 1-tree configuration
- `010_5` = Tree 5 in the 10-tree configuration
- `200_199` = Tree 199 in the 200-tree configuration

## Value Format

To avoid loss of precision, all numeric values must be:

1. Converted to a string
2. Prepended with the letter `s`

Examples:
- Position x = 1.5 becomes `s1.5`
- Position y = -0.123456 becomes `s-0.123456`
- Angle = 45.0 degrees becomes `s45.0`

## Complete Example

```csv
id,x,y,deg
001_0,s0.0,s0.0,s0.0
002_0,s0.0,s0.0,s0.0
002_1,s-0.541068,s0.259317,s51.66348
003_0,s0.0,s0.0,s0.0
003_1,s-0.541068,s0.259317,s51.66348
003_2,s0.4,s0.3,s90.0
...
```

## Total Number of Rows

The submission must contain exactly:

$$\sum_{n=1}^{200} n = \frac{200 \times 201}{2} = 20100 \text{ rows}$$

(plus the header row)

---

# Using the Evaluator

## Requirements

Install the required Python packages:

```bash
pip install pandas shapely matplotlib
```

## Basic Usage

To evaluate your submission:

```bash
python evaluator.py your_submission.csv
```

The evaluator will:

1. Validate the submission format
2. Check for overlapping trees in each configuration
3. Calculate and report the total score

## Visualize a Configuration

To visualize a specific configuration (e.g., the 10-tree arrangement):

```bash
python evaluator.py your_submission.csv --visualize 10
```

## Quiet Mode

To suppress progress output:

```bash
python evaluator.py your_submission.csv --quiet
```

---

# Creating Your Own Solution

## Python Code Example

Here is example code to create a tree polygon and generate a submission:

```python
from decimal import Decimal
from shapely import affinity
from shapely.geometry import Polygon

SCALE_FACTOR = Decimal('1e15')

def create_tree_polygon(center_x, center_y, angle_degrees):
    """Create a Christmas tree polygon at the given position and rotation."""
    center_x = Decimal(str(center_x))
    center_y = Decimal(str(center_y))
    angle = Decimal(str(angle_degrees))

    # Tree dimensions
    trunk_w = Decimal('0.15')
    trunk_h = Decimal('0.2')
    base_w = Decimal('0.7')
    mid_w = Decimal('0.4')
    top_w = Decimal('0.25')

    # Y coordinates
    tip_y = Decimal('0.8')
    tier_1_y = Decimal('0.5')
    tier_2_y = Decimal('0.25')
    base_y = Decimal('0.0')
    trunk_bottom_y = -trunk_h

    # Create polygon (scaled for precision)
    vertices = [
        (float(Decimal('0.0') * SCALE_FACTOR), float(tip_y * SCALE_FACTOR)),
        (float(top_w / 2 * SCALE_FACTOR), float(tier_1_y * SCALE_FACTOR)),
        (float(top_w / 4 * SCALE_FACTOR), float(tier_1_y * SCALE_FACTOR)),
        (float(mid_w / 2 * SCALE_FACTOR), float(tier_2_y * SCALE_FACTOR)),
        (float(mid_w / 4 * SCALE_FACTOR), float(tier_2_y * SCALE_FACTOR)),
        (float(base_w / 2 * SCALE_FACTOR), float(base_y * SCALE_FACTOR)),
        (float(trunk_w / 2 * SCALE_FACTOR), float(base_y * SCALE_FACTOR)),
        (float(trunk_w / 2 * SCALE_FACTOR), float(trunk_bottom_y * SCALE_FACTOR)),
        (float(-trunk_w / 2 * SCALE_FACTOR), float(trunk_bottom_y * SCALE_FACTOR)),
        (float(-trunk_w / 2 * SCALE_FACTOR), float(base_y * SCALE_FACTOR)),
        (float(-base_w / 2 * SCALE_FACTOR), float(base_y * SCALE_FACTOR)),
        (float(-mid_w / 4 * SCALE_FACTOR), float(tier_2_y * SCALE_FACTOR)),
        (float(-mid_w / 2 * SCALE_FACTOR), float(tier_2_y * SCALE_FACTOR)),
        (float(-top_w / 4 * SCALE_FACTOR), float(tier_1_y * SCALE_FACTOR)),
        (float(-top_w / 2 * SCALE_FACTOR), float(tier_1_y * SCALE_FACTOR)),
    ]

    polygon = Polygon(vertices)
    rotated = affinity.rotate(polygon, float(angle), origin=(0, 0))
    translated = affinity.translate(
        rotated,
        xoff=float(center_x * SCALE_FACTOR),
        yoff=float(center_y * SCALE_FACTOR)
    )
    return translated
```

## Checking for Overlaps

```python
from shapely.strtree import STRtree

def trees_overlap(poly1, poly2):
    """Check if two tree polygons overlap (touching is OK)."""
    return poly1.intersects(poly2) and not poly1.touches(poly2)

def check_configuration(polygons):
    """Check if any trees in a configuration overlap."""
    tree_index = STRtree(polygons)
    for i, poly in enumerate(polygons):
        candidates = tree_index.query(poly)
        for j in candidates:
            if j > i and trees_overlap(poly, polygons[j]):
                return False  # Found overlap
    return True  # No overlaps
```

## Generating a Submission File

```python
import pandas as pd

def generate_submission(solutions):
    """
    Generate a submission CSV from a dict of solutions.

    Args:
        solutions: Dict mapping n -> list of (x, y, deg) tuples
    """
    rows = []
    for n in range(1, 201):
        for t, (x, y, deg) in enumerate(solutions[n]):
            rows.append({
                'id': f'{n:03d}_{t}',
                'x': f's{x}',
                'y': f's{y}',
                'deg': f's{deg}'
            })

    df = pd.DataFrame(rows)
    df.to_csv('submission.csv', index=False)
```

---

# Tips and Strategies

1. **Start simple**: Begin with a naive placement (e.g., grid) and optimize from there.

2. **Leverage symmetry**: The tree shape has vertical symmetry, which can help in packing.

3. **Consider rotation**: Rotating trees can often lead to tighter packing arrangements.

4. **Use incremental building**: The solution for $n$ trees can often be extended to $n+1$ trees by adding one more tree in an optimal position.

5. **Optimization algorithms**: Consider using:
   - Simulated annealing
   - Genetic algorithms
   - Gradient-free optimization methods
   - Basin-hopping

6. **Collision detection**: Use spatial indexing (like STRtree) for efficient overlap checking when dealing with many trees.

Happy packing!
