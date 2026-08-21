"""Immutable constants shared across the package.

Every numeric constant is copied verbatim from the official ``evaluator.py`` and
``simple_algorithm.py`` so that our tooling matches the grading harness exactly.
"""

from __future__ import annotations

from decimal import Decimal

# --- Precision -------------------------------------------------------------
DECIMAL_PRECISION = 25
SCALE_FACTOR = Decimal("1e15")
CLEARANCE_EPS = Decimal("1e-9")

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
