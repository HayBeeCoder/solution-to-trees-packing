"""End-to-end validation of a written submission CSV."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
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

    @property
    def is_valid(self) -> bool:
        return not self.validation_errors and all(
            not report.overlap_pairs and report.min_clearance >= config.CLEARANCE_EPS
            for report in self.configurations
        )


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


def gatekeep_submission(path: str | Path) -> GatekeeperReport:
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
        )

    configurations = tuple(
        _configuration_report(n, frame[frame["n"] == n])
        for n in range(config.MIN_TREES, config.MAX_TREES + 1)
    )
    total_score = sum((report.score_term for report in configurations), Decimal("0"))
    return GatekeeperReport(
        path=submission_path,
        validation_errors=(),
        configurations=configurations,
        total_score=total_score,
    )


def report_lines(report: GatekeeperReport) -> list[str]:
    """Render a compact human-readable report."""
    lines = [f"Gatekeep report: {report.path}"]
    if report.validation_errors:
        lines.append("Validation errors:")
        lines.extend(f"  - {error}" for error in report.validation_errors)
        return lines

    lines.append(f"Total score: {report.total_score}")
    for config_report in report.configurations:
        lines.append(
            f"  n={config_report.n}: side={config_report.side}, "
            f"score={config_report.score_term}, "
            f"overlaps={len(config_report.overlap_pairs)}, "
            f"min_clearance={config_report.min_clearance}"
        )
    return lines
