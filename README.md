# Media Tools

A lightweight, pure-Python CLI toolkit for subtitle, danmaku, AviUtl `.exo`, Sonic Visualiser, and text-animation workflows.

## Project Structure

```text
.
├── main.py                  # Local CLI launcher (zero-install usage)
├── pyproject.toml           # Package metadata & console script entrypoints
├── samples/                 # Sample input/reference files
├── src/
│   └── media_tools/
│       ├── _srt.py          # Shared SRT parser/writer & encoding helpers
│       ├── char_scatter.py  # Symmetric character coordinate calculator
│       ├── cli.py           # Unified subcommand dispatcher
│       ├── danmaku_scale.py # Bilibili mode-7 danmaku coordinate scaler
│       ├── dashed_lines.py  # Random dashed-line generator
│       ├── exo_upgrade.py   # AviUtl 1.00 EN -> 1.16d CN .exo converter
│       ├── srt_to_exo.py    # SRT -> AviUtl .exo converter
│       ├── srt_to_m7.py     # SRT -> m7-editor JSON converter
│       └── sv_to_srt.py     # Sonic Visualiser XML/.sv/.bz2 -> SRT converter
└── tests/
    └── test_tools.py        # Unit & CLI integration tests
```

## Requirements

- Python 3.10+ (standard library only; no third-party runtime dependencies)

## Usage

Run directly from the repository root with `python main.py <command> [flags]`, or install locally with `pip install -e .` to use `media-tools <command> [flags]` and individual command names.

```bash
python main.py --help
```

### 1. `sv-to-srt` — Sonic Visualiser to SRT

Export `timeinstants` markers from a Sonic Visualiser `.xml`, `.sv`, or `.bz2` file into `.srt`.

```bash
# List available timeinstants layers
python main.py sv-to-srt samples/sonic_visualiser.xml --list-layers

# Export a specific layer
python main.py sv-to-srt samples/sonic_visualiser.xml -l "Sound effects & secondary lead" -o output.srt
```

### 2. `srt-to-exo` — SRT to AviUtl EXO

Convert an `.srt` subtitle file into an AviUtl `.exo` object file with configurable canvas, font, and layout flags.

```bash
python main.py srt-to-exo samples/subtitles.srt -o output.exo --fps 30 --width 1280 --height 720 --font Arial --font-size 36
```

### 3. `srt-to-m7` — SRT to m7-editor JSON

Convert an `.srt` subtitle file into an `m7-editor` JSON array for pasting or importing.

```bash
python main.py srt-to-m7 samples/subtitles.srt -o project.json --layer 0 --font SimHei --font-size 25 --color "#ffffff"
```

### 4. `exo-upgrade` — AviUtl 1.00 EN to 1.16d CN EXO

Upgrade an AviUtl 1.00 English `.exo` file to AviUtl 1.16d Chinese `.exo` format.

```bash
python main.py exo-upgrade samples/aviutl_100.exo -o converted.exo
```

### 5. `danmaku-scale` — Scale Mode-7 Danmaku Coordinates

Scale proportional `0~1` coordinates in Bilibili mode-7 danmaku XML files to integer pixel coordinates.

```bash
python main.py danmaku-scale danmaku.xml -W 1920 -H 1080 -o danmaku_1920x1080.xml
```

### 6. `dashed-lines` — Random Dashed Line Generator

Generate random alternating dash/gap lines of fixed width.

```bash
python main.py dashed-lines --lines 33 --width 67 --max-seg 6 --seed 42 -o dashed_lines.txt
```

### 7. `char-scatter` — Center-Outward Character Coordinate Calculator

Compute evenly spaced character coordinates around a fixed center point.

```bash
python main.py char-scatter --count 5 --center 960 --spacing 40
python main.py char-scatter -n 5 -c 960 -s 40 --json
```

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
