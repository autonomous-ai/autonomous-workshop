"""#394: a press check makes each offset once per exact shape.

``CadGeometry.pressed`` keeps each outcome, refusal included, under the
hash of the unplaced shape's exact BREP bytes, the press and the join: an
obstacle shrunk again for a later input reuses the first outcome. Other
bytes, even of the same solid placed elsewhere, are offset anew.

Every press fixture of ``test_kit_tree_press_seat`` reaches the same
verdicts, failures and condition statuses with the cache as without it."""

from __future__ import annotations

import unittest
from unittest import mock

from tests.make import test_kit_tree_press_seat as seat
from tests.make.test_kit_tree import kit_tree


def two_pegs_kit(press=0.05):
    """A base with two sockets, then two pressed pegs: the base is an
    obstacle of both."""

    document = seat.kit(press=press)
    tree = document["assembly_tree"]
    tree["parts"].insert(1, {"id": "A03-post", "name": "Post", "filament": "oak"})
    tree["steps"][0]["inputs"].insert(1, {"id": "A03-post", "direction": [0, 0, -1], "press_mm": press})
    tree["components"][0]["parts"].insert(1, "A03-post")
    return document


def verdicts(report):
    """What a press check decides: its verdicts, failures and every
    condition's status."""

    statuses = [(step["id"], step.get("result", {}).get("status"))
                for sequence in report["conditions"] for step in sequence["inputs"]["steps"]]
    return ([(press["id"], press["verdict"]) for press in report["presses"]],
            sorted(report["failures"]), statuses)


def run(parts, document=None, cached=True, refuse_offset=False, **options):
    """``check_component`` on ``parts``, and how many offsets it made."""

    plan = kit_tree.Plan(document or seat.kit(**options))
    geometry = seat.Built(parts, refuse_offset)
    real = kit_tree.CadGeometry._offset
    with mock.patch.object(kit_tree.CadGeometry, "_offset", side_effect=real) as offset:
        if cached:
            report = kit_tree.check_component(plan, geometry, "block", 0.4)
        else:
            with mock.patch.object(kit_tree, "_brep_digest", side_effect=RuntimeError("uncached")):
                report = kit_tree.check_component(plan, geometry, "block", 0.4)
    return report, offset.call_count


class CachedVerdictsTest(unittest.TestCase):
    def setUp(self):
        try:
            from build123d import Box, Pos
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.Box, self.Pos = Box, Pos
        self.two = seat.PressTwoSidedTest()
        self.two.Box, self.two.Pos = Box, Pos

    def socket(self):
        Box, Pos = self.Box, self.Pos
        return Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)

    def peg(self, size=4.1, across=0.0):
        return self.Pos(across, 0, 10) * self.Box(size, size, 10)

    def fixtures(self):
        two = self.two
        yield "press passes", [("A01-base", self.socket()), ("A02-peg", self.peg())], {"press": 0.05}, False
        yield "shift fails", [("A01-base", self.socket()), ("A02-peg", self.peg(across=0.3))], {"press": 0.05}, False
        yield "deeper fails", [("A01-base", self.socket()), ("A02-peg", self.peg(4.7))], {"press": 0.05}, False
        yield "input refused", [("A01-base", self.socket()), ("A02-peg", self.peg())], {"press": 0.05}, "input"
        yield "whole refused", [("A01-base", self.socket()), ("A02-peg", self.peg())], {"press": 0.05}, "whole"
        for width, bite in ((0.19, 1.0), (0.15, 0.3), (0.25, 0.3), (0.5, 0.1), (0.19, 0.1), (0.3, 0.05)):
            yield ("ribs %s/%s" % (width, bite), [("A01-base", two.base()), ("A02-peg", two.peg(width, bite))],
                   {"press": 0.1}, False)
        for rib in ((0.19, 1.0), (0.19, 0.1)):
            yield "socket rib %s" % (rib,), [("A01-base", two.base(rib=rib)), ("A02-peg", two.peg())], \
                {"press": 0.1}, False

    def test_every_press_fixture_reaches_the_same_verdict_without_the_cache(self):
        for name, parts, options, refuse in self.fixtures():
            with self.subTest(name):
                cached, _ = run(parts, refuse_offset=refuse, **options)
                uncached, _ = run(parts, cached=False, refuse_offset=refuse, **options)
                self.assertEqual(verdicts(cached), verdicts(uncached))

    def two_sockets(self, post_across=0.0):
        Box, Pos = self.Box, self.Pos
        base = self.socket() - Pos(6, 6, 7.5) * Box(4, 4, 5)
        post = Pos(6 + post_across, 6, 10) * Box(4.1, 4.1, 10)
        return [("A01-base", base), ("A03-post", post), ("A02-peg", self.peg())]

    def test_an_obstacle_met_again_is_shrunk_once_with_the_same_verdicts(self):
        for across, verdict in ((0.0, ["PASS", "PASS"]), (0.3, ["FAIL", "PASS"])):
            with self.subTest(across=across):
                cached, made = run(self.two_sockets(across), two_pegs_kit())
                uncached, unmade = run(self.two_sockets(across), two_pegs_kit(), cached=False)
                self.assertEqual(verdicts(cached), verdicts(uncached))
                self.assertEqual([press["verdict"] for press in cached["presses"]], verdict)
                if across == 0.0:
                    # the base, shrunk for the post, is shrunk again for the peg
                    self.assertLess(made, unmade)


class OffsetCacheTest(unittest.TestCase):
    def setUp(self):
        try:
            from build123d import Box, Pos
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.Box, self.Pos = Box, Pos

    def test_an_obstacle_met_again_is_offset_once(self):
        Box, Pos = self.Box, self.Pos
        geometry = kit_tree.CadGeometry.__new__(kit_tree.CadGeometry)
        # one placed solid shrunk for two inputs, as an obstacle met again
        box = Pos(30, 0, 0) * Box(4, 4, 4)
        first = kit_tree.Body("A", box, key="A#1")
        again = kit_tree.Body("A", box, key="A#1")
        real = kit_tree.CadGeometry._offset
        with mock.patch.object(kit_tree.CadGeometry, "_offset", side_effect=real) as offset:
            (one,), _ = geometry.pressed([first], 0.1)
            (two,), _ = geometry.pressed([again], 0.1)
            geometry.pressed([again], 0.2)
            # other bytes, even the same solid moved there and back, are offset anew
            geometry.pressed([kit_tree.Body("A", box.moved(Pos(1, 0, 0)).moved(Pos(-1, 0, 0)), key="A#1")], 0.1)
        self.assertEqual(offset.call_count, 3)
        self.assertAlmostEqual(one.shape.volume, 3.8 ** 3, places=4)
        self.assertAlmostEqual(two.shape.volume, one.shape.volume, places=9)
        self.assertAlmostEqual(two.shape.center().X, 30, places=6)

    def test_a_refusal_is_kept_under_each_bodys_own_name(self):
        geometry = kit_tree.CadGeometry.__new__(kit_tree.CadGeometry)
        box = self.Pos(9, 0, 0) * self.Box(4, 4, 4)
        with mock.patch.object(kit_tree.CadGeometry, "_offset",
                               return_value=(None, "the offset of %s is no valid smaller solid", False)) as offset:
            self.assertEqual(geometry.pressed([kit_tree.Body("A", box, key="A#1")], 0.1),
                             (None, "the offset of A#1 is no valid smaller solid"))
            self.assertEqual(geometry.pressed([kit_tree.Body("A", box, key="A#2")], 0.1),
                             (None, "the offset of A#2 is no valid smaller solid"))
        self.assertEqual(offset.call_count, 1)

    def test_a_shape_it_cannot_write_is_offset_every_time(self):
        geometry = kit_tree.CadGeometry.__new__(kit_tree.CadGeometry)
        body = kit_tree.Body("A", self.Box(4, 4, 4), key="A#1")
        real = kit_tree.CadGeometry._offset
        with mock.patch.object(kit_tree, "_brep_digest", side_effect=RuntimeError("no bytes")), \
                mock.patch.object(kit_tree.CadGeometry, "_offset", side_effect=real) as offset:
            first, _ = geometry.pressed([body], 0.1)
            second, _ = geometry.pressed([body], 0.1)
        self.assertEqual(offset.call_count, 2)
        self.assertAlmostEqual(first[0].shape.volume, second[0].shape.volume, places=9)

    def test_a_kernel_error_text_is_kept_whole(self):
        outcome = kit_tree.CadGeometry._offset(object(), 0.1, False, mock.Mock(),
                                               mock.Mock(side_effect=RuntimeError("50% done")))
        self.assertEqual(outcome[1] % "A#1", "the kernel refuses to offset A#1: 50% done")


if __name__ == "__main__":
    unittest.main()
