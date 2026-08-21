"""Read/write the s-prefixed submission CSV format."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, cast

import pandas as pd

from tree_packing import config

Placement = tuple[float, float, float]


class _PlacementLike(Protocol):
    x: float
    y: float
    deg: float


def _placement_components(placement: object) -> tuple[float, float, float]:
    if isinstance(placement, tuple) and len(placement) == 3:
        return float(placement[0]), float(placement[1]), float(placement[2])
    try:
        typed_placement = cast(_PlacementLike, placement)
        return (
            float(typed_placement.x),
            float(typed_placement.y),
            float(typed_placement.deg),
        )
    except AttributeError as exc:  # pragma: no cover - defensive fallback
        raise TypeError(f"Unsupported placement type: {type(placement)!r}") from exc


def format_value(value: float) -> str:
    """Numeric -> submission string, e.g. 1.5 -> 's1.5'."""
    return f"s{value}"


def parse_value(value: str | float) -> float:
    """Submission string -> float, tolerating the 's' prefix."""
    if isinstance(value, str) and value.startswith("s"):
        return float(value[1:])
    return float(value)


def write_submission(
    solutions: Mapping[int, Sequence[Placement | object]], path: str | Path
) -> None:
    """Serialize {n: [(x, y, deg), ...]} to the official CSV layout."""
    rows = [
        {
            "id": f"{n:03d}_{t}",
            "x": format_value(x),
            "y": format_value(y),
            "deg": format_value(deg),
        }
        for n in range(config.MIN_TREES, config.MAX_TREES + 1)
        for t, placement in enumerate(solutions[n])
        for x, y, deg in [_placement_components(placement)]
    ]

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["id", "x", "y", "deg"]).to_csv(out, index=False)


def load_submission(path: str | Path) -> pd.DataFrame:
    """Parse a submission CSV into columns: n, tree_idx, x, y, deg."""
    df = pd.read_csv(path, index_col="id")
    records: list[dict[str, int | float]] = []
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
