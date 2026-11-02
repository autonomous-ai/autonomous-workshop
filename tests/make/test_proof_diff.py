"""ADR 0096 decision 2b: proof_diff compares built STEP with the Approved Proof.

Contract: a Part passes at |dV| <= 1%, every bounding-box side within 0.1 mm
and a two-way Boolean difference <= 1% of volume; a failed Boolean is
reported and judged on volume and box alone; the surface deviation is always
reported and fails a Part only when a limit is set; directories compare
``part_*.step`` by name and a missing or extra Part fails.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import build123d as bd

from workshop.make import proof_diff
from workshop.make.proof_diff import ProofDiffError, Tolerance, compare, diff_part, main


def _write(path: Path, *shapes: tuple[str | None, bd.Shape]) -> Path:
    solids = []
    for label, shape in shapes:
        solid = shape.solids()[0] if not isinstance(shape, bd.Solid) else shape
        if label:
            solid.label = label
        solids.append(solid)
    path.parent.mkdir(parents=True, exist_ok=True)
    bd.export_step(bd.Compound(children=solids), str(path))
    return path


def _cube(size: float = 10.0) -> bd.Solid:
    return bd.Solid.make_box(size, size, size)


class ProofDiffPartTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _pair(self, a: bd.Shape, b: bd.Shape, label: str = "body") -> tuple[Path, Path]:
        return (
            _write(self.root / "a" / "part_x.step", (label, a)),
            _write(self.root / "b" / "part_x.step", (label, b)),
        )

    def test_identical_part_passes_with_zero_differences(self) -> None:
        a, b = self._pair(_cube(), _cube())
        report = compare(a, b)
        self.assertTrue(report["passed"])
        (part,) = report["parts"]
        self.assertEqual(part["part"], "body")
        self.assertEqual(part["boolean"], "ok")
        self.assertAlmostEqual(part["volume_delta"], 0.0, places=9)
        self.assertAlmostEqual(part["two_way"], 0.0, places=6)
        self.assertAlmostEqual(part["surface_deviation_mm"], 0.0, places=6)

    def test_hidden_pocket_over_one_percent_fails_on_volume_and_two_way(self) -> None:
        pocket = bd.Pos(3.5, 3.5, 0) * bd.Solid.make_box(3, 3, 2)  # 18 mm3 of 1000
        a, b = self._pair(_cube(), _cube() - pocket)
        report = compare(a, b)
        self.assertFalse(report["passed"])
        (part,) = report["parts"]
        self.assertAlmostEqual(part["volume_delta"], 0.018, places=6)
        self.assertTrue(any("volume differs" in r for r in part["reasons"]))
        self.assertTrue(any("two-way" in r for r in part["reasons"]))

    def test_pocket_under_one_percent_passes(self) -> None:
        pocket = bd.Pos(4, 4, 0) * bd.Solid.make_box(2, 2, 2)  # 8 mm3 of 1000
        a, b = self._pair(_cube(), _cube() - pocket)
        self.assertTrue(compare(a, b)["passed"])

    def test_add_and_remove_with_zero_net_volume_fails_on_two_way(self) -> None:
        base = bd.Solid.make_box(20, 20, 5)
        bump = bd.Solid.make_box(3, 3, 2)
        left = base + bd.Pos(2, 2, 5) * bump
        right = base + bd.Pos(15, 15, 5) * bump
        a, b = self._pair(left, right)
        (part,) = compare(a, b)["parts"]
        self.assertLess(part["volume_delta"], 1e-9)
        self.assertLess(part["bbox_side_delta_mm"], 1e-9)
        self.assertFalse(part["passed"])
        self.assertGreater(part["two_way"], 0.01)

    def test_bounding_box_side_change_of_two_tenths_fails(self) -> None:
        a, b = self._pair(bd.Solid.make_box(100, 10, 10), bd.Solid.make_box(100.2, 10, 10))
        (part,) = compare(a, b)["parts"]
        self.assertFalse(part["passed"])
        self.assertAlmostEqual(part["bbox_side_delta_mm"], 0.2, places=6)
        self.assertTrue(any("bounding-box side" in r for r in part["reasons"]))

    def test_bbox_alignment_ignores_a_shift_but_display_pose_does_not(self) -> None:
        a, b = self._pair(_cube(), bd.Pos(5, 0, 0) * _cube())
        self.assertTrue(compare(a, b, align="bbox")["passed"])
        moved = compare(a, b, align="none")
        self.assertFalse(moved["passed"])
        self.assertTrue(any("position differs" in r for r in moved["parts"][0]["reasons"]))

    def test_failed_boolean_is_reported_and_judged_on_volume_and_box(self) -> None:
        def broken(_a, _b):
            raise RuntimeError("kernel")

        a, b = self._pair(_cube(), _cube())
        report = compare(a, b, boolean=broken)
        self.assertTrue(report["passed"])
        self.assertEqual(report["boolean_failed"], ["body"])
        self.assertIsNone(report["parts"][0]["two_way"])

    def test_boolean_that_returns_an_operand_unchanged_counts_as_failed(self) -> None:
        # K4's faceted wink head: A.cut(B) returned A whole, which breaks
        # A - B = only_A - only_B.
        def returns_a(a, _b):
            return a.volume, 0.0

        a, b = self._pair(_cube(), _cube())
        (part,) = compare(a, b, boolean=returns_a)["parts"]
        self.assertEqual(part["boolean"], "failed")
        self.assertTrue(part["passed"])

    def test_surface_deviation_is_reported_but_fails_only_with_a_limit(self) -> None:
        dent = bd.Pos(4, 4, 9.7) * bd.Solid.make_box(2, 2, 0.3)  # 1.2 mm3, 0.3 mm deep
        a, b = self._pair(_cube(), _cube() - dent)
        default = compare(a, b)
        self.assertTrue(default["passed"])
        self.assertAlmostEqual(default["parts"][0]["surface_deviation_mm"], 0.3, places=3)
        limited = compare(a, b, tolerance=Tolerance(surface_mm=0.1))
        self.assertFalse(limited["passed"])
        self.assertTrue(any("surface deviates" in r for r in limited["parts"][0]["reasons"]))

    def test_engraving_redrawn_like_k4_v01_passes_three_criteria_but_not_surface(self) -> None:
        # K4 v01's Grumpy face: the same head with its eye engraving redrawn
        # (two-way 0.77%, surface 0.6 mm on the real STEP). The three
        # accepted criteria pass it; only the surface measure sees it.
        head = bd.Solid.make_box(11.4, 11.0, 2.0)  # 250.8 mm3
        round_eye = bd.Pos(3.0, 5.0, 1.4) * bd.Solid.make_box(1.0, 1.0, 0.6)
        slant_eye = bd.Pos(3.0, 5.0, 1.4) * bd.Solid.make_box(1.6, 0.6, 0.6)
        a, b = self._pair(head - round_eye, head - slant_eye)
        (part,) = compare(a, b)["parts"]
        self.assertTrue(part["passed"])
        self.assertLess(part["two_way"], 0.01)
        self.assertGreaterEqual(part["surface_deviation_mm"], 0.2)
        limited = compare(a, b, tolerance=Tolerance(surface_mm=0.1))
        self.assertFalse(limited["passed"])

    def test_unmeasurable_surface_fails_only_with_a_limit(self) -> None:
        def broken(_a, _b):
            raise RuntimeError("extrema")

        a, b = self._pair(_cube(), _cube())
        self.assertTrue(compare(a, b, surface=broken)["passed"])
        limited = compare(a, b, surface=broken, tolerance=Tolerance(surface_mm=0.1))
        self.assertFalse(limited["passed"])

    def test_zero_volume_approved_part_refuses(self) -> None:
        with self.assertRaises(ProofDiffError):
            diff_part("flat", bd.Compound([]), _cube())


class ProofDiffProjectTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_kit_parts_are_compared_by_label(self) -> None:
        board = bd.Solid.make_box(30, 20, 2)
        hat = bd.Pos(40, 0, 0) * bd.Solid.make_box(5, 5, 5)
        _write(self.root / "a" / "part_kit.step", ("B01-board", board), ("A03-hat", hat))
        _write(self.root / "b" / "part_kit.step", ("B01-board", board), ("A03-hat", hat))
        report = compare(self.root / "a", self.root / "b")
        self.assertTrue(report["passed"])
        self.assertEqual(
            [p["part"] for p in report["parts"]],
            ["part_kit.step/A03-hat", "part_kit.step/B01-board"],
        )

    def test_missing_and_extra_parts_and_files_fail(self) -> None:
        _write(self.root / "a" / "part_kit.step", ("B01-board", _cube()), ("A03-hat", bd.Pos(20, 0, 0) * _cube()))
        _write(self.root / "a" / "part_gone.step", ("gone", _cube()))
        _write(self.root / "b" / "part_kit.step", ("B01-board", _cube()), ("A04-cape", bd.Pos(20, 0, 0) * _cube()))
        _write(self.root / "b" / "part_new.step", ("new", _cube()))
        report = compare(self.root / "a", self.root / "b")
        self.assertFalse(report["passed"])
        self.assertEqual(report["missing"], ["part_gone.step", "part_kit.step/A03-hat"])
        self.assertEqual(report["extra"], ["part_new.step", "part_kit.step/A04-cape"])

    def test_unlabelled_solid_is_one_part_named_for_the_file(self) -> None:
        _write(self.root / "a" / "part_x.step", (None, _cube()))
        _write(self.root / "b" / "part_x.step", (None, _cube()))
        (part,) = compare(self.root / "a" / "part_x.step", self.root / "b" / "part_x.step")["parts"]
        self.assertEqual(part["part"], "part_x")

    def test_one_part_files_pair_regardless_of_label(self) -> None:
        # K4's v01 labelled its plate anchor_plate, the Proof anchor-plate.
        _write(self.root / "a" / "part_plate.step", ("anchor-plate", _cube()))
        _write(self.root / "b" / "part_plate.step", ("anchor_plate", _cube()))
        report = compare(self.root / "a", self.root / "b")
        self.assertTrue(report["passed"])
        self.assertEqual([p["part"] for p in report["parts"]], ["part_plate.step/anchor-plate"])

    def test_file_against_directory_refuses(self) -> None:
        path = _write(self.root / "a" / "part_x.step", ("x", _cube()))
        with self.assertRaises(ProofDiffError):
            compare(path, self.root / "a")

    def test_unreadable_step_refuses(self) -> None:
        bad = self.root / "a" / "part_x.step"
        bad.parent.mkdir(parents=True)
        bad.write_text("not a step file", encoding="utf-8")
        with self.assertRaises(ProofDiffError):
            compare(bad, bad)


class ProofDiffCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_exit_codes_and_json_report(self) -> None:
        a = _write(self.root / "a" / "part_x.step", ("x", _cube()))
        same = _write(self.root / "b" / "part_x.step", ("x", _cube()))
        big = _write(self.root / "c" / "part_x.step", ("x", _cube(10.5)))
        out_json = self.root / "report.json"
        code, out, _ = self._run(str(a), str(same), "--json", str(out_json))
        self.assertEqual(code, 0)
        self.assertIn("PASS x", out)
        report = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertEqual(report["tool"], "proof_diff")
        self.assertEqual(report["schema_version"], proof_diff.SCHEMA_VERSION)
        self.assertEqual(report["tolerance"], {"volume": 0.01, "bbox_mm": 0.1, "two_way": 0.01, "surface_mm": None})
        code, out, _ = self._run(str(a), str(big))
        self.assertEqual(code, 1)
        self.assertIn("over tolerance", out)
        code, _, err = self._run(str(a), str(self.root / "missing.step"))
        self.assertEqual(code, 2)
        self.assertIn("no such STEP file", err)


if __name__ == "__main__":
    unittest.main()
