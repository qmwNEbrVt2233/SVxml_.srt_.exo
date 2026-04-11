"""Convert SRT subtitles into an AviUtl (.exo) project object file."""

from __future__ import annotations

import argparse
import binascii
from pathlib import Path
import sys

from ._srt import SubtitleEntry, parse_srt


def ms_to_frame(ms: int, fps: int) -> int:
    """Convert milliseconds to a 1-based AviUtl frame index."""
    return int(round((ms / 1000.0) * fps)) + 1


def text_to_exo_hex(text: str, pad_chars: int = 4096) -> str:
    """Encode text as UTF-16LE hex zero-padded to AviUtl's fixed 4096-hex-char buffer."""
    normalized = text.replace("\\n", "\r\n").replace("\n", "\r\n")
    hex_str = binascii.hexlify(normalized.encode("utf-16-le")).decode("ascii")
    if len(hex_str) >= pad_chars:
        return hex_str[:pad_chars]
    return hex_str + ("0" * (pad_chars - len(hex_str)))


def convert_srt_to_exo(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    fps: int = 30,
    width: int = 780,
    height: int = 440,
    font: str = "SimHei",
    font_size: int = 25,
    color: str = "ffffff",
    shadow_color: str = "000000",
    x: float = 0.0,
    y: float | None = None,
    layer: int = 1,
    tail_frames: int = 30,
    audio_rate: int = 44100,
    audio_ch: int = 2,
    input_encoding: str | None = None,
    output_encoding: str = "shift_jis",
) -> tuple[Path, int]:
    """Convert an SRT subtitle file into an AviUtl .exo file."""
    if fps <= 0 or width <= 0 or height <= 0 or font_size <= 0 or layer <= 0:
        raise ValueError("fps, width, height, font_size, and layer must be positive.")

    src = Path(input_path)
    dst = Path(output_path) if output_path else src.with_suffix(".exo")
    subtitles: list[SubtitleEntry] = parse_srt(src, encoding=input_encoding)
    if not subtitles:
        raise ValueError(f"No valid subtitles found in {src}.")

    pos_y = float(height // 2 - 100) if y is None else float(y)
    total_length = ms_to_frame(subtitles[-1].end_ms, fps) + tail_frames
    last_end_frame = 0

    lines: list[str] = [
        "[exedit]",
        f"width={width}",
        f"height={height}",
        f"rate={fps}",
        "scale=1",
        f"length={total_length}",
        f"audio_rate={audio_rate}",
        f"audio_ch={audio_ch}",
        "",
    ]

    for idx, sub in enumerate(subtitles):
        start_frame = ms_to_frame(sub.start_ms, fps)
        end_frame = ms_to_frame(sub.end_ms, fps)

        if start_frame <= last_end_frame:
            start_frame = last_end_frame + 1
        if end_frame <= start_frame:
            end_frame = start_frame + 1
        last_end_frame = end_frame

        lines.extend(
            [
                f"[{idx}]",
                f"start={start_frame}",
                f"end={end_frame}",
                f"layer={layer}",
                "overlay=1",
                "camera=0",
                "",
                f"[{idx}.0]",
                "_name=Text",
                f"Size={font_size}",
                "vDisplay=0.0",
                "1char1obj=0",
                "B=0",
                "I=0",
                "type=0",
                "autoadjust=0",
                "soft=1",
                "monospace=0",
                "align=0",
                "spacing_x=0",
                "spacing_y=0",
                "precision=1",
                f"color={color.lstrip('#')}",
                f"color2={shadow_color.lstrip('#')}",
                f"font={font}",
                f"text={text_to_exo_hex(sub.text)}",
                "",
                f"[{idx}.1]",
                "_name=Standard drawing",
                f"X={x}",
                f"Y={pos_y}",
                "Z=0.0",
                "Zoom%=100.0",
                "Alpha=0.0",
                "Rotation=0.0",
                "blend=0",
                "",
            ]
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines), encoding=output_encoding, errors="replace", newline="\n")
    return dst, len(subtitles)


def build_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    """Configure argument parser for srt-to-exo."""
    p = parser or argparse.ArgumentParser(
        description="Convert an SRT subtitle file into an AviUtl .exo file."
    )
    p.add_argument("input", type=Path, help="Input SRT file path")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output EXO file path")
    p.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")
    p.add_argument("--width", type=int, default=780, help="Canvas width in pixels (default: 780)")
    p.add_argument("--height", type=int, default=440, help="Canvas height in pixels (default: 440)")
    p.add_argument("--font", type=str, default="SimHei", help="Font name (default: SimHei)")
    p.add_argument("--font-size", type=int, default=25, help="Font size (default: 25)")
    p.add_argument("--color", type=str, default="ffffff", help="Primary hex color (default: ffffff)")
    p.add_argument(
        "--shadow-color",
        type=str,
        default="000000",
        help="Secondary/shadow hex color (default: 000000)",
    )
    p.add_argument("--x", type=float, default=0.0, help="Text X coordinate (default: 0.0)")
    p.add_argument(
        "--y",
        type=float,
        default=None,
        help="Text Y coordinate (default: height // 2 - 100)",
    )
    p.add_argument("--layer", type=int, default=1, help="AviUtl layer index (default: 1)")
    p.add_argument(
        "--tail-frames",
        type=int,
        default=30,
        help="Extra frames appended to total length (default: 30)",
    )
    p.add_argument("--audio-rate", type=int, default=44100, help="Header audio_rate (default: 44100)")
    p.add_argument("--audio-ch", type=int, default=2, help="Header audio_ch (default: 2)")
    p.add_argument(
        "--input-encoding",
        type=str,
        default=None,
        help="Input SRT encoding (default: auto-detect utf-8-sig/utf-8/gbk)",
    )
    p.add_argument(
        "--output-encoding",
        type=str,
        default="shift_jis",
        help="Output EXO encoding (default: shift_jis)",
    )
    return p


def run_args(args: argparse.Namespace) -> int:
    """Execute srt-to-exo from parsed CLI arguments."""
    dst, count = convert_srt_to_exo(
        input_path=args.input,
        output_path=args.output,
        fps=args.fps,
        width=args.width,
        height=args.height,
        font=args.font,
        font_size=args.font_size,
        color=args.color,
        shadow_color=args.shadow_color,
        x=args.x,
        y=args.y,
        layer=args.layer,
        tail_frames=args.tail_frames,
        audio_rate=args.audio_rate,
        audio_ch=args.audio_ch,
        input_encoding=args.input_encoding,
        output_encoding=args.output_encoding,
    )
    print(f"Converted {count} subtitles to {dst}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    return run_args(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
