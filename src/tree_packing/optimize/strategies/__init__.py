"""Built-in deterministic strategy implementations."""

from tree_packing.optimize.strategies.baseline import BaselineStrategy
from tree_packing.optimize.strategies.grid import TightGridStrategy
from tree_packing.optimize.strategies.lattice import LatticeStrategy

__all__ = ["BaselineStrategy", "LatticeStrategy", "TightGridStrategy"]
