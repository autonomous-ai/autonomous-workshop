"""render_set: build scenes to STEP once, then render each from every camera
through render_review's own cached tessellation -- never a private routine."""
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock

from build123d import Shape


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_set"


class RenderSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = runpy.run_path(str(RENDERER))

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "widget" / "cad"
        self.root.mkdir(parents=True)
        self.render_review = self.module["_load_render_review"]()
        self.calls = 0
        real_tessellate = Shape.tessellate

        def counting_tessellate(shape, *args, **kwargs):
            self.calls += 1
            return real_tessellate(shape, *args, **kwargs)

        patcher = mock.patch.object(Shape, "tessellate", counting_tessellate)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_entry(self, name: str, size: tuple[float, float, float] = (2, 3, 4)) -> Path:
        entry = self.root / f"{name}.step.py"
        entry.write_text(
            "from build123d import Box\n"
            f"def gen_step():\n    return Box{size!r}\n",
            encoding="utf-8",
        )
        return entry

    def test_write_scenes_exports_a_step_entry_and_leaves_an_existing_step_alone(self):
        entry = self.write_entry("opening")
        scenes = self.module["write_scenes"](
            self.render_review, [("opening", entry)], self.root / "scenes"
        )
        self.assertTrue(scenes["opening"].is_file())
        self.assertEqual(scenes["opening"].suffix, ".step")

        already_step = scenes["opening"]
        again = self.module["write_scenes"](
            self.render_review, [("opening", already_step)], self.root / "scenes2"
        )
        self.assertEqual(again["opening"], already_step)
        self.assertFalse((self.root / "scenes2").exists())

    def test_one_scene_rendered_from_two_cameras_tessellates_once(self):
        entry = self.write_entry("opening")
        scenes = self.module["write_scenes"](
            self.render_review, [("opening", entry)], self.root / "scenes"
        )
        views = [self.render_review.parse_view("iso"), self.render_review.parse_view("front")]
        paths = self.module["render_scenes"](
            self.render_review, scenes, views,
            tolerance=0.1, angular=None, size=200, pad=self.render_review.DEFAULT_PAD,
            out_dir=self.root / "out",
        )
        self.assertEqual(len(paths), 2)
        self.assertEqual(self.calls, 1, "two cameras on one scene must tessellate only once")

    def test_unmoved_occurrence_across_two_board_states_is_a_cache_hit(self):
        (self.root / "piece_a.py").write_text(
            "from build123d import Box\ndef piece():\n    return Box(2, 3, 4)\n",
            encoding="utf-8",
        )
        (self.root / "piece_b.py").write_text(
            "from build123d import Box\ndef piece():\n    return Box(5, 6, 7)\n",
            encoding="utf-8",
        )

        opening = self.root / "opening.step.py"
        opening.write_text(
            "from build123d import Compound\n"
            "from piece_a import piece as a\n"
            "from piece_b import piece as b\n"
            "def gen_step():\n    return Compound(children=[a(), b()])\n",
            encoding="utf-8",
        )
        endgame = self.root / "endgame.step.py"
        endgame.write_text(
            "from build123d import Compound\n"
            "from piece_b import piece as b\n"
            "def gen_step():\n    return Compound(children=[b()])\n",
            encoding="utf-8",
        )

        scenes = self.module["write_scenes"](
            self.render_review,
            [("opening", opening), ("endgame", endgame)],
            self.root / "scenes",
        )
        views = [self.render_review.parse_view("iso")]
        self.module["render_scenes"](
            self.render_review, scenes, views,
            tolerance=0.1, angular=None, size=200, pad=self.render_review.DEFAULT_PAD,
            out_dir=self.root / "out",
        )
        self.assertEqual(self.calls, 2, "the opening state tessellates both pieces once each")

        self.calls = 0
        second_scenes = self.module["write_scenes"](
            self.render_review, [("endgame", endgame)], self.root / "scenes"
        )
        self.module["render_scenes"](
            self.render_review, second_scenes, views,
            tolerance=0.1, angular=None, size=200, pad=self.render_review.DEFAULT_PAD,
            out_dir=self.root / "out",
        )
        self.assertEqual(
            self.calls, 0,
            "piece_b is unmoved between board states and must hit the persistent cache",
        )

    def test_angular_tolerance_is_passed_through_and_changes_the_cache_key(self):
        entry = self.write_entry("opening")
        scenes = self.module["write_scenes"](
            self.render_review, [("opening", entry)], self.root / "scenes"
        )
        views = [self.render_review.parse_view("iso")]
        self.module["render_scenes"](
            self.render_review, scenes, views,
            tolerance=0.05, angular=0.1, size=200, pad=self.render_review.DEFAULT_PAD,
            out_dir=self.root / "out",
        )
        self.assertEqual(self.calls, 1)
        self.module["render_scenes"](
            self.render_review, scenes, views,
            tolerance=0.05, angular=0.05, size=200, pad=self.render_review.DEFAULT_PAD,
            out_dir=self.root / "out",
        )
        self.assertEqual(self.calls, 2, "a changed angular tolerance must miss the cache")

    def test_cli_requires_an_explicit_view_and_chooses_no_frame(self):
        entry = self.write_entry("opening")
        with self.assertRaises(SystemExit):
            self.module["main"](
                [str(self.root / "out"), "--scene", f"opening={entry}"]
            )

    def test_self_check(self):
        self.assertEqual(self.module["self_check"](), 0)


if __name__ == "__main__":
    unittest.main()
