"""The printed-only primary a direct publication ships to Factory."""

import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.make.cad.step_color import read_step_part_colors
from workshop.release.printed_primary import printed_only_primary, scene_bodies


def step(children, *, single=False):
    """A real STEP: each child is (label, hex colour or None, shape)."""

    from build123d import Color, Compound, export_step

    parts = []
    for label, colour, shape in children:
        shape.label = label
        if colour is not None:
            shape.color = Color(*(int(colour[i:i + 2], 16) / 255.0 for i in (1, 3, 5)))
        parts.append(shape)
    shape = parts[0] if single else Compound(label="scene", children=parts)
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "scene.step"
        export_step(shape, str(path))
        return path.read_bytes()


def base():
    from build123d import Box
    return Box(40, 30, 6)


def post():
    from build123d import Cylinder
    return Cylinder(6, 50)


def rod():
    from build123d import Cylinder
    return Cylinder(3, 60)


def nut():
    from build123d import Box, Cylinder
    return Cylinder(5, 5) - Cylinder(3, 5)


def placed(shape, x):
    from build123d import Pos, Rot
    return Pos(x, 10, 3) * Rot(0, 0, 37) * shape


class PrintedPrimaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.printed = {
            "part_base.step": step([("base", "#5a3a22", base())], single=True),
            "part_post.step": step([("post", "#1a1a1a", post())], single=True),
        }
        cls.scene = step([
            ("base", "#5a3a22", placed(base(), 0)),
            ("post", "#1a1a1a", placed(post(), 50)),
            ("rod_m6", "#9aa0a6", placed(rod(), 100)),
            ("nut_top", "#9aa0a6", placed(nut(), 150)),
            ("nut_bottom", "#9aa0a6", placed(nut(), 200)),
        ])

    def test_an_undeclared_body_is_refused_and_named(self):
        with self.assertRaises(ContractError) as caught:
            printed_only_primary(self.scene, self.printed)
        message = str(caught.exception)
        for name in ("rod_m6", "nut_top", "nut_bottom"):
            self.assertIn(name, message)
        self.assertNotIn("base,", message)
        self.assertIn("--display-only", message)

    def test_a_partly_declared_scene_is_still_refused(self):
        with self.assertRaisesRegex(ContractError, "nut_bottom, nut_top"):
            printed_only_primary(self.scene, self.printed, declared=["rod_m6"])

    def test_declared_bodies_are_stripped_and_printed_ones_kept_with_colours(self):
        result = printed_only_primary(
            self.scene, self.printed, declared=["rod_m6", "nut_top", "nut_bottom"]
        )
        self.assertEqual(result.stripped, ("rod_m6", "nut_top", "nut_bottom"))
        self.assertEqual(result.kept, ("base", "post"))
        bodies = scene_bodies(result.content)
        self.assertEqual([body.name for body in bodies], ["base", "post"])
        self.assertTrue(result.content.startswith(b"ISO-10303-21"))
        colours = {name: colour.hex for name, colour in read_step_part_colors(result.content).items()}
        self.assertEqual(colours, {"base": "#5a3a22", "post": "#1a1a1a"})

    def test_a_group_emptied_by_stripping_leaves_no_empty_body(self):
        # A powered Workshop toy keeps its bought bodies in one `bought` group
        # (ADR 0095); stripping them all must not leave the group behind.
        from build123d import Color, Compound, export_step

        def labelled(label, colour, shape):
            shape.label = label
            shape.color = Color(*(int(colour[i:i + 2], 16) / 255.0 for i in (1, 3, 5)))
            return shape

        scene = Compound(label="scene", children=[
            labelled("base", "#5a3a22", placed(base(), 0)),
            labelled("post", "#1a1a1a", placed(post(), 50)),
            Compound(label="bought", children=[
                labelled("bought_rod", "#ff00ff", placed(rod(), 100)),
                labelled("bought_nut", "#ff00ff", placed(nut(), 150)),
            ]),
        ])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "scene.step"
            export_step(scene, str(path))
            primary = path.read_bytes()
        result = printed_only_primary(primary, self.printed, declared=["bought_rod", "bought_nut"])
        self.assertEqual(sorted(body.name for body in scene_bodies(result.content)), ["base", "post"])
        self.assertEqual(sorted(result.stripped), ["bought_nut", "bought_rod"])

    def test_a_fully_printed_primary_keeps_its_exact_bytes(self):
        scene = step([("base", None, placed(base(), 0)), ("post", None, placed(post(), 50))])
        result = printed_only_primary(scene, self.printed)
        self.assertIs(result.content, scene)
        self.assertEqual(result.stripped, ())

    def test_a_declaration_naming_a_printed_body_is_refused(self):
        with self.assertRaisesRegex(ContractError, "post is declared not printed but matches"):
            printed_only_primary(
                self.scene, self.printed, declared=["rod_m6", "nut_top", "nut_bottom", "post"]
            )

    def test_a_declaration_naming_no_body_is_refused(self):
        with self.assertRaisesRegex(ContractError, "washer .*has no body of that name"):
            printed_only_primary(
                self.scene, self.printed,
                declared=["rod_m6", "nut_top", "nut_bottom", "washer"],
            )

    def test_a_scene_part_that_differs_from_its_printed_entry_is_not_printed(self):
        from build123d import Box
        scene = step([("base", None, placed(Box(40, 30, 7), 0)), ("post", None, placed(post(), 50))])
        with self.assertRaisesRegex(ContractError, "would bill them as filament: base"):
            printed_only_primary(scene, self.printed)

    def test_a_part_written_as_a_closed_shell_still_counts_as_printed(self):
        from build123d import Shell
        printed = {
            "part_base.step": step([("base", None, Shell(base().faces()))], single=True),
            "part_post.step": self.printed["part_post.step"],
        }
        self.assertEqual(scene_bodies(printed["part_base.step"])[0].solids, ())
        result = printed_only_primary(
            self.scene, printed, declared=["rod_m6", "nut_top", "nut_bottom"]
        )
        self.assertEqual(result.kept, ("base", "post"))

    def test_stripping_every_body_is_refused(self):
        scene = step([("rod_m6", None, placed(rod(), 0)), ("nut_top", None, placed(nut(), 50))])
        with self.assertRaisesRegex(ContractError, "no printed body remains"):
            printed_only_primary(scene, self.printed, declared=["rod_m6", "nut_top"])


if __name__ == "__main__":
    unittest.main()
