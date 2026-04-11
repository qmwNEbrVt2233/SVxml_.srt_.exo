"""Scale 0~1 proportional coordinates in Bilibili mode-7 danmaku XML to integer pixels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def convert_danmaku_xml(
    input_path: str | Path,
    width: int,
    height: int,
    output_path: str | Path | None = None,
) -> tuple[Path, int]:
    """Scale 0~1 coordinates in mode-7 danmakus to integer pixels."""
    src = Path(input_path)
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive integers.")

    dst = Path(output_path) if output_path else src.with_name(f"{src.stem}_{width}x{height}{src.suffix}")

    tree = ET.parse(src)
    root = tree.getroot()
    converted = 0

    for elem in root.findall("d"):
        p_parts = elem.attrib.get("p", "").split(",")
        if len(p_parts) < 2 or p_parts[1].strip() != "7" or not elem.text:
            continue

        try:
            arr = json.loads(elem.text)
        except json.JSONDecodeError:
            continue

        if not isinstance(arr, list):
            continue

        changed = False
        for idx, size in ((0, width), (1, height), (7, width), (8, height)):
            if idx >= len(arr):
                continue
            val = arr[idx]
            if isinstance(val, float) and 0 <= val <= 1:
                arr[idx] = round(val * size)
                changed = True

        if changed:
            elem.text = json.dumps(arr, ensure_ascii=False, separators=(",", ":"))
            converted += 1

    xml_body = ET.tostring(root, encoding="unicode")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(f'<?xml version="1.0" encoding="UTF-8"?>{xml_body}', encoding="utf-8", newline="\n")
    return dst, converted


def build_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    """Configure argument parser for danmaku-scale."""
    p = parser or argparse.ArgumentParser(
        description="Scale 0~1 proportional coordinates in mode-7 danmaku XML to integer pixels."
    )
    p.add_argument("input", type=Path, help="Input danmaku XML path")
    p.add_argument("-W", "--width", type=int, required=True, help="Target video width in pixels")
    p.add_argument("-H", "--height", type=int, required=True, help="Target video height in pixels")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output XML path")
    return p


def run_args(args: argparse.Namespace) -> int:
    """Execute danmaku-scale from parsed CLI arguments."""
    dst, converted = convert_danmaku_xml(args.input, args.width, args.height, args.output)
    print(f"Saved {dst} (converted {converted} danmakus)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    return run_args(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
