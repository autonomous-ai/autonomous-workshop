"""design-a-toy Stage 3a: the Contract Proof's image tool (ADR 0093)."""

import argparse
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

REPOSITORY = Path(__file__).resolve().parents[2]
TOOL = REPOSITORY / ".claude" / "skills" / "design-a-toy" / "scripts" / "proof_views.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("proof_views_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


proof_views = _load_tool()

BACKGROUND = (245, 240, 230)


def _sheet(path, boxes, size=(900, 300)):
    image = Image.new("RGB", size, BACKGROUND)
    draw = ImageDraw.Draw(image)
    for box in boxes:
        draw.rectangle(box, fill=(40, 40, 40))
    image.save(path)


class SplitTests(unittest.TestCase):
    def test_cuts_a_three_view_sheet_at_its_empty_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            sheet = Path(tmp) / "sheet.png"
            _sheet(sheet, [(50, 60, 200, 240), (350, 100, 480, 200), (650, 40, 820, 260)])
            paths = proof_views.split(sheet, Path(tmp) / "views")
            self.assertEqual([Path(p).name for p in paths], ["view-1.png", "view-2.png", "view-3.png"])
            for path in paths:
                view = Image.open(path)
                self.assertEqual(view.width, view.height)

    def test_scales_a_large_view_down_to_the_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            sheet = Path(tmp) / "sheet.png"
            _sheet(sheet, [(20, 20, 1900, 980)], size=(2000, 1000))
            (path,) = proof_views.split(sheet, Path(tmp) / "views", max_side=400)
            self.assertEqual(Image.open(path).size, (400, 400))


class InputTests(unittest.TestCase):
    def test_camera_is_parsed_and_range_checked(self):
        self.assertEqual(proof_views.parse_camera("-90,15"), (-90.0, 15.0))
        with self.assertRaises(argparse.ArgumentTypeError):
            proof_views.parse_camera("200,0")
        with self.assertRaises(argparse.ArgumentTypeError):
            proof_views.parse_camera("0,95")

    def test_contract_without_a_block_is_refused(self):
        with self.assertRaises(ValueError):
            proof_views.contract_block("# A contract\n\nNo block here.\n")

    def test_contract_block_is_read(self):
        text = '# C\n\n```design-contract\n{"schema_version": 8, "references": []}\n```\n'
        self.assertEqual(proof_views.contract_block(text)["schema_version"], 8)

    def test_proof_needs_exactly_one_combined_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            proof = Path(tmp)
            (proof / "part_door.step.py").write_text("")
            with self.assertRaises(ValueError):
                proof_views.combined_entry(proof)
            (proof / "cabinet.step.py").write_text("")
            self.assertEqual(proof_views.combined_entry(proof).name, "cabinet.step.py")
            (proof / "other.step.py").write_text("")
            with self.assertRaises(ValueError):
                proof_views.combined_entry(proof)


if __name__ == "__main__":
    unittest.main()
