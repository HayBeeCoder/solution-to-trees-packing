from decimal import Decimal

from tree_packing import config


def test_precision_and_scale_constants() -> None:
    assert Decimal("1e15") == config.SCALE_FACTOR
    assert Decimal("1e-9") == config.CLEARANCE_EPS
    assert config.DECIMAL_PRECISION == 25


def test_bounds_and_configuration_range() -> None:
    assert (config.MIN_COORD, config.MAX_COORD) == (-100, 100)
    assert (config.MIN_TREES, config.MAX_TREES) == (1, 200)
    assert config.GRID_SPACING == 1.1
