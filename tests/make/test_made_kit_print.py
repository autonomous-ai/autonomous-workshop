"""ADR 0104 decision 4: before Make is accepted the host checks a kit's print
layout on the sealed bytes, without rebuilding geometry, and records it as
the printed-only primary Release ships to Factory.

Contract: the record is for the sealed tree, names the sealed STEP by hash
and lays out the tree's Sheets and every loose printed copy; the STEP's
leaves are exactly one per Sheet and one per loose copy, each Sheet one
connected solid (one solid, one outer shell; a void inside is allowed),
each loose copy a solid, and copies of one Part are alike. Only schema 2
is accepted: a schema 1 record, with unfused Sheet leaves, is refused from
any run. A kit with Sheets must have one; a kit without Sheets that wrote
none, and a non-kit, give None."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.make.kit_print import expected_bodies, expected_copies, verify_made_print_layout
from workshop.make.kit_tree import install_document, tree_digest
from tests.make import test_made_kit_tree as tree_tests

PRODUCT = tree_tests.PRODUCT


def layout_step(names, *, odd=None, shapes=None) -> bytes:
    """A layout STEP with one box leaf per name; ``shapes`` maps a name to
    the shape built for it instead."""

    from build123d import Box, Compound, Pos

    from cadgen.step_export import export_build123d_step_file

    children = []
    for index, name in enumerate(names):
        part = name.split("/", 1)[-1].rsplit("#", 1)[0]
        size = 4 + (sum(map(ord, part)) % 7) + (1 if name == odd else 0)
        built = (shapes or {}).get(name)
        solid = Pos(index * 30.0, 0, 0) * (built() if built else Box(size, size, 2))
        solid.label = name
        children.append(solid)
    root = Compound(children=children)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "print.step"
        export_build123d_step_file(root, path)
        return path.read_bytes()


class MadeKitPrintTest(unittest.TestCase):
    setUp = tree_tests.MadeKitTreeTest.setUp
    write = tree_tests.MadeKitTreeTest.write
    made = tree_tests.MadeKitTreeTest.made

    @classmethod
    def setUpClass(cls):
        import sys

        root = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/packages/cadgen/src"
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))

    def seal(self, contract=None, names=None, step=None, **changes):
        contract = contract or self.contract
        sheets, loose = expected_copies(contract)
        names = expected_bodies(sheets, loose) if names is None else names
        step = layout_step(names) if step is None else step
        (self.cad / "measure/kit").mkdir(parents=True, exist_ok=True)
        (self.cad / "measure/kit/print.step").write_bytes(step)
        (self.run_root / PRODUCT / "assembled.step").write_bytes(b"scene")
        copies = {}
        for sheet in sheets:
            for part, count in sheet["copies"].items():
                copies[part] = copies.get(part, 0) + count
        for part, count in loose.items():
            copies[part] = copies.get(part, 0) + count
        report = {"kind": "kit-print-layout", "schema_version": 2,
                  "tree_sha256": tree_digest(install_document(contract, self.catalogue)),
                  "step": "measure/kit/print.step", "sha256": hashlib.sha256(step).hexdigest(),
                  "sheets": sheets, "loose": loose, "copies": dict(sorted(copies.items())),
                  "bodies": expected_bodies(sheets, loose)}
        report.update(changes)
        self.write("measure/kit/print.json", report)
        return report

    def check(self, contract=None):
        return verify_made_print_layout(self.run_root, self.made(), contract or self.contract, self.catalogue)

    def refused(self, contract=None):
        with self.assertRaises(ContractError) as caught:
            self.check(contract)
        return str(caught.exception)

    def sheeted(self):
        contract = copy.deepcopy(self.contract)
        tree = contract["assembly_tree"]
        tree["sheets"] = [{"id": "B1", "filament": next(p["filament"] for p in tree["parts"]
                                                        if p["id"] == "B01-cabinet-carcass"),
                           "parts": [{"id": "B01-cabinet-carcass", "count": 1}]}]
        return contract

    def test_a_layout_of_every_loose_copy_is_the_printed_only_primary(self):
        self.seal()
        record = self.check()
        sheets, loose = expected_copies(self.contract)
        self.assertEqual(sheets, [])
        self.assertEqual(sorted(loose), ["A01-case-shell", "B01-cabinet-carcass", "B02-cabinet-door",
                                         "C01-desk-body", "D01-inkwell"])
        self.assertEqual(record["path"], "cad/measure/kit/print.step")
        self.assertEqual(record["layout_path"], "cad/measure/kit/print.json")
        self.assertEqual(record["scene_path"], "assembled.step")
        self.assertEqual(record["printed_bodies"], sum(loose.values()))
        self.assertEqual(record["removed"], [item["body"] for item in self.listed["bodies"]])
        self.assertEqual(record["removed_bodies"], len(self.listed["bodies"]))

    def test_a_sheet_is_one_fused_leaf_and_loose_parts_stay_apart(self):
        contract = self.sheeted()
        self.seal(contract)
        names = expected_bodies(*expected_copies(contract))
        self.assertIn("B1", names)
        self.assertFalse(any(name.startswith("B1/") for name in names))
        self.assertNotIn("loose/B01-cabinet-carcass#1", names)
        loose = [name for name in names if name.startswith("loose/")]
        self.assertEqual(len(loose), len(names) - 1)
        record = self.check(contract)
        self.assertEqual(record["printed_bodies"], len(names))
        # The record must be for the tree in effect.
        self.assertIn("another Assembly Tree", self.refused())

    def test_a_sheet_with_a_void_inside_is_still_one_connected_solid(self):
        from build123d import Box

        contract = self.sheeted()
        self.seal(contract, step=layout_step(expected_bodies(*expected_copies(contract)),
                                             shapes={"B1": lambda: Box(20, 20, 6) - Box(6, 6, 2)}))
        self.assertIsNotNone(self.check(contract))

    def test_a_sheet_that_is_not_one_connected_solid_is_refused(self):
        from build123d import Box, Compound, Pos

        def apart():
            # A copy whose gate misses the frame: two solids in one leaf.
            return Compound([Box(10, 10, 2), Pos(30, 0, 0) * Box(10, 10, 2)])

        def two_shells():
            # One solid that bounds two separate pieces of material.
            from build123d import Solid
            from OCP.BRep import BRep_Builder
            from OCP.TopoDS import TopoDS_Solid

            builder, solid = BRep_Builder(), TopoDS_Solid()
            builder.MakeSolid(solid)
            for piece in (Box(10, 10, 2), Pos(30, 0, 0) * Box(10, 10, 2)):
                builder.Add(solid, piece.shells()[0].wrapped)
            return Solid(solid)

        contract = self.sheeted()
        names = expected_bodies(*expected_copies(contract))
        for label, build in (("two solids", apart), ("two outer shells", two_shells)):
            with self.subTest(label):
                self.seal(contract, step=layout_step(names, shapes={"B1": build}))
                self.assertIn("Sheet B1 is not one connected solid but 2 piece(s)", self.refused(contract))

    def test_a_schema_1_layout_from_a_current_run_is_refused(self):
        # The unfused layout #312 wrote: a frame leaf and a leaf per copy.
        contract = self.sheeted()
        sheets, loose = expected_copies(contract)
        unfused = sorted(["B1/frame", "B1/B01-cabinet-carcass#1"]
                         + [name for name in expected_bodies(sheets, loose) if name.startswith("loose/")])
        self.seal(contract, step=layout_step(unfused), schema_version=1, bodies=unfused)
        self.assertIn("is not a kit print layout record", self.refused(contract))
        # Relabelled schema 2, its unfused leaves are still not the Sheet.
        self.seal(contract, step=layout_step(unfused))
        self.assertIn("missing B1", self.refused(contract))
        for bad in (True, 3, "2"):
            with self.subTest(bad):
                report = self.seal(contract)
                report["schema_version"] = bad
                self.write("measure/kit/print.json", report)
                self.assertIn("is not a kit print layout record", self.refused(contract))

    def test_a_kit_with_sheets_needs_its_layout_and_one_without_may_keep_its_scene(self):
        self.assertIsNone(self.check())
        self.assertIn("wrote no measure/kit/print.json", self.refused(self.sheeted()))
        self.assertIsNone(verify_made_print_layout(self.run_root, self.made(), {"schema_version": 6}, None))

    def test_each_wrong_layout_is_refused(self):
        sheets, loose = expected_copies(self.contract)
        names = expected_bodies(sheets, loose)
        bought = names[:-1] + ["loose/P01-hinge-pin#1"]
        cases = {
            "another tree": ({"tree_sha256": "0" * 64}, None, None, "another Assembly Tree"),
            "a loose copy short": ({"loose": dict(loose, **{"D01-inkwell": 0})}, None, None,
                                   "does not lay out the sealed tree"),
            "another step": ({"sha256": "0" * 64}, None, None, "is not the layout"),
            "a bought body": ({}, bought, None, "extra loose/P01-hinge-pin#1"),
            "copies differ": ({}, None, "odd", "differ in volume or area"),
        }
        for label, (changes, step_names, odd, words) in cases.items():
            with self.subTest(label):
                step = None
                if odd:
                    twin = [n for n in names if n.endswith("#2")][0]
                    step = layout_step(names, odd=twin)
                elif step_names is not None:
                    step = layout_step(step_names)
                self.seal(step=step, **changes)
                self.assertIn(words, self.refused())


if __name__ == "__main__":
    unittest.main()
