"""End-to-end validation of a written submission CSV."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

from tree_packing import config
from tree_packing.geometry import create_tree_polygon
from tree_packing.scoring import bounding_box_side, configuration_score
from tree_packing.serialization import load_submission
from tree_packing.validation.clearance import min_pairwise_clearance
from tree_packing.validation.overlap import find_overlapping_pairs, validate_submission_frame


@dataclass(frozen=True, slots=True)
class ConfigurationReport:
    """Summary statistics for a single configuration."""

    n: int
    side: Decimal
    score_term: Decimal
    overlap_pairs: tuple[tuple[int, int], ...]
    min_clearance: Decimal


@dataclass(frozen=True, slots=True)
class GatekeeperReport:
    """Validation result for one submission file."""

    path: Path
    validation_errors: tuple[str, ...]
    configurations: tuple[ConfigurationReport, ...]
    total_score: Decimal | None
    against: Path | None = None
    regression_errors: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        monotone = all(
            earlier.side <= later.side for earlier, later in pairwise(self.configurations)
        )
        return (
            not self.validation_errors
            and not self.regression_errors
            and monotone
            and all(
                not report.overlap_pairs and report.min_clearance >= config.CLEARANCE_EPS
                for report in self.configurations
            )
        )


def _load_best_scores(path: Path) -> tuple[Decimal, dict[int, Decimal]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    total = Decimal(str(data["total_score"]))
    score_terms = {int(key): Decimal(str(value)) for key, value in data["score_terms"].items()}
    return total, score_terms


def _configuration_report(n: int, rows: Any) -> ConfigurationReport:
    polygons = [
        create_tree_polygon(str(row.x), str(row.y), str(row.deg)) for row in rows.itertuples()
    ]
    side = bounding_box_side(polygons)
    score_term = configuration_score(side, n)
    overlap_pairs = tuple(find_overlapping_pairs(polygons))
    min_clearance = min_pairwise_clearance(polygons)
    return ConfigurationReport(
        n=n,
        side=side,
        score_term=score_term,
        overlap_pairs=overlap_pairs,
        min_clearance=min_clearance,
    )


def gatekeep_submission(path: str | Path, against: str | Path | None = None) -> GatekeeperReport:
    """Read ``path`` from disk and validate it end-to-end."""
    submission_path = Path(path)
    frame = load_submission(submission_path)
    validation_errors = tuple(validate_submission_frame(frame))

    if validation_errors:
        return GatekeeperReport(
            path=submission_path,
            validation_errors=validation_errors,
            configurations=(),
            total_score=None,
            against=Path(against) if against is not None else None,
        )

    configurations = tuple(
        _configuration_report(n, frame[frame["n"] == n])
        for n in range(config.MIN_TREES, config.MAX_TREES + 1)
    )
    total_score = sum((report.score_term for report in configurations), Decimal("0"))
    monotone = all(earlier.side <= later.side for earlier, later in pairwise(configurations))
    regression_errors: list[str] = []
    if not monotone:
        regression_errors.append("score terms are not monotone across n")
    best_path = Path(against) if against is not None else None
    if best_path is not None:
        best_total, best_terms = _load_best_scores(best_path)
        if total_score > best_total:
            regression_errors.append(
                f"total score {total_score} exceeds recorded best {best_total}"
            )
        for report in configurations:
            expected = best_terms.get(report.n)
            if expected is None:
                regression_errors.append(f"missing expected score term for n={report.n}")
                continue
            if report.score_term > expected:
                regression_errors.append(
                    f"n={report.n}: score {report.score_term} exceeds recorded best {expected}"
                )
    return GatekeeperReport(
        path=submission_path,
        validation_errors=(),
        configurations=configurations,
        total_score=total_score,
        against=best_path,
        regression_errors=tuple(regression_errors),
    )


def report_lines(report: GatekeeperReport) -> list[str]:
    """Render a compact human-readable report."""
    lines = [f"Gatekeep report: {report.path}"]
    if report.validation_errors:
        lines.append("Validation errors:")
        lines.extend(f"  - {error}" for error in report.validation_errors)
        return lines

    lines.append(f"Total score: {report.total_score}")
    if report.against is not None:
        lines.append(f"Against: {report.against}")
    if report.configurations:
        monotone = all(
            earlier.side <= later.side for earlier, later in pairwise(report.configurations)
        )
        lines.append(f"Monotone: {monotone}")
    if report.regression_errors:
        lines.append("Regression errors:")
        lines.extend(f"  - {error}" for error in report.regression_errors)
    for config_report in report.configurations:
        lines.append(
            f"  n={config_report.n}: side={config_report.side}, "
            f"score={config_report.score_term}, "
            f"overlaps={len(config_report.overlap_pairs)}, "
            f"min_clearance={config_report.min_clearance}"
        )
    return lines
