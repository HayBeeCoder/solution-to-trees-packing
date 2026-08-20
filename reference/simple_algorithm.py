#!/usr/bin/env python3
"""
Christmas Tree Packing Challenge - Simple Algorithm

This script generates a baseline submission by placing trees in a simple grid pattern.
It's not optimized but provides a valid starting point that you can improve upon.

Usage:
    python simple_algorithm.py
    python simple_algorithm.py --output my_submission.csv

This will generate a submission file that can be evaluated with:
    python evaluator.py submission.csv
"""

import argparse
import math

import pandas as pd


def generate_grid_positions(n):
    """
    Generate positions for n trees in a simple grid pattern.

    Trees are placed in a grid with spacing large enough to avoid overlaps.
    The tree dimensions are approximately 0.7 wide and 1.0 tall, so we use
    spacing of 0.8 to ensure no overlaps.

    Args:
        n: Number of trees to place

    Returns:
        List of (x, y, deg) tuples for each tree
    """
    if n == 0:
        return []

    # Tree is about 0.7 wide and 1.0 tall
    # Use spacing larger than the tree dimensions to avoid overlaps
    spacing = 1.1

    # Calculate grid dimensions
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    positions = []
    tree_count = 0

    for row in range(rows):
        for col in range(cols):
            if tree_count >= n:
                break

            # Center the grid around origin
            x = (col - (cols - 1) / 2) * spacing
            y = (row - (rows - 1) / 2) * spacing

            # No rotation for simplicity
            deg = 0.0

            positions.append((x, y, deg))
            tree_count += 1

    return positions


def generate_submission(output_path):
    """
    Generate a complete submission file with all 200 configurations.

    Args:
        output_path: Path to save the submission CSV
    """
    rows = []

    for n in range(1, 201):
        positions = generate_grid_positions(n)

        for t, (x, y, deg) in enumerate(positions):
            # Format: id is NNN_T where NNN is zero-padded n, T is tree index
            row_id = f'{n:03d}_{t}'

            # Values must be strings prefixed with 's'
            rows.append({
                'id': row_id,
                'x': f's{x:.6f}',
                'y': f's{y:.6f}',
                'deg': f's{deg:.6f}'
            })

        if n % 50 == 0:
            print(f"Generated configurations 1-{n}...")

    # Create DataFrame and save
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"\nSubmission saved to: {output_path}")
    print(f"Total rows: {len(rows)}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate a simple baseline submission for the Christmas Tree Packing Challenge'
    )
    parser.add_argument(
        '--output', '-o',
        default='submission.csv',
        help='Output file path (default: submission.csv)'
    )

    args = parser.parse_args()

    print("Generating simple grid-based submission...")
    print("This places trees in a grid pattern without optimization.\n")

    generate_submission(args.output)

    print("\nTo evaluate this submission, run:")
    print(f"  python evaluator.py {args.output}")
    print("\nTo visualize a configuration (e.g., 10 trees), run:")
    print(f"  python evaluator.py {args.output} --visualize 10")


if __name__ == '__main__':
    main()
