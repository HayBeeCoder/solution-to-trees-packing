"""Built-in deterministic strategy implementations."""

from tree_packing.optimize.strategies.baseline import BaselineStrategy
from tree_packing.optimize.strategies.grid import TightGridStrategy

__all__ = ["BaselineStrategy", "TightGridStrategy"]
