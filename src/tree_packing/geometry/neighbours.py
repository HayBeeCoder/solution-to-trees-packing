"""Geometric neighbour enumeration over a Gauss-reduced lattice basis."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

import numpy as np

Vector = tuple[float, float]


def _as_vector(vector: Vector) -> Any:
    return np.asarray(vector, dtype=float)


def _as_vector_tuple(values: Any) -> Vector:
    return (float(values[0]), float(values[1]))


def gauss_reduce_basis(a: Vector, b: Vector) -> tuple[Vector, Vector]:
    """Return a 2D Gauss-reduced basis with ``|b| >= |a|`` and a short angle."""
    basis_a = _as_vector(a)
    basis_b = _as_vector(b)

    if np.dot(basis_b, basis_b) < np.dot(basis_a, basis_a):
        basis_a, basis_b = basis_b, basis_a

    while True:
        mu = int(np.rint(np.dot(basis_a, basis_b) / np.dot(basis_a, basis_a)))
        if mu != 0:
            basis_b = basis_b - mu * basis_a
        if np.dot(basis_b, basis_b) < np.dot(basis_a, basis_a):
            basis_a, basis_b = basis_b, basis_a
            continue
        if abs(2.0 * float(np.dot(basis_a, basis_b))) <= float(np.dot(basis_a, basis_a)):
            return _as_vector_tuple(basis_a), _as_vector_tuple(basis_b)
        sign = 1.0 if float(np.dot(basis_a, basis_b)) > 0 else -1.0
        basis_b = basis_b - sign * basis_a


def _coefficient_bound(reduced_a: Any, reduced_b: Any, radius: float) -> int:
    matrix = np.column_stack([reduced_a, reduced_b])
    inverse = np.linalg.inv(matrix)
    row_sums = np.sum(np.abs(inverse), axis=1)
    bound = math.ceil(radius * float(np.max(row_sums))) + 1
    return max(bound, 1)


def enumerate_neighbour_offsets(a: Vector, b: Vector, radius: float = 1.6) -> list[tuple[int, int]]:
    """Enumerate reduced-basis index offsets whose translated norm is below ``radius``."""
    reduced_a, reduced_b = gauss_reduce_basis(a, b)
    vec_a = _as_vector(reduced_a)
    vec_b = _as_vector(reduced_b)
    bound = _coefficient_bound(vec_a, vec_b, radius)

    offsets: list[tuple[int, int]] = []
    for i in range(-bound, bound + 1):
        for j in range(-bound, bound + 1):
            if i == 0 and j == 0:
                continue
            candidate = i * vec_a + j * vec_b
            if float(np.linalg.norm(candidate)) < radius:
                offsets.append((i, j))
    return offsets


def enumerate_neighbour_vectors(a: Vector, b: Vector, radius: float = 1.6) -> list[Vector]:
    """Enumerate the actual translation vectors whose norm is below ``radius``."""
    reduced_a, reduced_b = gauss_reduce_basis(a, b)
    vec_a = _as_vector(reduced_a)
    vec_b = _as_vector(reduced_b)
    bound = _coefficient_bound(vec_a, vec_b, radius)

    vectors: list[Vector] = []
    for i in range(-bound, bound + 1):
        for j in range(-bound, bound + 1):
            if i == 0 and j == 0:
                continue
            candidate = i * vec_a + j * vec_b
            if float(np.linalg.norm(candidate)) < radius:
                vectors.append((float(candidate[0]), float(candidate[1])))
    return vectors


def enumerate_neighbours(a: Vector, b: Vector, radius: float = 1.6) -> list[Vector]:
    """Alias for the vector-valued neighbour enumeration."""
    return enumerate_neighbour_vectors(a, b, radius=radius)


def iter_reduced_neighbour_vectors(basis: Iterable[Vector], radius: float = 1.6) -> list[Vector]:
    """Convenience wrapper for callers that already store the basis as an iterable."""
    a, b = tuple(basis)
    return enumerate_neighbour_vectors(a, b, radius=radius)
