"""Convert SRT subtitles into an m7-editor project JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from ._srt import SubtitleEntry, parse_srt


def _build_m7_item(
    item_id: str,
    layer: int,
    start_time: int,
    text: str,
    duration: int,
    *,
    font: str,
    font_size: int,
    color: str,
    stroke: bool,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    z_rotate: float,
    y_rotate: float,
    opacity_from: float,
    opacity_to: float,
    move_duration: int,
    delay: int,
    easing: str,
) -> dict[str, Any]:
    """Construct a single m7-editor danmaku object."""
    return {
        "id": item_id,
        "layer": layer,
        "startTime": start_time,
        "content": {
            "text": text,
            "font": font,
            "size": font_size,
            "color": color,
            "stroke": stroke,
        },
        "transform": {
            "start": {"x": start_x, "y": start_y},
            "end": {"x": end_x, "y": end_y},
            "zRotate": z_rotate,
            "yRotate": y_rotate,
        },
        "opacity": {
            "from": opacity_from,
            "to": opacity_to,
        },
        "animation": {
            "duration": duration,
            "moveDuration": move_duration,
            "delay": delay,
            "easing": easing,
        },
    }


def convert_srt_to_m7(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    layer: int = 0,
    font: str = "SimHei",
    font_size: int = 25,
    color: str = "#ffffff",
    stroke: bool = True,
    start_x: float = 0,
    start_y: float = 0,
    end_x: float = 0,
    end_y: float = 0,
    z_rotate: float = 0,
    y_rotate: float = 0,
    opacity_from: float = 1,
    opacity_to: float = 1,
    move_duration: int = 500,
    delay: int = 0,
    easing: str = "speeddown",
    include_anchor: bool = False,
    input_encoding: str | None = None,
) -> tuple[Path, int]:
    """Convert an SRT subtitle file to an m7-editor JSON array."""
    src = Path(input_path)
    dst = Path(output_path) if output_path else src.with_suffix(".json")
    subtitles: list[SubtitleEntry] = parse_srt(src, encoding=input_encoding)

    common = {
        "font": font,
        "font_size": font_size,
        "color": color,
        "stroke": stroke,
        "start_x": start_x,
        "start_y": start_y,
        "end_x": end_x,
        "end_y": end_y,
        "z_rotate": z_rotate,
        "y_rotate": y_rotate,
        "opacity_from": opacity_from,
        "opacity_to": opacity_to,
        "move_duration": move_duration,
        "delay": delay,
        "easing": easing,
    }

    items: list[dict[str, Any]] = []
    if include_anchor:
        items.append(_build_m7_item("0", 1, 0, "0", 100, **common))

    for idx, sub in enumerate(subtitles):
        duration = max(0, sub.end_ms - sub.start_ms)
        items.append(
            _build_m7_item(str(idx), layer, sub.start_ms, sub.text, duration, **common)
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return dst, len(subtitles)


def build_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    """Configure argument parser for srt-to-m7."""
    p = parser or argparse.ArgumentParser(
        description="Convert an SRT subtitle file into an m7-editor JSON file."
    )
    p.add_argument("input", type=Path, help="Input SRT file path")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output JSON file path")
    p.add_argument("--layer", type=int, default=0, help="Target m7-editor layer (default: 0)")
    p.add_argument("--font", type=str, default="SimHei", help="Font name (default: SimHei)")
    p.add_argument("--font-size", type=int, default=25, help="Font size (default: 25)")
    p.add_argument("--color", type=str, default="#ffffff", help="Text hex color (default: #ffffff)")
    p.add_argument("--no-stroke", action="store_true", help="Disable text stroke")
    p.add_argument("--start-x", type=float, default=0, help="Transform start X (default: 0)")
    p.add_argument("--start-y", type=float, default=0, help="Transform start Y (default: 0)")
    p.add_argument("--end-x", type=float, default=0, help="Transform end X (default: 0)")
    p.add_argument("--end-y", type=float, default=0, help="Transform end Y (default: 0)")
    p.add_argument("--z-rotate", type=float, default=0, help="Z rotation in degrees (default: 0)")
    p.add_argument("--y-rotate", type=float, default=0, help="Y rotation in degrees (default: 0)")
    p.add_argument("--opacity-from", type=float, default=1, help="Start opacity (default: 1)")
    p.add_argument("--opacity-to", type=float, default=1, help="End opacity (default: 1)")
    p.add_argument(
        "--move-duration",
        type=int,
        default=500,
        help="Move animation duration in ms (default: 500)",
    )
    p.add_argument("--delay", type=int, default=0, help="Animation delay in ms (default: 0)")
    p.add_argument(
        "--easing",
        type=str,
        default="speeddown",
        help="Animation easing name (default: speeddown)",
    )
    p.add_argument(
        "--include-anchor",
        action="store_true",
        help="Prepend a legacy layer-1 anchor item at 0ms",
    )
    p.add_argument(
        "--input-encoding",
        type=str,
        default=None,
        help="Input SRT encoding (default: auto-detect utf-8-sig/utf-8/gbk)",
    )
    return p


def run_args(args: argparse.Namespace) -> int:
    """Execute srt-to-m7 from parsed CLI arguments."""
    dst, count = convert_srt_to_m7(
        input_path=args.input,
        output_path=args.output,
        layer=args.layer,
        font=args.font,
        font_size=args.font_size,
        color=args.color,
        stroke=not args.no_stroke,
        start_x=args.start_x,
        start_y=args.start_y,
        end_x=args.end_x,
        end_y=args.end_y,
        z_rotate=args.z_rotate,
        y_rotate=args.y_rotate,
        opacity_from=args.opacity_from,
        opacity_to=args.opacity_to,
        move_duration=args.move_duration,
        delay=args.delay,
        easing=args.easing,
        include_anchor=args.include_anchor,
        input_encoding=args.input_encoding,
    )
    print(f"Exported {count} items to {dst}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    return run_args(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
