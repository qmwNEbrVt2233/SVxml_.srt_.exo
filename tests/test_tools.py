"""Unit and CLI integration tests for media_tools."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from media_tools import cli  # noqa: E402
from media_tools._srt import format_srt_timestamp, parse_srt, parse_srt_timestamp  # noqa: E402
from media_tools.char_scatter import calculate_positions, compute_actual_center  # noqa: E402
from media_tools.danmaku_scale import convert_danmaku_xml  # noqa: E402
from media_tools.dashed_lines import generate_dashed_lines  # noqa: E402
from media_tools.exo_upgrade import convert_exo_100_to_116  # noqa: E402
from media_tools.srt_to_exo import convert_srt_to_exo, text_to_exo_hex  # noqa: E402
from media_tools.srt_to_m7 import convert_srt_to_m7  # noqa: E402
from media_tools.sv_to_srt import convert_sv_to_srt, list_time_instant_layers  # noqa: E402

SAMPLES_DIR = _ROOT / "samples"


class TestSrtHelpers(unittest.TestCase):
    def test_timestamp_roundtrip(self) -> None:
        ms = parse_srt_timestamp("01:02:03,456")
        self.assertEqual(ms, 3_723_456)
        self.assertEqual(format_srt_timestamp(ms), "01:02:03,456")

    def test_parse_sample_srt(self) -> None:
        entries = parse_srt(SAMPLES_DIR / "subtitles.srt")
        self.assertEqual(len(entries), 36)
        self.assertEqual(entries[0].text, "7.2")
        self.assertEqual(entries[0].start_ms, 1613)
        self.assertEqual(entries[0].end_ms, 1826)


class TestSvToSrt(unittest.TestCase):
    def test_list_layers_and_convert_xml_and_bz2(self) -> None:
        layers = list_time_instant_layers(SAMPLES_DIR / "sonic_visualiser.xml")
        self.assertIn("Sound effects & secondary lead", layers)
        self.assertIn("vocal", layers)

        with tempfile.TemporaryDirectory() as tmp:
            out_xml_srt = Path(tmp) / "from_xml.srt"
            dst, count = convert_sv_to_srt(
                SAMPLES_DIR / "sonic_visualiser.xml",
                out_xml_srt,
                layer_name="Sound effects & secondary lead",
            )
            self.assertEqual(dst, out_xml_srt)
            self.assertGreater(count, 0)
            parsed = parse_srt(out_xml_srt)
            self.assertEqual(len(parsed), count)

            out_bz2_srt = Path(tmp) / "from_bz2.srt"
            _, bz2_count = convert_sv_to_srt(
                SAMPLES_DIR / "sonic_visualiser.sv.bz2",
                out_bz2_srt,
                layer_name="vocal",
            )
            self.assertGreater(bz2_count, 0)

    def test_missing_layer_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                convert_sv_to_srt(
                    SAMPLES_DIR / "sonic_visualiser.xml",
                    Path(tmp) / "out.srt",
                    layer_name="nonexistent-layer",
                )


class TestSrtConverters(unittest.TestCase):
    def test_srt_to_exo(self) -> None:
        self.assertEqual(len(text_to_exo_hex("abc")), 4096)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.exo"
            dst, count = convert_srt_to_exo(
                SAMPLES_DIR / "subtitles.srt",
                out,
                fps=60,
                width=1920,
                height=1080,
                font="Arial",
                font_size=40,
            )
            self.assertEqual(dst, out)
            self.assertEqual(count, 36)
            content = out.read_text(encoding="shift_jis")
            self.assertIn("width=1920", content)
            self.assertIn("height=1080", content)
            self.assertIn("rate=60", content)
            self.assertIn("font=Arial", content)
            self.assertIn("Size=40", content)

    def test_srt_to_m7(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "project.json"
            dst, count = convert_srt_to_m7(
                SAMPLES_DIR / "subtitles.srt",
                out,
                layer=2,
                font="Noto Sans",
                font_size=32,
                color="#00ffcc",
                stroke=False,
                easing="linear",
            )
            self.assertEqual(dst, out)
            self.assertEqual(count, 36)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 36)
            self.assertEqual(data[0]["layer"], 2)
            self.assertEqual(data[0]["content"]["font"], "Noto Sans")
            self.assertEqual(data[0]["content"]["size"], 32)
            self.assertEqual(data[0]["content"]["color"], "#00ffcc")
            self.assertFalse(data[0]["content"]["stroke"])
            self.assertEqual(data[0]["animation"]["easing"], "linear")


class TestExoUpgrade(unittest.TestCase):
    def test_matches_expected_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "converted.exo"
            dst, obj_count = convert_exo_100_to_116(SAMPLES_DIR / "aviutl_100.exo", out)
            self.assertEqual(dst, out)
            self.assertEqual(obj_count, 2)
            actual = out.read_text(encoding="gbk").replace("\r\n", "\n")
            expected = (SAMPLES_DIR / "aviutl_116_expected.exo").read_text(encoding="gbk").replace(
                "\r\n", "\n"
            )
            self.assertEqual(actual, expected)


class TestDanmakuScale(unittest.TestCase):
    def test_scales_mode7_coordinates(self) -> None:
        sample_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<i>"
            '<d p="1.5,7,25,16777215,0,0,0,0">[0.5,0.25,1,0,1,"hi",0,0.75,0.5]</d>'
            '<d p="2.0,1,25,16777215,0,0,0,0">normal danmaku</d>'
            "</i>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "danmaku.xml"
            out = Path(tmp) / "scaled.xml"
            src.write_text(sample_xml, encoding="utf-8")
            dst, count = convert_danmaku_xml(src, 1920, 1080, out)
            self.assertEqual(dst, out)
            self.assertEqual(count, 1)
            result = out.read_text(encoding="utf-8")
            self.assertIn('[960,270,1,0,1,"hi",0,1440,540]', result)


class TestDashedLines(unittest.TestCase):
    def test_exact_dimensions_and_determinism(self) -> None:
        lines_a = generate_dashed_lines(lines=10, width=25, max_seg=4, seed=42)
        lines_b = generate_dashed_lines(lines=10, width=25, max_seg=4, seed=42)
        self.assertEqual(lines_a, lines_b)
        self.assertEqual(len(lines_a), 10)
        self.assertTrue(all(len(line) == 25 for line in lines_a))


class TestCharScatter(unittest.TestCase):
    def test_even_and_odd_counts_preserve_center(self) -> None:
        for count in (4, 5):
            positions = calculate_positions(count=count, center=960.0, spacing=30.0)
            self.assertEqual(len(positions), count)
            self.assertAlmostEqual(compute_actual_center(positions), 960.0)


class TestCliDispatch(unittest.TestCase):
    def test_subcommands_via_cli_main(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            self.assertEqual(
                cli.main(["sv-to-srt", str(SAMPLES_DIR / "sonic_visualiser.xml"), "--list-layers"]),
                0,
            )
            self.assertEqual(
                cli.main(["char-scatter", "-n", "5", "-c", "500", "-s", "20", "--json"]),
                0,
            )
            dashed_out = tmp_dir / "dash.txt"
            self.assertEqual(
                cli.main(
                    ["dashed-lines", "--lines", "4", "--width", "12", "--max-seg", "3", "-o", str(dashed_out)]
                ),
                0,
            )
            self.assertTrue(dashed_out.exists())


if __name__ == "__main__":
    unittest.main()
