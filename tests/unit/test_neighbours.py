from tree_packing.geometry.neighbours import (
    enumerate_neighbour_offsets,
    enumerate_neighbour_vectors,
    gauss_reduce_basis,
)


def test_gauss_reduction_satisfies_bounds() -> None:
    a, b = gauss_reduce_basis((0.2, 0.0), (0.1, 0.5))
    norm_a = a[0] ** 2 + a[1] ** 2
    norm_b = b[0] ** 2 + b[1] ** 2
    dot = a[0] * b[0] + a[1] * b[1]
    assert norm_b >= norm_a
    assert abs(2.0 * dot) <= norm_a


def test_enumeration_finds_sheared_offset_regression() -> None:
    offsets = enumerate_neighbour_offsets((0.2, 0.0), (0.1, 0.5), radius=1.6)
    assert (4, 2) in offsets


def test_enumeration_returns_short_vectors() -> None:
    vectors = enumerate_neighbour_vectors((0.2, 0.0), (0.1, 0.5), radius=1.6)
    assert any(abs(x - 1.0) < 1e-12 and abs(y - 1.0) < 1e-12 for x, y in vectors)
    assert all((x * x + y * y) ** 0.5 < 1.6 + 1e-12 for x, y in vectors)
