"""Validation helpers for overlap detection, clearance, and gatekeeping."""

from tree_packing.validation.clearance import min_pairwise_clearance
from tree_packing.validation.gatekeeper import (
    ConfigurationReport,
    GatekeeperReport,
    gatekeep_submission,
    report_lines,
)
from tree_packing.validation.overlap import (
    find_overlapping_pairs,
    has_overlap,
    validate_submission_frame,
)

__all__ = [
    "ConfigurationReport",
    "GatekeeperReport",
    "find_overlapping_pairs",
    "gatekeep_submission",
    "has_overlap",
    "min_pairwise_clearance",
    "report_lines",
    "validate_submission_frame",
]
