"""Selected CAD copies preserve geometry without copying assembly ancestors."""

from collections import Counter
from contextlib import contextmanager
from pathlib import Path
import runpy
import math
import unittest
from unittest import mock

from build123d import Color, Compound, Location, Pos, Shape, Solid


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
COPY = runpy.run_path(str(SCRIPTS / "assembly_copy.py"))["placed_subtree_copy"]


def assembly(siblings=0):
    leaf = Solid.make_box(1, 2, 3)
    leaf.label = "moving"
    leaf.color = Color("red")
    leaf.location = Location((3, 5, 1), (0, 0, 15))
    neighbours = []
    for index in range(siblings):
        neighbour = Solid.make_box(1, 1, 1)
        neighbour.label = f"sibling_{index}"
        neighbour.location = Location((10 + 3 * index, 0, 0))
        neighbours.append(neighbour)
    group = Compound(children=[leaf, *neighbours], label="group")
    group.color = Color("blue")
    group.location = Location((7, -4, 2), (0, 0, 30))
    root = Compound(children=[group], label="root")
    root.location = Location((100, 20, 5), (10, 0, 0))
    return root, group, leaf


def source_state(root):
    return [
        (id(node), id(node.parent), tuple(map(id, node.children)),
         node.location, node.global_location, node.label, colour_tuple(node))
        for node in [root, *root.descendants]
    ]


def colour_tuple(node):
    return None if node._color is None else tuple(node._color)


def inherited_colour_tuple(node):
    while node is not None:
        if node._color is not None:
            return tuple(node._color)
        node = node.parent
    return None


def geometry(shape):
    box = shape.bounding_box()
    vertices = sorted(tuple(vertex.center()) for vertex in shape.vertices())
    return [
        *box.min, *box.max,
        sum(solid.volume for solid in shape.solids()),
        *[coordinate for vertex in vertices for coordinate in vertex],
    ]


def assert_geometry_matches(actual, expected):
    first, second = geometry(actual), geometry(expected)
    assert len(first) == len(second)
    assert all(math.isclose(a, b, rel_tol=0, abs_tol=1e-8) for a, b in zip(first, second)), (first, second)


@contextmanager
def copied_shapes():
    copied = Counter()
    original = Shape.__deepcopy__

    def tracked(shape, memo):
        copied[shape.label] += 1
        return original(shape, memo)

    with mock.patch.object(Shape, "__deepcopy__", tracked):
        yield copied


def check_copy_matches_world_geometry_and_preserves_subtree_metadata(selection):
    root, group, leaf = assembly(2)
    selected = {"root": root, "group": group, "moving": leaf}[selection]
    before = source_state(root)
    expected = selected.located(selected.global_location)
    with copied_shapes() as copied:
        actual = COPY(selected, selected.global_location)
    assert_geometry_matches(actual, expected)
    assert actual.location == selected.global_location
    assert actual.parent is None
    original_nodes = [selected, *selected.descendants]
    actual_nodes = [actual, *actual.descendants]
    assert sum(copied.values()) == len(original_nodes)
    assert len(actual_nodes) == len(original_nodes)
    for original, clone in zip(original_nodes, actual_nodes):
        assert clone is not original
        assert clone.label == original.label
        actual_colour = None if clone.color is None else tuple(clone.color)
        assert actual_colour == inherited_colour_tuple(original)
        assert clone.global_location == original.global_location
        if clone is not actual:
            assert clone.parent in actual_nodes
            assert clone.location == original.location
    actual_nodes[-1].label = "changed only in copy"
    actual.translate((1, 2, 3))
    assert source_state(root) == before


def check_index_copy_work_is_linear_and_leaf_motion_copies_one_shape(tool_name, siblings):
    tool = runpy.run_path(str(SCRIPTS / tool_name))
    root, group, leaf = assembly(siblings)
    before = source_state(root)
    with copied_shapes() as copied:
        parts = tool["index_parts"](root)
    # At this fixed depth, each occurrence can be copied for itself, its group,
    # and the root. Copying the retained parent would instead copy the whole
    # assembly for every occurrence: 9, 49, 361 copies in check_motion.
    assert sum(copied.values()) <= 3 * (siblings + 3)
    assert copied["moving"] <= 3
    moving = parts["moving"]
    assert moving is parts["root.group.moving"]
    assert moving.parent is None
    assert parts["group"] is parts["root.group"]
    assert parts["group"].parent is None
    assert len(parts["group"].children) == siblings + 1
    assert parts["__ambiguous__"] == []
    expected = Solid(leaf.wrapped.Located(leaf.global_location.wrapped))
    for operation in (
        lambda shape: Pos(0, 0, .25) * shape,
        lambda shape: shape.translate((.25, 0, 0)),
    ):
        with copied_shapes() as moved_copies:
            moved = operation(moving)
        assert moved_copies == {"moving": 1}
        assert_geometry_matches(moved, operation(expected))
    if tool_name == "check_motion":
        assert parts["__node_keys__"]["moving"] == (0, 0)
        assert parts["__node_keys__"]["root.group.moving"] == (0, 0)
        assert parts["__node_keys__"]["group"] == (0,)
        assert parts["__toplevel__"] == ["group"]
        key, placed, colour = parts["__leaf_nodes__"][0]
        assert key == (0, 0)
        assert placed is moving
        assert tuple(colour) == tuple(leaf.color)
    assert source_state(root) == before


def check_selected_group_excludes_external_siblings_and_keeps_internal_parents():
    root, group, _leaf = assembly(2)
    outside = Solid.make_box(1, 1, 1)
    outside.label = "outside"
    root.children = [group, outside]
    before = source_state(root)
    with copied_shapes() as copied:
        selected = COPY(group, group.global_location)
        moved = Pos(0, 0, 2) * selected
    assert copied == {"group": 2, "moving": 2, "sibling_0": 2, "sibling_1": 2}
    assert all(child.parent is selected for child in selected.children)
    assert all(child.parent is moved for child in moved.children)
    assert source_state(root) == before


def check_failed_copy_never_detaches_or_relocates_source(testcase):
    class Uncopyable:
        def __deepcopy__(self, memo):
            raise RuntimeError("metadata cannot be copied")

    root, _group, leaf = assembly(2)
    leaf.metadata = Uncopyable()
    before = source_state(root)
    with testcase.assertRaisesRegex(RuntimeError, "metadata cannot be copied"):
        COPY(leaf, Location((999, 999, 999)))
    assert source_state(root) == before


def check_empty_shape_retains_located_failure_without_copying(testcase):
    empty = Solid()
    with copied_shapes() as copied, testcase.assertRaisesRegex(ValueError, "Cannot locate an empty shape"):
        COPY(empty, Location())
    assert not copied


class AssemblyCopyTests(unittest.TestCase):
    def test_world_geometry_and_subtree_metadata(self):
        for selection in ("root", "group", "moving"):
            with self.subTest(selection=selection):
                check_copy_matches_world_geometry_and_preserves_subtree_metadata(selection)

    def test_linear_index_and_constant_leaf_motion_copy_counts(self):
        for tool in ("check_motion", "check_mount"):
            for siblings in (0, 4, 16):
                with self.subTest(tool=tool, siblings=siblings):
                    check_index_copy_work_is_linear_and_leaf_motion_copies_one_shape(tool, siblings)

    def test_group_copy_excludes_siblings(self):
        check_selected_group_excludes_external_siblings_and_keeps_internal_parents()

    def test_copy_failure_keeps_source_tree(self):
        check_failed_copy_never_detaches_or_relocates_source(self)

    def test_empty_copy_keeps_failure(self):
        check_empty_shape_retains_located_failure_without_copying(self)

    def test_inherited_colour_is_preserved_without_populating_source_caches(self):
        for tool_name in ("check_motion", "check_mount"):
            with self.subTest(tool=tool_name):
                root, group, leaf = assembly(2)
                root.color = Color("orange")
                group.color = None
                leaf.color = None
                before = source_state(root)
                direct = COPY(leaf, leaf.global_location)
                self.assertEqual(tuple(direct.color), tuple(root.color))
                self.assertEqual(source_state(root), before)
                parts = runpy.run_path(str(SCRIPTS / tool_name))["index_parts"](root)
                for name in ("moving", "group"):
                    self.assertEqual(tuple(parts[name].color), tuple(root.color))
                if tool_name == "check_motion":
                    for _key, _placed, colour in parts["__leaf_nodes__"]:
                        self.assertEqual(tuple(colour), tuple(root.color))
                self.assertIsNone(group._color)
                self.assertIsNone(leaf._color)
                self.assertEqual(source_state(root), before)


if __name__ == "__main__":
    unittest.main()
