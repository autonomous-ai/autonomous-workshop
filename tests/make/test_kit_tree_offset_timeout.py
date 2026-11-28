"""#396: the wall clock never picks a kit tree verdict.

An obstacle's sharp join that runs out of ``PRESS_OFFSET_SECONDS`` is
replaced by the arc join, which holds more material. A press that passes
through it passes; one that fails through it is UNVERIFIED (a rerun), never
a FAIL, and the outcome kept for a later Part sharing the obstacle carries
the same mark. Kyoto's Gion Canal gave PASS, FAIL, PASS on the same bytes.

The fixture: a 4.1 mm square peg pressed 0.05 mm into a 4 mm square socket.
The sharp join keeps the socket's corners square, so it passes; the arc
join rounds them, and the peg's corners bite: FAIL."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tests.make import test_kit_tree_press_seat as seat
from tests.make import test_kit_tree_press_speedups as speedups
from tests.make.test_kit_tree import kit_tree


def timed_out(*_args, **_kwargs):
    raise kit_tree.OffsetInterrupted("the kernel's offset did not finish (signal 14)")


def crashed(*_args, **_kwargs):
    raise RuntimeError("the kernel's offset failed (child status 134)")


class OffsetTimeoutVerdictTest(unittest.TestCase):
    def setUp(self):
        try:
            from build123d import Box, Pos
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.Box, self.Pos = Box, Pos

    def parts(self, size=4.1, across=0.0):
        Box, Pos = self.Box, self.Pos
        socket = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)
        return [("A01-base", socket), ("A02-peg", Pos(across, 0, 10) * Box(size, size, 10))]

    def check(self, parts, sharp=None):
        """The component check with the sharp join as given: None runs it."""

        if sharp is None:
            report = seat.check(parts, press=0.05)
        else:
            with mock.patch.object(kit_tree, "_isolated_offset", side_effect=sharp) as join:
                report = seat.check(parts, press=0.05)
            self.assertGreater(join.call_count, 0)
        return kit_tree.summarise(report)

    def test_the_sharp_join_passes_and_the_arc_join_alone_fails(self):
        # The fixture is the two ways the old 120 s cutoff chose between.
        self.assertEqual(self.check(self.parts())["verdict"], "PASS")
        crash = self.check(self.parts(), crashed)
        self.assertEqual(crash["verdict"], "FAIL")
        self.assertEqual(crash["unverified"], [])

    def test_a_timed_out_sharp_join_is_unverified_not_a_failure(self):
        report = self.check(self.parts(), timed_out)
        self.assertEqual(report["verdict"], "UNVERIFIED")
        self.assertEqual(report["failures"], [])
        (entry,) = report["unverified"]
        self.assertIn("bites deeper than its press", entry)
        self.assertIn("ran out of %ds; rerun" % kit_tree.PRESS_OFFSET_SECONDS, entry)
        (press,) = report["presses"]
        self.assertEqual((press["verdict"], press["offset_timeouts"]), ("UNVERIFIED", 1))

    def test_a_press_that_passes_through_the_arc_join_passes(self):
        # The arc join holds more material: through it a pass is a pass.
        report = self.check(self.parts(size=4.06), timed_out)
        self.assertEqual(report["verdict"], "PASS", report["unverified"])
        self.assertEqual(report["presses"][0]["verdict"], "PASS")

    def test_a_failure_that_reads_no_obstacle_offset_stays_a_failure(self):
        # Shifted 0.3 mm, the shrunk peg already hits the real socket: its
        # first sweep reads no obstacle offset, so the timeout decides nothing.
        report = self.check(self.parts(across=0.3), timed_out)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["unverified"], [])
        self.assertEqual(self.check(self.parts(across=0.3))["failures"], report["failures"])

    def test_a_failure_stands_beside_an_undecided_press(self):
        report = kit_tree.summarise({"defects": [], "failures": ["S01: a real failure"],
                                     "unverified": ["S02: not decided"]})
        self.assertEqual(report["verdict"], "FAIL")

    def test_a_cached_timeout_is_never_a_refusal_for_a_later_part(self):
        # The base is an obstacle of the post and then of the peg (#394): the
        # timed-out outcome kept for it marks the peg's press too.
        Box, Pos = self.Box, self.Pos
        base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5) - Pos(6, 6, 7.5) * Box(4, 4, 5)
        parts = [("A01-base", base), ("A03-post", Pos(6, 6, 10) * Box(4.1, 4.1, 10)),
                 ("A02-peg", Pos(0, 0, 10) * Box(4.1, 4.1, 10))]
        plan = kit_tree.Plan(speedups.two_pegs_kit())
        real = kit_tree.summarise(kit_tree.check_component(plan, seat.Built(parts), "block", 0.4))
        self.assertEqual([press["verdict"] for press in real["presses"]], ["PASS", "PASS"])
        with mock.patch.object(kit_tree, "_isolated_offset", side_effect=timed_out) as join:
            report = kit_tree.summarise(kit_tree.check_component(plan, seat.Built(parts), "block", 0.4))
        self.assertEqual(report["failures"], [])
        self.assertEqual([press["verdict"] for press in report["presses"]], ["UNVERIFIED", "UNVERIFIED"])
        self.assertEqual(report["verdict"], "UNVERIFIED")
        self.assertEqual(len(report["unverified"]), 2)
        # the base's shape was tried once; the later input reused the mark
        digests = {kit_tree._brep_digest(call.args[0]) for call in join.call_args_list}
        self.assertEqual(len(digests), join.call_count)

    def test_a_kept_timeout_is_marked_at_every_use(self):
        geometry = kit_tree.CadGeometry.__new__(kit_tree.CadGeometry)
        body = kit_tree.Body("A", self.Pos(9, 0, 0) * self.Box(4, 4, 4), key="A#1")
        with mock.patch.object(kit_tree, "_isolated_offset", side_effect=timed_out) as join:
            first, error = geometry.pressed([body], 0.1, sharp=True)
            second, again = geometry.pressed([body], 0.1, sharp=True)
        self.assertIsNone(error)
        self.assertIsNone(again)
        self.assertEqual(join.call_count, 1)
        self.assertEqual(geometry.offset_timeouts, 2)
        self.assertAlmostEqual(first[0].shape.volume, second[0].shape.volume, places=9)

    def test_a_crashed_sharp_join_is_no_timeout(self):
        geometry = kit_tree.CadGeometry.__new__(kit_tree.CadGeometry)
        body = kit_tree.Body("A", self.Box(4, 4, 4), key="A#1")
        with mock.patch.object(kit_tree, "_isolated_offset", side_effect=crashed):
            geometry.pressed([body], 0.1, sharp=True)
        self.assertEqual(getattr(geometry, "offset_timeouts", 0), 0)


class IsolatedOffsetTest(unittest.TestCase):
    """The forked child's end decides which exception the caller sees."""

    def setUp(self):
        try:
            import build123d
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.build123d = build123d

    def test_an_alarm_is_an_interruption(self):
        import time

        real = self.build123d.offset

        def stalling(shape, *args, **kwargs):
            time.sleep(60)
            return real(shape, *args, **kwargs)

        with mock.patch.object(self.build123d, "offset", side_effect=stalling), \
                mock.patch.dict(kit_tree._isolated_offset.__globals__, {"PRESS_OFFSET_SECONDS": 1}):
            with self.assertRaises(kit_tree.OffsetInterrupted):
                kit_tree._isolated_offset(self.build123d.Box(4, 4, 4), 0.1, self.build123d.Kind.INTERSECTION)

    def test_a_crash_is_a_refusal_not_an_interruption(self):
        import os

        with mock.patch.object(self.build123d, "offset", side_effect=lambda *a, **k: os.abort()):
            with self.assertRaises(RuntimeError) as raised:
                kit_tree._isolated_offset(self.build123d.Box(4, 4, 4), 0.1, self.build123d.Kind.INTERSECTION)
        self.assertNotIsInstance(raised.exception, kit_tree.OffsetInterrupted)


class UnverifiedReportTest(unittest.TestCase):
    def report(self, **extra):
        base = {"scope": "component:block", "defects": [], "failures": [], "unverified": [],
                "conditions": [], "routes": [], "kind": kit_tree.REPORT_KIND, "tree_sha256": "0" * 64}
        base.update(extra)
        return kit_tree.summarise(base)

    def run_main(self, report):
        out = io.StringIO()
        with mock.patch.object(kit_tree, "run", return_value=report), redirect_stdout(out):
            code = kit_tree.main(["proj", "--component", "block", "--json"])
        return code, out.getvalue()

    def test_an_undecided_tree_exits_4_and_says_so(self):
        code, out = self.run_main(self.report(unverified=["S01: A02-peg#1 ... (not decided ...; rerun)"]))
        self.assertEqual(code, kit_tree.EXIT_UNVERIFIED)
        self.assertEqual(code, 4)
        first = out.splitlines()[0]
        self.assertIn(": UNVERIFIED,", first)
        self.assertIn("1 unverified", first)
        self.assertIn("UNVERIFIED S01: A02-peg#1", out)
        self.assertEqual(json.loads(out.splitlines()[-1])["verdict"], "UNVERIFIED")

    def test_a_failure_still_exits_1(self):
        code, _ = self.run_main(self.report(failures=["S01: x"], unverified=["S02: y"]))
        self.assertEqual(code, kit_tree.EXIT_FAIL)

    def test_a_clean_tree_still_passes(self):
        self.assertEqual(self.run_main(self.report())[0], kit_tree.EXIT_PASS)


if __name__ == "__main__":
    unittest.main()
