from __future__ import annotations

import struct
import unittest

from workshop.make.cad.fe_parts import (
    FePartsError,
    PosedOccurrence,
    fe_part_groups,
    key_parts,
    mesh_signature,
    own_groups,
    part_shapes,
    read_stl_triangles,
    signature_distance,
    slide_key,
)


def cube(size=1.0, at=(0.0, 0.0, 0.0), flip=False):
    """Twelve outward-facing triangles of an axis-aligned cube."""

    x, y, z = at
    p = lambda i, j, k: (x + i * size, y + j * size, z + k * size)  # noqa: E731
    faces = []

    def quad(a, b, c, d):
        faces.append((a, b, c))
        faces.append((a, c, d))

    quad(p(0, 0, 0), p(0, 1, 0), p(1, 1, 0), p(1, 0, 0))
    quad(p(0, 0, 1), p(1, 0, 1), p(1, 1, 1), p(0, 1, 1))
    quad(p(0, 0, 0), p(1, 0, 0), p(1, 0, 1), p(0, 0, 1))
    quad(p(0, 1, 0), p(0, 1, 1), p(1, 1, 1), p(1, 1, 0))
    quad(p(0, 0, 0), p(0, 0, 1), p(0, 1, 1), p(0, 1, 0))
    quad(p(1, 0, 0), p(1, 1, 0), p(1, 1, 1), p(1, 0, 1))
    if flip:
        faces = [(a, c, b) for a, b, c in faces]
    return faces


def binary_stl(triangles):
    out = bytearray(b"\0" * 80 + struct.pack("<I", len(triangles)))
    for a, b, c in triangles:
        out += struct.pack("<3f", 0.0, 0.0, 0.0)
        for vertex in (a, b, c):
            out += struct.pack("<3f", *vertex)
        out += b"\0\0"
    return bytes(out)


def posed(name, triangles):
    points = tuple(vertex for triangle in triangles for vertex in triangle)
    lo = tuple(min(p[i] for p in points) for i in range(3))
    hi = tuple(max(p[i] for p in points) for i in range(3))
    return PosedOccurrence(name=name, bbox_min=lo, bbox_max=hi, points=points)


class FePartGroupsTest(unittest.TestCase):
    def test_separate_and_touching_solids_split_like_the_viewer(self):
        apart = cube(1.0) + cube(1.0, at=(5.0, 0.0, 0.0))
        touching = cube(1.0) + cube(1.0, at=(1.0, 0.0, 0.0))

        self.assertEqual(fe_part_groups(apart).count, 2)
        groups = fe_part_groups(touching)
        # The shared square is triangulated identically by both cubes, so all
        # of its edges carry four triangles: its four facets are loose and take
        # their bodies' numbers, exactly as the viewer colours them.
        self.assertEqual(groups.count, 2)
        self.assertEqual(groups.loose_shells, 4)
        self.assertEqual([group.triangles for group in groups.groups], [12, 12])
        self.assertEqual(groups.groups[1].centroid[0] > groups.groups[0].centroid[0], True)

    def test_a_loose_facet_takes_its_owners_number(self):
        solid = cube(2.0)
        facet = [((5.0, 5.0, 5.0), (6.0, 5.0, 5.0), (5.0, 6.0, 5.0))]

        groups = fe_part_groups(solid + facet)

        self.assertEqual(groups.shells, 2)
        self.assertEqual(groups.loose_shells, 1)
        self.assertEqual(groups.count, 1)
        self.assertEqual(groups.groups[0].triangles, 13)

    def test_binary_and_ascii_stl_read_in_file_order(self):
        triangles = cube(1.0)
        self.assertEqual(read_stl_triangles(binary_stl(triangles))[0][1], triangles[0][1])
        ascii_stl = b"solid t\n" + b"".join(
            b" facet normal 0 0 0\n  outer loop\n"
            + b"".join(b"   vertex %r %r %r\n" % v for v in tri)
            + b"  endloop\n endfacet\n"
            for tri in triangles
        ) + b"endsolid t\n"
        self.assertEqual(len(read_stl_triangles(ascii_stl)), 12)
        with self.assertRaises(FePartsError):
            read_stl_triangles(b"nonsense")
        with self.assertRaises(FePartsError):
            fe_part_groups([])

    def test_signature_is_pose_invariant_and_shape_specific(self):
        a = mesh_signature(cube(2.0))
        b = mesh_signature(cube(2.0, at=(10.0, -3.0, 7.0)))
        rotated = mesh_signature([tuple((v[1], v[2], v[0]) for v in tri) for tri in cube(2.0)])
        other = mesh_signature(cube(3.0))

        self.assertLess(signature_distance(a, b), 1e-6)
        self.assertLess(signature_distance(a, rotated), 1e-6)
        self.assertGreater(signature_distance(a, other), 0.5)


class OwnershipTest(unittest.TestCase):
    def test_signature_anchors_ownership_and_position_tells_instances_apart(self):
        big = cube(2.0, at=(0.0, 0.0, 0.0))
        small_a = cube(1.0, at=(10.0, 0.0, 0.0))
        small_b = cube(1.0, at=(20.0, 0.0, 0.0))
        assembled = binary_stl(big + small_a + small_b)
        # The posed extent of "frame" is wrong on purpose: shape identity must win.
        occurrences = [
            PosedOccurrence(name="frame", bbox_min=(0.0, 0.0, 0.0), bbox_max=(0.1, 0.1, 0.1), points=((0.05, 0.05, 0.05),)),
            posed("wheel_1", small_a),
            posed("wheel_2", small_b),
        ]
        meshes = {
            "frame": binary_stl(cube(2.0, at=(-50.0, 9.0, 3.0))),
            "wheel_1": binary_stl(cube(1.0, at=(40.0, 40.0, 40.0))),
            "wheel_2": binary_stl(cube(1.0, at=(40.0, 40.0, 40.0))),
        }

        keying = key_parts(
            assembled,
            occurrences,
            slide_order=["frame", "wheel_1", "wheel_2"],
            colours={"frame": "#2b2b2b", "wheel_1": "#8b2323", "wheel_2": "#8b2323"},
            part_meshes=meshes,
        )

        self.assertTrue(keying.complete)
        self.assertEqual(
            [(key.order, key.part, key.owner, key.color) for key in keying.keys],
            [
                (0, "frame.stl", "frame", "#2b2b2b"),
                (1, "wheel_1.stl", "wheel_1", "#8b2323"),
                (2, "wheel_2.stl", "wheel_2", "#8b2323"),
            ],
        )

    def test_split_pieces_follow_their_part_and_slot_keys_past_the_slides(self):
        body = cube(2.0)
        piece = cube(0.4, at=(2.0, 0.8, 0.8))   # touches the body: a second shell
        far = cube(1.0, at=(30.0, 0.0, 0.0))
        assembled = binary_stl(body + piece + far)
        occurrences = [posed("tank", body + piece), posed("bar", far)]
        meshes = {"tank": binary_stl(body + piece), "bar": binary_stl(far)}

        keying = key_parts(
            assembled, occurrences, slide_order=["tank", "bar"], part_meshes=meshes,
            colours={"tank": "#1f1f1f", "bar": "#2b2b2b"},
        )

        self.assertTrue(keying.complete)
        self.assertEqual(keying.groups.count, 3)
        self.assertEqual([key.owner for key in keying.keys], ["tank", "tank", "bar"])
        self.assertEqual([key.part for key in keying.keys], ["tank.stl", "bar.stl", "assembled.stl#2"])
        self.assertEqual(keying.keys[2].color, "#2b2b2b")

    def test_a_sliver_only_part_keeps_its_sliver(self):
        body = cube(2.0)
        sliver = [((3.0, 0.0, 0.0), (3.2, 0.0, 0.0), (3.0, 0.2, 0.0)), ((3.0, 0.0, 0.0), (3.0, 0.2, 0.0), (3.2, 0.0, 0.0))]
        occurrences = [posed("body", body), posed("keeper", sliver)]

        keying = key_parts(
            binary_stl(body + sliver), occurrences, slide_order=["body", "keeper"],
            part_meshes={"body": binary_stl(body), "keeper": binary_stl(sliver)},
        )

        self.assertTrue(keying.complete)
        self.assertEqual([key.owner for key in keying.keys], ["body", "keeper"])
        self.assertEqual(keying.keys[1].mesh_name, "keeper_sliver")

    def test_an_occurrence_without_any_group_is_reported(self):
        body = cube(2.0)
        occurrences = [posed("body", body), posed("ghost", cube(1.0, at=(50.0, 50.0, 50.0)))]

        keying = key_parts(binary_stl(body), occurrences, slide_order=["body", "ghost"])

        self.assertFalse(keying.complete)
        self.assertEqual(keying.unowned_occurrences, ("ghost",))

    def test_slot_keys_and_helpers(self):
        self.assertEqual(slide_key("assembled.stl", ["a.stl"], 0, 3), "a.stl")
        self.assertEqual(slide_key("assembled.stl", [], 0, 1), "assembled.stl")
        self.assertEqual(slide_key("assembled.stl", [], 0, 2), "assembled.stl#0")
        self.assertEqual(slide_key("assembled.stl", ["a.stl"], 1, 2), "assembled.stl#1")
        shapes = part_shapes({"tank": binary_stl(cube(2.0) + cube(0.4, at=(2.0, 0.8, 0.8)))})
        self.assertEqual(len(shapes["tank"].shells), 2)
        with self.assertRaises(FePartsError):
            own_groups(fe_part_groups(cube(1.0)), [posed("a", cube(1.0)), posed("a", cube(1.0))])
        self.assertEqual(own_groups(fe_part_groups(cube(1.0)), []), (None,))


if __name__ == "__main__":
    unittest.main()
