import pytest

from tree_packing.geometry import create_tree_polygon


@pytest.fixture
def origin_tree():
    return create_tree_polygon(0, 0, 0)
