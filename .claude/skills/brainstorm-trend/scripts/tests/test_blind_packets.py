"""Blind packets: what each judge sees, and nothing about who drew it."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import blind_packets as BP  # noqa: E402

POOL = [
    {"id": "storyteller", "name": "Storyteller", "leans": "form"},
    {"id": "cam-whisperer", "name": "Cam Whisperer", "leans": "mechanism"},
    {"id": "walker", "name": "Walker", "leans": "mechanism"},
]

CONTRACT = """# Daybreak

A night slab that opens into a dawn landscape. Designed by the Storyteller.

## Trend Hook

The one seam down the middle.

## Signature Motion

Open either leaf and a sun rises; the walker on the hill stays put.

## Palette

- spine: navy PLA

## Joints

Pins everywhere.

```design-contract
{"title": "Daybreak"}
```
"""


def _slot(run: Path, slot: str, text: str = CONTRACT, preview: str = "preview.png") -> None:
    (run / slot).mkdir(parents=True)
    (run / slot / "CONTRACT.md").write_text(text)
    (run / slot / preview).write_bytes(b"image-" + slot.encode())


SCHEDULE = {"matches": [
    {"index": 0, "a": "candidate-1", "b": "candidate-2"},
    {"index": 1, "a": "candidate-2", "b": "candidate-1"},
]}


class PacketTextTests(unittest.TestCase):
    def test_keeps_the_title_and_the_three_sections_only(self) -> None:
        text = BP.packet_text(CONTRACT)
        self.assertEqual(
            text,
            "# Daybreak\n\n"
            "## Trend Hook\n\nThe one seam down the middle.\n\n"
            "## Signature Motion\n\n"
            "Open either leaf and a sun rises; the walker on the hill stays put.\n\n"
            "## Palette\n\n- spine: navy PLA\n",
        )

    def test_a_missing_section_is_refused(self) -> None:
        with self.assertRaisesRegex(BP.PacketError, "no Palette section"):
            BP.packet_text(CONTRACT.replace("## Palette", "## Colours"))


class NamedPersonalityTests(unittest.TestCase):
    def test_finds_a_pool_name_or_hyphenated_id_and_the_word_personality(self) -> None:
        text = "A Cam Whisperer build, cam-whisperer style, by this personality."
        self.assertEqual(
            BP.named_personalities(text, POOL),
            ["Cam Whisperer", "cam-whisperer", "personality"],
        )

    def test_an_ordinary_lowercase_word_is_not_a_name(self) -> None:
        self.assertEqual(BP.named_personalities("the walker on the hill", POOL), [])


class BuildTests(unittest.TestCase):
    def test_writes_a_and_b_for_every_match_in_scheduled_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run, out = Path(directory) / "run", Path(directory) / "packets"
            clean = CONTRACT.replace(" Designed by the Storyteller.", "")
            _slot(run, "candidate-1", clean)
            _slot(run, "candidate-2", clean.replace("Daybreak", "Moth"), preview="preview.jpg")
            written = BP.build_packets(SCHEDULE, run, out, POOL)
            self.assertEqual(written, [out / "match-00", out / "match-01"])
            self.assertTrue((out / "match-01" / "A.md").read_text().startswith("# Moth"))
            self.assertEqual((out / "match-01" / "A.jpg").read_bytes(), b"image-candidate-2")
            self.assertEqual((out / "match-01" / "B.png").read_bytes(), b"image-candidate-1")

    def test_the_intro_paragraph_never_reaches_a_judge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run, out = Path(directory) / "run", Path(directory) / "packets"
            _slot(run, "candidate-1")
            _slot(run, "candidate-2")
            BP.build_packets(SCHEDULE, run, out, POOL)
            self.assertNotIn("Storyteller", (out / "match-00" / "A.md").read_text())

    def test_a_section_naming_a_personality_refuses_every_packet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run, out = Path(directory) / "run", Path(directory) / "packets"
            _slot(run, "candidate-1", CONTRACT.replace("The one seam", "The Storyteller's seam"))
            _slot(run, "candidate-2")
            with self.assertRaisesRegex(BP.PacketError, "candidate-1 names Storyteller"):
                BP.build_packets(SCHEDULE, run, out, POOL)
            self.assertFalse(out.exists())

    def test_a_slot_without_a_preview_image_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run, out = Path(directory) / "run", Path(directory) / "packets"
            _slot(run, "candidate-1")
            (run / "candidate-2").mkdir()
            (run / "candidate-2" / "CONTRACT.md").write_text(CONTRACT)
            with self.assertRaisesRegex(BP.PacketError, "candidate-2 has no Preview Image"):
                BP.build_packets(SCHEDULE, run, out, POOL)


class CliTests(unittest.TestCase):
    def test_refusal_exits_2_with_every_reason(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run, out = Path(directory) / "run", Path(directory) / "packets"
            _slot(run, "candidate-1", CONTRACT.replace("The one seam", "A Storyteller seam"))
            _slot(run, "candidate-2", CONTRACT.replace("The one seam", "A Walker seam"))
            schedule = Path(directory) / "schedule.json"
            schedule.write_text(json.dumps(SCHEDULE))
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_ROOT / "blind_packets.py"),
                 "--schedule", str(schedule), "--run-dir", str(run), "--out", str(out)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("candidate-1 names Storyteller", result.stderr)
            self.assertIn("candidate-2 names Walker", result.stderr)


if __name__ == "__main__":
    unittest.main()
