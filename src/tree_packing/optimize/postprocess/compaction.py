"""Vectorised container-shrinking compaction (H4.2 / H4.3)."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from tree_packing.geometry.penetration import _canonical_pieces
from tree_packing.optimize.base import evaluate_layout
from tree_packing.optimize.postprocess.fast_ratchet import fast_box_side
from tree_packing.optimize.types import Layout, Placement

_SHRINK_FACTOR: float = 0.01
_MAX_OUTER: int = 50
_MAX_INNER: int = 80
_STEP_SCALE: float = 1.1
_PENETRATION_TOL: float = 1e-9
_BOUNDARY_WIDTH: float = 1.6
type FloatArray = NDArray[np.float64]
type BoolArray = NDArray[np.bool_]


def _build_sat_tables() -> (
    tuple[
        FloatArray,
        FloatArray,
        FloatArray,
        FloatArray,
        FloatArray,
    ]
):
    canon = _canonical_pieces()

    def _rotate_pieces(deg: float) -> list[FloatArray]:
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        rot = np.array([[c, -s], [s, c]], dtype=float)
        return [p @ rot.T for p in canon]

    p0, p180 = _rotate_pieces(0.0), _rotate_pieces(180.0)

    axes: list[FloatArray] = []
    for pieces in [p0, p180]:
        for piece in pieces:
            nv = len(piece)
            for i in range(nv):
                edge = piece[(i + 1) % nv] - piece[i]
                normal = np.array([-edge[1], edge[0]], dtype=float)
                length = float(np.linalg.norm(normal))
                if length < 1e-12:
                    continue
                a = normal / length
                if a[0] < 0 or (abs(a[0]) < 1e-12 and a[1] < 0):
                    a = -a
                if not any(np.allclose(a, u, atol=1e-9) for u in axes):
                    axes.append(a)

    axes_arr = np.array(axes, dtype=float)

    def _piece_minmax(pieces: list[FloatArray]) -> tuple[FloatArray, FloatArray]:
        mn = np.zeros((4, len(axes_arr)), dtype=float)
        mx = np.zeros((4, len(axes_arr)), dtype=float)
        for k, piece in enumerate(pieces):
            proj = piece @ axes_arr.T
            mn[k] = np.min(proj, axis=0)
            mx[k] = np.max(proj, axis=0)
        return mn, mx

    pmn0, pmx0 = _piece_minmax(p0)
    pmn180, pmx180 = _piece_minmax(p180)
    return axes_arr, pmn0, pmx0, pmn180, pmx180


_AXES, _PMNS_0, _PMXS_0, _PMNS_180, _PMXS_180 = _build_sat_tables()


def _resolution_pass(
    xs: FloatArray,
    ys: FloatArray,
    is_180: BoolArray,
    movable: FloatArray,
    step_scale: float,
) -> tuple[FloatArray, float]:
    n_trees = len(xs)
    centres = np.column_stack([xs, ys])
    cx_proj = centres @ _AXES.T

    pmnt = (
        np.where(is_180[:, None, None], _PMNS_180[None, :, :], _PMNS_0[None, :, :])
        + cx_proj[:, None, :]
    )
    pmxt = (
        np.where(is_180[:, None, None], _PMXS_180[None, :, :], _PMXS_0[None, :, :])
        + cx_proj[:, None, :]
    )

    po = np.minimum(pmxt[:, None, :, None, :], pmxt[None, :, None, :, :]) - np.maximum(
        pmnt[:, None, :, None, :], pmnt[None, :, None, :, :]
    )

    piece_pair_overlaps = (po > 0).all(axis=4)
    piece_depths = np.where(po > 0, po, np.inf).min(axis=4)
    piece_depths = np.where(piece_pair_overlaps, piece_depths, 0.0)

    tree_depths = piece_depths.max(axis=(2, 3))
    np.fill_diagonal(tree_depths, 0.0)

    max_depth = float(np.max(np.triu(tree_depths, k=1)))
    if max_depth < _PENETRATION_TOL:
        return np.zeros((n_trees, 2), dtype=float), max_depth

    best_pp = piece_depths.reshape(n_trees, n_trees, 16).argmax(axis=2)
    po_best = np.take_along_axis(
        po.reshape(n_trees, n_trees, 16, -1), best_pp[:, :, None, None], axis=2
    )
    po_best = po_best.squeeze(axis=2)
    ax_idx = np.argmin(np.where(po_best > 0, po_best, np.inf), axis=2)
    pair_ax = _AXES[ax_idx]

    diff = centres[None, :, :] - centres[:, None, :]
    dot = (diff * pair_ax).sum(axis=2)
    oriented = pair_ax * np.where(dot >= 0, 1.0, -1.0)[:, :, None]

    mask = np.triu(tree_depths > 0, k=1)
    td_masked = np.where(mask, tree_depths, 0.0)
    mtv = td_masked[:, :, None] * oriented * step_scale

    grad = (mtv.sum(axis=0) - mtv.sum(axis=1)) * 0.5
    grad *= movable[:, None]

    return grad, max_depth


def compact_layout(
    layout: Layout,
    *,
    shrink_factor: float = _SHRINK_FACTOR,
    max_outer: int = _MAX_OUTER,
    max_inner: int = _MAX_INNER,
    step_scale: float = _STEP_SCALE,
    boundary_only: bool = False,
    boundary_width: float = _BOUNDARY_WIDTH,
) -> Layout:
    """Compact layout by iteratively shrinking the container.

    Uses fast arithmetic box-side check inside the loop (no Shapely),
    with a single authoritative evaluate_layout call at the end.
    Always returns a valid layout.
    """
    current = evaluate_layout(layout) if layout.side is None else layout
    if current.side is None:
        return layout

    xs = np.array([p.x for p in current.placements], dtype=float)
    ys = np.array([p.y for p in current.placements], dtype=float)
    degs = np.array([p.deg for p in current.placements], dtype=float)
    is_180 = (degs % 360) > 90
    n = len(xs)

    best_side = float(current.side)
    best_xs, best_ys = xs.copy(), ys.copy()

    for _ in range(max_outer):
        new_side = best_side * (1.0 - shrink_factor)
        scale = new_side / best_side
        xs_try = best_xs * scale
        ys_try = best_ys * scale

        if boundary_only:
            half = new_side / 2.0
            dist = np.minimum(
                np.minimum(xs_try + half, half - xs_try),
                np.minimum(ys_try + half, half - ys_try),
            )
            movable = (dist <= boundary_width).astype(float)
        else:
            movable = np.ones(n, dtype=float)

        for _ in range(max_inner):
            grad, max_d = _resolution_pass(xs_try, ys_try, is_180, movable, step_scale)
            xs_try += grad[:, 0]
            ys_try += grad[:, 1]
            if max_d < _PENETRATION_TOL:
                break

        if max_d >= _PENETRATION_TOL:
            break

        placements_try = tuple(
            Placement(x=float(xs_try[k]), y=float(ys_try[k]), deg=float(degs[k])) for k in range(n)
        )
        candidate_side = float(fast_box_side(placements_try))

        if candidate_side < best_side:
            best_side = candidate_side
            best_xs = xs_try.copy()
            best_ys = ys_try.copy()
        else:
            break

    placements = tuple(
        Placement(x=float(best_xs[k]), y=float(best_ys[k]), deg=float(degs[k])) for k in range(n)
    )
    result = evaluate_layout(Layout(n=n, placements=placements))

    # Final validity gate — if compaction produced overlaps, return original
    if result.min_clearance is not None and result.min_clearance >= 0:
        return result
    return current
