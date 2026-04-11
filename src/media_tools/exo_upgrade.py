"""Convert AviUtl 1.00 English .exo files to AviUtl 1.16d Chinese .exo format."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from ._srt import read_text_with_fallback

_HEADER_KEYS = ("width", "height", "rate", "scale", "length", "audio_rate", "audio_ch")
_SECTION_RE = re.compile(r"^\[(\d+)(?:\.(\d+))?\]$")

# Target property keys required by AviUtl 1.16d Chinese edition .exo format.
_TEXT_KEY_MAP = {
    "Size": "大小",
    "vDisplay": "显示速度",
    "1char1obj": "独立每个文字",
    "Show on motion coordinate": "在路径上显示",
    "Automatic scrolling": "自动滚动",
    "Text": "文本",
}

_DRAW_KEY_MAP = {
    "Zoom%": "缩放率",
    "Clearness": "透明度",
    "Rotation": "旋转",
    "Standard drawing": "标准变换",
}


def convert_exo_100_to_116(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    add_stroke: bool = False,
    stroke_size: int = 3,
    stroke_blur: int = 50,
    stroke_color: str = "00ff00",
    input_encoding: str | None = None,
    output_encoding: str = "gbk",
) -> tuple[Path, int]:
    """Upgrade an AviUtl 1.00 English .exo file to AviUtl 1.16d Chinese .exo format."""
    src = Path(input_path)
    dst = Path(output_path) if output_path else src.with_name(f"{src.stem}_1.16{src.suffix}")
    content = read_text_with_fallback(
        src,
        encoding=input_encoding,
        fallback_encodings=("utf-8", "gbk", "shift_jis"),
    )

    output_lines: list[str] = ["[exedit]"]
    current_section: str | None = None
    obj_index = 0

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            output_lines.append("")
            continue

        if line.startswith("[exedit]"):
            continue

        if any(line.startswith(k) for k in _HEADER_KEYS):
            output_lines.append(line)
            continue

        section_match = _SECTION_RE.match(line)
        if section_match:
            minor = section_match.group(2)
            if minor is None:
                current_section = "main"
                output_lines.append(f"[{obj_index}]")
                obj_index += 1
            elif minor == "0":
                current_section = "text"
                output_lines.append(f"[{obj_index - 1}.0]")
            elif minor == "1":
                if add_stroke:
                    output_lines.extend(
                        [
                            f"[{obj_index - 1}.1]",
                            "_name=描边",
                            f"大小={stroke_size}",
                            f"模糊={stroke_blur}",
                            f"color={stroke_color.lstrip('#')}",
                            "file=",
                        ]
                    )
                current_section = "draw"
                output_lines.append(f"[{obj_index - 1}.2]")
            else:
                current_section = "other"
                output_lines.append(f"[{obj_index - 1}.{minor}]")
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            if current_section == "text":
                new_key = _TEXT_KEY_MAP.get(key, key)
                if key == "_name" and value == "Text":
                    value = _TEXT_KEY_MAP["Text"]
                output_lines.append(f"{new_key}={value}")
            elif current_section == "draw":
                new_key = _DRAW_KEY_MAP.get(key, key)
                if key == "_name" and value == "Standard drawing":
                    value = _DRAW_KEY_MAP["Standard drawing"]
                output_lines.append(f"{new_key}={value}")
            else:
                output_lines.append(line)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(output_lines), encoding=output_encoding, errors="replace", newline="\n")
    return dst, obj_index


def build_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    """Configure argument parser for exo-upgrade."""
    p = parser or argparse.ArgumentParser(
        description="Convert an AviUtl 1.00 English .exo file to AviUtl 1.16d Chinese .exo format."
    )
    p.add_argument("input", type=Path, help="Input AviUtl 1.00 .exo file path")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output AviUtl 1.16 .exo path")
    p.add_argument(
        "--add-stroke",
        action="store_true",
        help="Insert a default [n.1] stroke effect block before standard drawing",
    )
    p.add_argument("--stroke-size", type=int, default=3, help="Stroke size when --add-stroke is set")
    p.add_argument("--stroke-blur", type=int, default=50, help="Stroke blur when --add-stroke is set")
    p.add_argument(
        "--stroke-color",
        type=str,
        default="00ff00",
        help="Stroke hex color when --add-stroke is set (default: 00ff00)",
    )
    p.add_argument(
        "--input-encoding",
        type=str,
        default=None,
        help="Input encoding override (default: auto-detect utf-8/gbk/shift_jis)",
    )
    p.add_argument(
        "--output-encoding",
        type=str,
        default="gbk",
        help="Output .exo encoding (default: gbk)",
    )
    return p


def run_args(args: argparse.Namespace) -> int:
    """Execute exo-upgrade from parsed CLI arguments."""
    dst, count = convert_exo_100_to_116(
        input_path=args.input,
        output_path=args.output,
        add_stroke=args.add_stroke,
        stroke_size=args.stroke_size,
        stroke_blur=args.stroke_blur,
        stroke_color=args.stroke_color,
        input_encoding=args.input_encoding,
        output_encoding=args.output_encoding,
    )
    print(f"Converted {count} objects to {dst}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    return run_args(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
