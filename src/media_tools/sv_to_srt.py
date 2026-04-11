"""Convert a Sonic Visualiser XML or compressed .sv/.bz2 layer into an SRT subtitle file."""

from __future__ import annotations

import argparse
import bz2
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from ._srt import SubtitleEntry, write_srt


def _load_sv_root(input_path: Path) -> ET.Element:
    """Parse XML from a plain .xml file or a bzip2-compressed .sv/.bz2 file."""
    raw = input_path.read_bytes()
    if input_path.suffix.lower() in {".sv", ".bz2"} or raw.startswith(b"BZh"):
        xml_bytes = bz2.decompress(raw)
        return ET.fromstring(xml_bytes)
    return ET.fromstring(raw)


def list_time_instant_layers(input_path: str | Path) -> list[str]:
    """Return unique timeinstants layer presentationName values in document order."""
    root = _load_sv_root(Path(input_path))
    seen: set[str] = set()
    layers: list[str] = []
    for layer in root.findall(".//layer[@type='timeinstants']"):
        name = layer.get("presentationName")
        if name and name not in seen:
            seen.add(name)
            layers.append(name)
    return layers


def _frame_to_ms(frame: int, sample_rate: int) -> int:
    """Convert an audio frame index to milliseconds (truncated, matching timedelta ms)."""
    return int((float(frame) / float(sample_rate)) * 1000)


def convert_sv_to_srt(
    input_path: str | Path,
    output_path: str | Path | None = None,
    layer_name: str = "vocal",
    last_duration: float = 2.0,
    encoding: str = "utf-8",
) -> tuple[Path, int]:
    """Export time-instant markers from a Sonic Visualiser layer to an SRT file."""
    if last_duration <= 0:
        raise ValueError("last_duration must be positive.")

    src = Path(input_path)
    dst = Path(output_path) if output_path else src.with_suffix(".srt")
    root = _load_sv_root(src)

    models: dict[str, tuple[int, int, str | None]] = {}
    for model in root.findall(".//model"):
        m_id = model.get("id")
        if m_id is None:
            continue
        models[m_id] = (
            int(model.get("sampleRate", 44100)),
            int(model.get("end", 0)),
            model.get("dataset"),
        )

    model_id: str | None = None
    dataset_id: str | None = None
    for layer in root.findall(".//layer[@type='timeinstants']"):
        if layer.get("presentationName") == layer_name:
            model_id = layer.get("model")
            if model_id and model_id in models:
                dataset_id = models[model_id][2]
            break

    if not dataset_id or model_id is None:
        available = list_time_instant_layers(src)
        available_msg = ", ".join(available) if available else "none"
        raise ValueError(
            f"Layer '{layer_name}' not found in {src}. Available timeinstants layers: {available_msg}"
        )

    dataset = root.find(f".//dataset[@id='{dataset_id}']")
    if dataset is None:
        raise ValueError(f"Dataset '{dataset_id}' referenced by layer '{layer_name}' was not found.")

    points = sorted(
        (
            (int(point.get("frame", "0")), point.get("label", ""))
            for point in dataset.findall("point")
        ),
        key=lambda item: item[0],
    )

    sample_rate, model_end_frame, _ = models[model_id]
    entries: list[SubtitleEntry] = []
    for idx, (start_frame, label) in enumerate(points):
        if idx + 1 < len(points):
            end_frame = points[idx + 1][0]
        else:
            end_frame = max(start_frame + round(sample_rate * last_duration), model_end_frame)

        entries.append(
            SubtitleEntry(
                index=idx + 1,
                start_ms=_frame_to_ms(start_frame, sample_rate),
                end_ms=_frame_to_ms(end_frame, sample_rate),
                text=label,
            )
        )

    count = write_srt(entries, dst, encoding=encoding)
    return dst, count


def build_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    """Configure argument parser for sv-to-srt."""
    p = parser or argparse.ArgumentParser(
        description="Convert Sonic Visualiser (.xml, .sv, .bz2) time-instant markers to SRT."
    )
    p.add_argument("input", type=Path, help="Input Sonic Visualiser XML, .sv, or .bz2 path")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output SRT path")
    p.add_argument(
        "-l",
        "--layer",
        type=str,
        default="vocal",
        help="Target timeinstants layer presentationName (default: vocal)",
    )
    p.add_argument(
        "--list-layers",
        action="store_true",
        help="List available timeinstants layers in the input file and exit",
    )
    p.add_argument(
        "--last-duration",
        type=float,
        default=2.0,
        help="Minimum duration in seconds for the final marker (default: 2.0)",
    )
    p.add_argument(
        "--encoding",
        type=str,
        default="utf-8",
        help="Output SRT file encoding (default: utf-8)",
    )
    return p


def run_args(args: argparse.Namespace) -> int:
    """Execute sv-to-srt from parsed CLI arguments."""
    if args.list_layers:
        layers = list_time_instant_layers(args.input)
        if not layers:
            print("No timeinstants layers found.")
        else:
            print("Available timeinstants layers:")
            for name in layers:
                print(f"  - {name}")
        return 0

    dst, count = convert_sv_to_srt(
        input_path=args.input,
        output_path=args.output,
        layer_name=args.layer,
        last_duration=args.last_duration,
        encoding=args.encoding,
    )
    print(f"Exported {count} cues to {dst} (layer: {args.layer})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    return run_args(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
