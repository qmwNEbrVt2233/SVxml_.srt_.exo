"""Unified CLI entrypoint for media-tools subcommands."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import (
    __version__,
    char_scatter,
    danmaku_scale,
    dashed_lines,
    exo_upgrade,
    srt_to_exo,
    srt_to_m7,
    sv_to_srt,
)

_COMMANDS: tuple[tuple[str, str, Any], ...] = (
    ("sv-to-srt", "Convert Sonic Visualiser (.xml/.sv/.bz2) markers to SRT", sv_to_srt),
    ("srt-to-exo", "Convert SRT subtitles to an AviUtl .exo file", srt_to_exo),
    ("srt-to-m7", "Convert SRT subtitles to an m7-editor JSON file", srt_to_m7),
    ("exo-upgrade", "Convert AviUtl 1.00 English .exo to 1.16d Chinese .exo", exo_upgrade),
    ("danmaku-scale", "Scale 0~1 mode-7 danmaku XML coordinates to pixels", danmaku_scale),
    ("dashed-lines", "Generate a random dashed-line text pattern file", dashed_lines),
    ("char-scatter", "Calculate symmetric character scatter coordinates", char_scatter),
)


def build_parser() -> argparse.ArgumentParser:
    """Build top-level CLI parser with all tool subcommands."""
    parser = argparse.ArgumentParser(
        prog="media-tools",
        description="CLI toolkit for subtitle, danmaku, AviUtl EXO, and Sonic Visualiser workflows.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    for name, summary, module in _COMMANDS:
        subparser = subparsers.add_parser(name, help=summary, description=summary)
        module.build_parser(subparser)
        subparser.set_defaults(_handler=module.run_args)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args._handler(args))


if __name__ == "__main__":
    sys.exit(main())
