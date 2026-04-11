"""Generate random dashed text patterns for subtitle and danmaku effects."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


def generate_dashed_lines(
    lines: int,
    width: int,
    max_seg: int,
    *,
    dash_char: str = "\u2014",
    space_char: str = "\u3000",
    seed: int | None = None,
) -> list[str]:
    """Generate random alternating dash and space lines of exact character width."""
    if lines <= 0 or width <= 0 or max_seg <= 0:
        raise ValueError("lines, width, and max_seg must be positive integers.")
    if len(dash_char) != 1 or len(space_char) != 1:
        raise ValueError("dash_char and space_char must each be a single character.")

    rng = random.Random(seed)
    result: list[str] = []

    for _ in range(lines):
        line_chars: list[str] = []
        remaining = width
        use_dash = rng.choice([True, False])

        while remaining > 0:
            seg_len = rng.randint(1, min(max_seg, remaining))
            ch = dash_char if use_dash else space_char
            line_chars.append(ch * seg_len)
            remaining -= seg_len
            use_dash = not use_dash

        line = "".join(line_chars)
        result.append(line)

    return result


def write_dashed_file(
    output_path: str | Path,
    lines: int = 33,
    width: int = 67,
    max_seg: int = 6,
    *,
    dash_char: str = "\u2014",
    space_char: str = "\u3000",
    seed: int | None = None,
    encoding: str = "utf-8",
) -> Path:
    """Generate random dashed lines and write them to output_path."""
    dst = Path(output_path)
    generated = generate_dashed_lines(
        lines=lines,
        width=width,
        max_seg=max_seg,
        dash_char=dash_char,
        space_char=space_char,
        seed=seed,
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(generated) + "\n", encoding=encoding, newline="\n")
    return dst


def build_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    """Configure argument parser for dashed-lines."""
    p = parser or argparse.ArgumentParser(
        description="Generate a text file containing random dashed lines."
    )
    p.add_argument("--lines", type=int, default=33, help="Number of lines (default: 33)")
    p.add_argument("--width", type=int, default=67, help="Characters per line (default: 67)")
    p.add_argument("--max-seg", type=int, default=6, help="Maximum segment length (default: 6)")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("dashed_lines.txt"),
        help="Output file path (default: dashed_lines.txt)",
    )
    p.add_argument(
        "--dash-char",
        type=str,
        default="\u2014",
        help="Single character used for dashes (default: em-dash)",
    )
    p.add_argument(
        "--space-char",
        type=str,
        default="\u3000",
        help="Single character used for gaps (default: fullwidth space U+3000)",
    )
    p.add_argument("--seed", type=int, default=None, help="Optional RNG seed for reproducibility")
    p.add_argument("--encoding", type=str, default="utf-8", help="Output encoding (default: utf-8)")
    return p


def run_args(args: argparse.Namespace) -> int:
    """Execute dashed-lines from parsed CLI arguments."""
    dst = write_dashed_file(
        output_path=args.output,
        lines=args.lines,
        width=args.width,
        max_seg=args.max_seg,
        dash_char=args.dash_char,
        space_char=args.space_char,
        seed=args.seed,
        encoding=args.encoding,
    )
    print(f"Generated {dst.resolve()} ({args.lines} lines, {args.width} chars/line)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    return run_args(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
