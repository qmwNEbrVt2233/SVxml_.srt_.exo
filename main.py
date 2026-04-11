"""Local runner for media-tools without requiring package installation."""

from __future__ import annotations

from pathlib import Path
import sys

_SRC_DIR = Path(__file__).resolve().parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from media_tools.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
