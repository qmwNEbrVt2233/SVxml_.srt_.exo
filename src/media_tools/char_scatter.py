"""Calculate symmetric character coordinates expanding outward from a fixed center."""

from __future__ import annotations

import argparse
import json
import sys


def calculate_positions(count: int, center: float, spacing: float) -> list[float]:
    """Compute character coordinates evenly spaced while preserving the center point."""
    if count <= 0:
        raise ValueError("count must be a positive integer.")
    half_index = (count - 1) / 2.0
    return [center + (idx - half_index) * spacing for idx in range(count)]


def compute_actual_center(positions: list[float]) -> float:
    """Compute the midpoint of the given sorted character positions."""
    if not positions:
        raise ValueError("positions must not be empty.")
    n = len(positions)
    if n % 2 == 0:
        return (positions[n // 2 - 1] + positions[n // 2]) / 2.0
    return positions[n // 2]


def build_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    """Configure argument parser for char-scatter."""
    p = parser or argparse.ArgumentParser(
        description="Calculate character coordinates evenly spaced around a fixed center point."
    )
    p.add_argument("-n", "--count", type=int, required=True, help="Total number of characters")
    p.add_argument("-c", "--center", type=float, required=True, help="Target center coordinate")
    p.add_argument("-s", "--spacing", type=float, required=True, help="Spacing between characters")
    p.add_argument(
        "--precision",
        type=int,
        default=6,
        help="Decimal precision for text output (default: 6)",
    )
    p.add_argument("--json", action="store_true", help="Output result as JSON")
    return p


def run_args(args: argparse.Namespace) -> int:
    """Execute char-scatter from parsed CLI arguments."""
    positions = calculate_positions(args.count, args.center, args.spacing)
    actual_center = compute_actual_center(positions)
    verified = abs(actual_center - args.center) < 1e-6

    if args.json:
        payload = {
            "count": args.count,
            "target_center": args.center,
            "actual_center": actual_center,
            "spacing": args.spacing,
            "verified": verified,
            "positions": positions,
        }
        print(json.dumps(payload, indent=2))
        return 0 if verified else 1

    fmt = f".{args.precision}g"
    print("Computed coordinates:")
    for idx, pos in enumerate(positions, start=1):
        print(f"  Char {idx}: {format(pos, fmt)}")
    print(f"Verified center: {format(actual_center, fmt)} (target: {format(args.center, fmt)})")
    print("Status: PASS" if verified else "Status: FAIL")
    return 0 if verified else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    return run_args(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
