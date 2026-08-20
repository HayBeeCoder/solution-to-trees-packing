import importlib.util
from pathlib import Path

from tree_packing.geometry import create_tree_polygon


def test_geometry_matches_reference() -> None:
    path = Path(__file__).parents[1] / "reference" / "evaluator.py"
    spec = importlib.util.spec_from_file_location("reference_evaluator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for values in ((0, 0, 0), (1.25, -2.5, 17.0), (-3, 4, 90)):
        ours = create_tree_polygon(*values)
        theirs = module.create_tree_polygon(*values)
        assert ours.equals(theirs)
