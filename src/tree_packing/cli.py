"""Command-line interface for generating, evaluating, and visualizing submissions."""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

from tree_packing import config
from tree_packing.baseline import build_baseline
from tree_packing.geometry import create_tree_polygon
from tree_packing.scoring import bounding_box_side, configuration_score
from tree_packing.serialization import load_submission, write_submission
from tree_packing.validation import (
    find_overlapping_pairs,
    gatekeep_submission,
    report_lines,
    validate_submission_frame,
)


def _generate(output: Path) -> int:
    write_submission(build_baseline(), output)
    print(f"Submission saved to: {output}")
    print("Total rows: 20100")
    return 0


def _evaluate(submission: Path, quiet: bool) -> int:
    try:
        df = load_submission(submission)
    except Exception as exc:
        print(f"Error loading submission: {exc}", file=sys.stderr)
        return 1

    errors = validate_submission_frame(df)
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    total = Decimal("0")
    overlap_errors: list[tuple[int, int]] = []
    overlap_configurations: list[int] = []

    for n in range(config.MIN_TREES, config.MAX_TREES + 1):
        rows = df[df["n"] == n]
        polygons = [
            create_tree_polygon(str(row.x), str(row.y), str(row.deg)) for row in rows.itertuples()
        ]
        pairs = find_overlapping_pairs(polygons)
        if pairs:
            overlap_configurations.append(n)
            overlap_errors.append((n, len(pairs)))
        total += configuration_score(bounding_box_side(polygons), n)
        if not quiet and n % 20 == 0:
            print(f"  Evaluated configurations 1-{n}...")

    if overlap_configurations:
        print("OVERLAP ERRORS DETECTED:")
        for n, count in overlap_errors[:10]:
            print(f"  - Configuration n={n}: {count} overlapping pairs")
        if len(overlap_errors) > 10:
            print(f"  ... and {len(overlap_errors) - 10} more")
        return 1

    print(f"TOTAL SCORE: {total}")
    return 0


def _visualize(submission: Path, n: int) -> int:
    try:
        df = load_submission(submission)
        from tree_packing.visualization import plot_configuration

        plot_configuration(df, n)
    except (ImportError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def _gatekeep(submission: Path) -> int:
    report = gatekeep_submission(submission)
    for line in report_lines(report):
        print(line)
    return 0 if report.is_valid else 1


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Christmas Tree Packing baseline tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="generate the grid baseline")
    generate.add_argument("--output", type=Path, default=Path("submission.csv"))

    evaluate = subparsers.add_parser("evaluate", help="evaluate a submission")
    evaluate.add_argument("submission", type=Path)
    evaluate.add_argument("--quiet", action="store_true")

    gatekeep = subparsers.add_parser("gatekeep", help="run the full disk-backed gatekeeper")
    gatekeep.add_argument("submission", type=Path)

    visualize = subparsers.add_parser("visualize", help="visualize one configuration")
    visualize.add_argument("submission", type=Path)
    visualize.add_argument("--n", type=int, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface and return its exit code."""
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        return _generate(args.output)
    if args.command == "evaluate":
        return _evaluate(args.submission, args.quiet)
    if args.command == "gatekeep":
        return _gatekeep(args.submission)
    return _visualize(args.submission, args.n)


if __name__ == "__main__":
    raise SystemExit(main())
