"""Mount gates must measure selected parts in the complete assembly pose."""
from __future__ import annotations

import hashlib
import runpy
import tempfile
import unittest
from pathlib import Path

from build123d import Box, Compound, Location, export_step


CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_mount"


class MountAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    @staticmethod
    def nested_assembly(*, unnamed_wrapper=False):
        wall = Box(2, 4, 6).translate((2, 0, 0))
        wall.label = "wall"
        if unnamed_wrapper:
            wall = Compound(children=[wall])
            wall.location = Location((0, 3, 0))
        module = Compound(children=[wall], label="module")
        module.location = Location((10, 0, 0), (0, 0, 90))
        root = Compound(children=[module], label="root")
        root.location = Location((0, 20, 0), (90, 0, 0))
        return root

    def test_named_leaves_and_groups_match_whole_assembly_measurements(self):
        model = self.nested_assembly()
        parts = self.tool["index_parts"](model)
        # Local (2,0,0) -> module (10,2,0) -> world (10,20,2).
        # Rz(90) then Rx(90) maps the box's (2,4,6) extents to (4,6,2).
        world_probe = Box(4, 6, 2).translate((10, 20, 2))
        gap_probe = Box(2, 2, 2).translate((13.2, 20, 2))
        local_probe = Box(2, 4, 6).translate((2, 0, 0))
        for names in (None, ["wall"], ["module"], ["root.module.wall"], ["root.module"]):
            with self.subTest(parts=names):
                obstacles = self.tool["obstacle_solids"](model, parts, names)
                self.assertAlmostEqual(self.tool["clash_volume"](world_probe, obstacles), 48)
                self.assertAlmostEqual(self.tool["nearest_gap"](gap_probe, obstacles, 4), .2)
                self.assertEqual(self.tool["clash_volume"](local_probe, obstacles), 0)

    def test_unnamed_intermediate_wrapper_contributes_its_location(self):
        model = self.nested_assembly(unnamed_wrapper=True)
        parts = self.tool["index_parts"](model)
        # The wrapper adds local Y=3, which becomes world X=-3.
        expected = Box(4, 6, 2).translate((7, 20, 2))
        for name in ("wall", "module", "root.module.wall", "root.module"):
            with self.subTest(part=name):
                obstacles = self.tool["obstacle_solids"](model, parts, [name])
                self.assertAlmostEqual(self.tool["clash_volume"](expected, obstacles), 48)

    def test_indexing_keeps_source_locations_and_parent_relationships(self):
        model = self.nested_assembly()
        nodes = [model, *model.descendants]
        before = [
            (node.location, id(node.parent), tuple(map(id, node.children)))
            for node in nodes
        ]
        first = self.tool["index_parts"](model)
        second = self.tool["index_parts"](model)
        after = [
            (node.location, id(node.parent), tuple(map(id, node.children)))
            for node in nodes
        ]
        self.assertEqual(before, after)
        self.assertIsNot(first["wall"], model.descendants[-1])
        self.assertEqual(first["wall"].location, second["wall"].location)

    def test_repeated_labels_still_require_unique_dotted_paths(self):
        left = Box(2, 2, 2)
        left.label = "wall"
        right = Box(2, 2, 2)
        right.label = "wall"
        left_module = Compound(children=[left], label="left")
        left_module.location = Location((-10, 0, 0))
        right_module = Compound(children=[right], label="right")
        right_module.location = Location((10, 0, 0))
        model = Compound(children=[left_module, right_module], label="root")
        parts = self.tool["index_parts"](model)
        with self.assertRaisesRegex(self.tool["ManifestError"], "ambiguous"):
            self.tool["obstacle_solids"](model, parts, ["wall"])
        for name, x in (("root.left.wall", -10), ("root.right.wall", 10)):
            with self.subTest(part=name):
                obstacles = self.tool["obstacle_solids"](model, parts, [name])
                self.assertAlmostEqual(
                    self.tool["clash_volume"](Box(2, 2, 2).translate((x, 0, 0)), obstacles), 8
                )

    def test_mount_gate_preserves_clash_and_clearance_failures_in_world_pose(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            component = project / "component.step"
            export_step(Box(2, 2, 2), component)
            checksum = hashlib.sha256(component.read_bytes()).hexdigest()
            model = self.nested_assembly()
            parts = self.tool["index_parts"](model)
            cases = (
                ("clash", 10, 0, ["seat-clash"], 8, None),
                ("clear", 13.2, .1, [], 0, .2),
                ("tight", 13.05, .1, ["seat-clearance"], 0, .05),
                ("contact", 13, 0, [], 0, 0),
            )
            for name, x, floor, rules, clash, gap in cases:
                for selection in (None, ["wall"], ["module"], ["root.module.wall"]):
                    with self.subTest(case=name, parts=selection):
                        spec = {
                            "id": name, "component": component.name,
                            "sha256": checksum, "at": [x, 20, 2],
                            "min_clearance": floor, "bolts": False,
                        }
                        if selection is not None:
                            spec["parts"] = selection
                        measured = {}
                        findings = self.tool["run_mount"](spec, project, model, parts, 0, measured)
                        self.assertEqual([finding["rule"] for finding in findings], rules)
                        self.assertAlmostEqual(measured["clash_mm3"], clash)
                        if gap is None:
                            self.assertNotIn("clearance_mm", measured)
                        else:
                            self.assertAlmostEqual(measured["clearance_mm"], gap)


if __name__ == "__main__":
    unittest.main()
