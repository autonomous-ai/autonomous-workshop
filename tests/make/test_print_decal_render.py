"""ADR 0091 decision 8: the review renders draw each Print Piece's art where
the part receives it, in the print stance and in the Display Pose."""
from __future__ import annotations

import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from tests.make.test_print_piece_features import LIBRARY, SECTION

SKILLS = LIBRARY.parents[2]
RENDER = SKILLS / "cad" / "scripts" / "render_review"
MAKE_ROUND = SKILLS / "make-round" / "scripts" / "make_round"

PART = '''from build123d import *
from features import print_details
pd = print_details.Details(nozzle=0.4)

def gen_step():
    body = Pos(0, 0, 10) * Box(60, 60, 20)
    return pd.print_recess(body, "sky", (0, 0, 20))

def assembly_pose(shape, pose):
    return shape.moved(Location((100, 0, 0), (0, 0, 1), 90))
'''


class DecalRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = runpy.run_path(str(LIBRARY))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name) / "cad"
        self.project.mkdir()
        subprocess.run([sys.executable, str(LIBRARY), "--install", str(self.project)], check=True,
                       capture_output=True)
        (self.project / "print" / "art").mkdir(parents=True)
        (self.project / "print" / "pieces.json").write_text(
            json.dumps({"title": "T", "print": SECTION}, indent=2, sort_keys=True))
        # A pure red sky, 20 x 30 mm at 300 dpi.
        Image.new("RGB", (237, 355), (255, 0, 0)).save(self.project / "print" / "art" / "print-01-a.png")
        (self.project / "part_box.step.py").write_text(PART)

    def render(self, entry, *views):
        out = self.project / "snap"
        done = subprocess.run([sys.executable, str(RENDER), entry, *("--view=%s" % v for v in views),
                               "--size", "300", "-o", str(out)], cwd=self.project,
                              capture_output=True, text=True, check=False, timeout=600)
        self.assertEqual(done.returncode, 0, done.stderr)
        return out

    def test_a_decal_name_round_trips_and_moves_with_its_part(self):
        read, move = self.library["read_decal"], self.library["move_decal"]
        name = "print-decal:sky:quad:0.0000,1.0000,0.0000,1.0000:1,2,3:4,0,0:0,5,0"
        decal = read(name)
        self.assertEqual(decal["piece"], "sky")
        self.assertEqual(decal["crop"], (0.0, 1.0, 0.0, 1.0))
        self.assertEqual(decal["u"], (4.0, 0.0, 0.0))
        self.assertIsNone(read("print-decal:sky:paint:0,1,0,1:1,2,3:4,0,0:0,5,0"))
        self.assertIsNone(read("print-recess:sky:abc"))
        from build123d import Location

        moved = move(decal, Location((10, 0, 0), (0, 0, 1), 90))
        self.assertAlmostEqual(moved["origin"][0], 8.0, places=4)   # (1,2,3) turned, then +10 x
        self.assertAlmostEqual(moved["origin"][1], 1.0, places=4)
        self.assertAlmostEqual(moved["u"][1], 4.0, places=4)        # a direction only turns

    def test_the_print_stance_render_shows_the_art_in_its_recess(self):
        out = self.render("part_box.step.py", "-90,90")
        with Image.open(out / "az-90_el90.png") as image:
            red, green, blue = image.convert("RGB").getpixel((150, 150))
        self.assertGreater(red, 200)
        self.assertLess(green, 40)
        self.assertLess(blue, 40)

    def test_the_display_pose_render_moves_the_art_with_the_part(self):
        make_round = runpy.run_path(str(MAKE_ROUND))
        posed = self.project / "display_pose_box.step.py"
        posed.write_text(make_round["DISPLAY_POSE_ENTRY"] % {"project": str(self.project),
                                                             "part": "part_box.step.py"})
        out = self.render("display_pose_box.step.py", "-90,90")
        with Image.open(out / "az-90_el90.png") as image:
            red, green, _blue = image.convert("RGB").getpixel((150, 150))
        self.assertGreater(red, 200)
        self.assertLess(green, 40)

    def test_without_an_install_the_render_is_unchanged(self):
        (self.project / "print" / "pieces.json").rename(self.project / "print" / "pieces.off")
        (self.project / "part_box.step.py").write_text(
            "from build123d import *\n\ndef gen_step():\n    return Pos(0, 0, 10) * Box(60, 60, 20)\n")
        out = self.render("part_box.step.py", "-90,90")
        with Image.open(out / "az-90_el90.png") as image:
            red, green, blue = image.convert("RGB").getpixel((150, 150))
        self.assertLess(abs(red - blue), 40)

    def test_an_assembly_entry_draws_no_decal_in_a_part_frame(self):
        (self.project / "assembly.step.py").write_text(PART)
        out = self.render("assembly.step.py", "-90,90")
        with Image.open(out / "az-90_el90.png") as image:
            red, _green, blue = image.convert("RGB").getpixel((150, 150))
        self.assertLess(abs(red - blue), 40)


if __name__ == "__main__":
    unittest.main()
