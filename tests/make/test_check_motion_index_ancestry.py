"""Indexing an assembly must copy geometry, not the tree that owns it."""
from __future__ import annotations

import runpy
import unittest
from pathlib import Path

from build123d import Box, Compound, Location

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"


class IndexAncestryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    @staticmethod
    def leaf(label, center=(0, 0, 0)):
        shape = Box(2, 2, 2).translate(center)
        shape.label = label
        return shape

    def assembly(self, occurrences=6):
        """A root holding one named group per occurrence, each group one leaf."""
        groups = []
        for index in range(occurrences):
            part = self.leaf(f"part_{index}")
            group = Compound(children=[part], label=f"group_{index}")
            group.location = Location((10 * index, 0, 0))
            groups.append(group)
        root = Compound(children=groups, label="product")
        return root, groups

    def test_placed_leaves_keep_their_world_position(self):
        root, _ = self.assembly()
        parts = self.tool["index_parts"](root)
        for index in range(6):
            placed = parts[f"part_{index}"]
            self.assertAlmostEqual(placed.center().X, 10 * index, places=6)

    def test_indexing_leaves_the_source_assembly_attached(self):
        root, groups = self.assembly()
        self.tool["index_parts"](root)
        for group in groups:
            self.assertIs(group.parent, root)
            self.assertEqual([child.label for child in group.children], [group.label.replace("group", "part")])
        self.assertEqual(len(root.children), 6)

    def test_a_placed_copy_does_not_drag_its_siblings_along(self):
        root, _ = self.assembly()
        parts = self.tool["index_parts"](root)
        placed = parts["part_0"]
        self.assertIsNone(placed.parent)
        self.assertEqual(list(getattr(placed, "children", []) or []), [])

    def test_a_named_group_still_copies_with_its_own_children(self):
        root, _ = self.assembly()
        parts = self.tool["index_parts"](root)
        group = parts["group_3"]
        self.assertEqual([child.label for child in group.children], ["part_3"])

    def test_an_unattached_root_is_indexed_unchanged(self):
        lone = self.leaf("solo")
        parts = self.tool["index_parts"](Compound(children=[lone], label="product"))
        self.assertAlmostEqual(parts["solo"].center().X, 0, places=6)


if __name__ == "__main__":
    unittest.main()
