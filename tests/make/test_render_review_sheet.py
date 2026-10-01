"""The review sheet shows every requested view, labelled, in one image."""
import contextlib
import io
from pathlib import Path
import runpy
import tempfile
import unittest

from PIL import Image


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_review"


class ReviewSheetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = runpy.run_path(str(RENDERER))

    def test_tilted_views_face_each_side_from_above_or_below(self):
        views = self.renderer["NAMED_VIEWS"]
        faces = {"iso_front": "front", "iso_back": "back", "iso_left": "left", "iso_right": "right"}
        for tilted, face in faces.items():
            with self.subTest(view=tilted):
                azimuth, elevation = views[tilted]
                face_azimuth, _ = views[face]
                offset = (azimuth - face_azimuth + 180.0) % 360.0 - 180.0
                self.assertTrue(20.0 <= abs(offset) <= 30.0)
                self.assertTrue(20.0 <= elevation <= 30.0)
        self.assertGreater(views["iso_top"][1], 45.0)
        self.assertLess(views["iso_bottom"][1], -45.0)

    def test_sheet_lays_out_labelled_tiles_in_order(self):
        compose = self.renderer["compose_sheet"]
        colours = [(200, 0, 0), (0, 200, 0), (0, 0, 200), (200, 200, 0)]
        tiles = [("view%d" % i, Image.new("RGB", (50, 50), c)) for i, c in enumerate(colours)]
        sheet = compose(tiles, tile=40, columns=3)
        label = self.renderer["SHEET_LABEL_HEIGHT"]
        self.assertEqual(sheet.size, (120, 2 * (40 + label)))
        for index, colour in enumerate(colours):
            left, top = (index % 3) * 40, (index // 3) * (40 + label)
            self.assertEqual(sheet.getpixel((left + 20, top + label + 20)), colour)
        with self.assertRaises(ValueError):
            compose([])

    def test_cli_writes_each_view_and_the_sheet(self):
        from build123d import Box, export_step

        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "block.step"
            export_step(Box(10, 6, 4), source)
            out = Path(temporary) / "visual"
            argv = [str(source), "--view", "front", "--view", "iso_left", "--sheet",
                    "--size", "160", "-o", str(out)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.renderer["main"](argv), 0)
            self.assertEqual(sorted(p.name for p in out.iterdir()),
                             ["front.png", "iso_left.png", "sheet.png"])
            with Image.open(out / "sheet.png") as sheet:
                self.assertEqual(sheet.size[0], 3 * self.renderer["SHEET_TILE"])


if __name__ == "__main__":
    unittest.main()
