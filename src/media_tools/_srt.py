"""Shared SRT parsing, formatting, and text-encoding helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

_SRT_BLOCK_RE = re.compile(
    r"^\s*\d+\s*\n"
    r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n"
    r"([\s\S]*?)(?=\n\n|\Z)",
    re.MULTILINE,
)

DEFAULT_TEXT_ENCODINGS: tuple[str, ...] = ("utf-8-sig", "utf-8", "gbk")


@dataclass(frozen=True)
class SubtitleEntry:
    """Single SRT subtitle cue."""

    index: int
    start_ms: int
    end_ms: int
    text: str


def read_text_with_fallback(
    path: str | Path,
    encoding: str | None = None,
    fallback_encodings: tuple[str, ...] = DEFAULT_TEXT_ENCODINGS,
) -> str:
    """Read text file using explicit encoding or trying fallback encodings in order."""
    src = Path(path)
    if encoding:
        return src.read_text(encoding=encoding)

    last_error: UnicodeDecodeError | None = None
    for enc in fallback_encodings:
        try:
            return src.read_text(encoding=enc)
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    return src.read_text(encoding="utf-8")


def parse_srt_timestamp(timestamp: str) -> int:
    """Convert an SRT timestamp (HH:MM:SS,mmm) to milliseconds."""
    normalized = timestamp.strip().replace(".", ",")
    hms, ms_str = normalized.split(",")
    hours_str, minutes_str, seconds_str = hms.split(":")
    return (
        int(hours_str) * 3_600_000
        + int(minutes_str) * 60_000
        + int(seconds_str) * 1_000
        + int(ms_str)
    )


def format_srt_timestamp(ms: int) -> str:
    """Format milliseconds as an SRT timestamp (HH:MM:SS,mmm)."""
    if ms < 0:
        raise ValueError(f"Timestamp must be non-negative, got {ms}.")
    total_seconds, millis = divmod(ms, 1000)
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def parse_srt(path: str | Path, encoding: str | None = None) -> list[SubtitleEntry]:
    """Parse an SRT file into a list of SubtitleEntry items."""
    raw = read_text_with_fallback(path, encoding=encoding)
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")

    entries: list[SubtitleEntry] = []
    for idx, match in enumerate(_SRT_BLOCK_RE.finditer(normalized), start=1):
        start_str, end_str, text = match.groups()
        entries.append(
            SubtitleEntry(
                index=idx,
                start_ms=parse_srt_timestamp(start_str),
                end_ms=parse_srt_timestamp(end_str),
                text=text.strip(),
            )
        )
    return entries


def write_srt(
    entries: Iterable[SubtitleEntry],
    output_path: str | Path,
    encoding: str = "utf-8",
) -> int:
    """Write SubtitleEntry items to an SRT file and return the written cue count."""
    dst = Path(output_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    blocks: list[str] = []
    count = 0
    for idx, entry in enumerate(entries, start=1):
        start_ts = format_srt_timestamp(entry.start_ms)
        end_ts = format_srt_timestamp(entry.end_ms)
        blocks.append(f"{idx}\n{start_ts} --> {end_ts}\n{entry.text}")
        count += 1

    content = "\n\n".join(blocks) + ("\n" if blocks else "")
    dst.write_text(content, encoding=encoding, newline="\n")
    return count
