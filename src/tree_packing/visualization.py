"""Optional matplotlib rendering for one evaluated configuration."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
from shapely.ops import unary_union

from tree_packing import config
from tree_packing.geometry import create_tree_polygon
from tree_packing.scoring import bounding_box_side


def plot_configuration(df: pd.DataFrame, n: int) -> None:
    """Draw the trees in configuration ``n`` and its red dashed bounding square."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError as exc:
        raise ImportError(
            "Visualization requires matplotlib; install it with `uv sync --extra viz`."
        ) from exc

    config_df = df[df["n"] == n]
    if len(config_df) == 0:
        raise ValueError(f"No data for configuration n={n}")

    polygons = [
        create_tree_polygon(str(row.x), str(row.y), str(row.deg)) for row in config_df.itertuples()
    ]
    side = bounding_box_side(polygons)
    bounds = unary_union(polygons).bounds

    minx = Decimal(str(bounds[0])) / config.SCALE_FACTOR
    miny = Decimal(str(bounds[1])) / config.SCALE_FACTOR
    maxx = Decimal(str(bounds[2])) / config.SCALE_FACTOR
    maxy = Decimal(str(bounds[3])) / config.SCALE_FACTOR
    width = maxx - minx
    height = maxy - miny

    _, ax = plt.subplots(figsize=(8, 8))
    colors = plt.cm.viridis([i / n for i in range(n)])

    for i, poly in enumerate(polygons):
        x_scaled, y_scaled = poly.exterior.xy
        x = [Decimal(str(value)) / config.SCALE_FACTOR for value in x_scaled]
        y = [Decimal(str(value)) / config.SCALE_FACTOR for value in y_scaled]
        ax.plot([float(value) for value in x], [float(value) for value in y], color=colors[i])
        ax.fill(
            [float(value) for value in x],
            [float(value) for value in y],
            alpha=0.5,
            color=colors[i],
        )

    square_x = minx if width >= height else minx - (side - width) / 2
    square_y = miny if height >= width else miny - (side - height) / 2
    bounding_square = Rectangle(
        (float(square_x), float(square_y)),
        float(side),
        float(side),
        fill=False,
        edgecolor="red",
        linewidth=2,
        linestyle="--",
    )
    ax.add_patch(bounding_square)

    padding = Decimal("0.5")
    ax.set_xlim(float(square_x - padding), float(square_x + side + padding))
    ax.set_ylim(float(square_y - padding), float(square_y + side + padding))
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(f"{n} Trees - Side Length: {float(side):.6f}")
    plt.show()
