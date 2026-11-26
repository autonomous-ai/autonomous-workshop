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
from workshop.make.kit_print import (
    expected_bodies,
    expected_copies,
    printed_pieces,
    verify_made_print_layout,
)
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

    def with_spares(self, part, spares):
        contract = copy.deepcopy(self.contract)
        entry = next(p for p in contract["assembly_tree"]["parts"] if p["id"] == part)
        entry["loose_reason"], entry["spares"] = "A round pot.", spares
        return contract

    def test_a_loose_parts_spares_are_laid_out_and_counted(self):
        contract = self.with_spares("D01-inkwell", 2)
        uses = expected_copies(self.contract)[1]["D01-inkwell"]
        sheets, loose = expected_copies(contract)
        self.assertEqual(loose["D01-inkwell"], uses + 2)
        report = self.seal(contract)
        self.assertEqual(report["copies"]["D01-inkwell"], uses + 2)
        self.assertIn("loose/D01-inkwell#%d" % (uses + 2), report["bodies"])
        record = self.check(contract)
        self.assertEqual(record["printed_bodies"], sum(loose.values()))

    def test_a_layout_without_the_declared_spares_is_refused(self):
        contract = self.with_spares("D01-inkwell", 1)
        # The layout the tool wrote before spares: one copy per use.
        plain = expected_copies(self.contract)
        names = expected_bodies(*plain)
        self.seal(contract, names=names, sheets=plain[0], loose=plain[1], bodies=names,
                  copies={part: count for part, count in sorted(plain[1].items())})
        self.assertIn("as many times as the toy uses it plus its spares", self.refused(contract))
        # A record that counts the spares but whose STEP lacks the spare leaf.
        self.seal(contract, step=layout_step(names))
        self.assertIn("missing loose/D01-inkwell#", self.refused(contract))

    # ADR 0104 amendment 2026-11-26: a kit that ships no spares.

    def no_spares(self):
        contract = copy.deepcopy(self.contract)
        contract["assembly_tree"]["spares"] = "none"
        return contract

    def test_a_kit_that_ships_no_spares_is_recorded_in_the_receipt(self):
        contract = self.no_spares()
        self.seal(contract, spares="none")
        record = self.check(contract)
        self.assertEqual(record["spares"], "none")
        # The default kit's receipt is unchanged: no spares field.
        self.seal()
        self.assertNotIn("spares", self.check())

    def test_the_layout_record_states_the_opt_out_exactly_when_the_tree_does(self):
        contract = self.no_spares()
        self.seal(contract)
        self.assertIn('does not record spares "none"', self.refused(contract))
        self.seal(spares="none")
        self.assertIn("records spares the tree does not declare", self.refused())
        self.seal(contract, spares="some")
        self.assertIn('does not record spares "none"', self.refused(contract))

    def test_a_kit_that_ships_no_spares_carries_no_spare_copy(self):
        contract = self.with_spares("D01-inkwell", 1)
        contract["assembly_tree"]["spares"] = "none"
        self.seal(contract, spares="none")
        self.assertIn('declares spares "none", but it carries spare copies of D01-inkwell',
                      self.refused(contract))

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

    # ADR 0092 amendment 2026-11-26: fit-test pieces on a Sheet.

    def fit_tested(self, no_spares=False):
        contract = self.sheeted()
        contract["assembly_tree"]["sheets"][0]["fit_test"] = {
            "pieces": [{"id": "T1", "name": "Fit slots"}, {"id": "T2", "name": "Fit tab"}],
            "text": "Press T2 into T1."}
        if no_spares:
            contract["assembly_tree"]["spares"] = "none"
        return contract

    def test_fit_test_pieces_fuse_with_their_sheet_and_are_no_part_copy(self):
        contract = self.fit_tested()
        sheets, _loose = expected_copies(contract)
        self.assertEqual(sheets[0]["fit_tests"], ["T1", "T2"])
        self.assertNotIn("T1", sheets[0]["copies"])
        names = expected_bodies(*expected_copies(contract))
        self.assertFalse(any("T1" in name or "T2" in name for name in names))
        self.seal(contract)
        record = self.check(contract)
        self.assertEqual(record["printed_bodies"], len(names))
        # A record that leaves the fit test out was laid out for another tree.
        self.seal(contract, sheets=expected_copies(self.sheeted())[0])
        self.assertIn("does not lay out the sealed tree's Sheets", self.refused(contract))

    def test_a_kit_that_ships_no_spares_does_not_count_fit_tests_as_spares(self):
        contract = self.fit_tested(no_spares=True)
        self.seal(contract, spares="none")
        self.assertEqual(self.check(contract)["spares"], "none")

    def test_a_loose_copy_of_two_solids_is_refused_and_one_passes(self):
        from build123d import Box, Compound, Pos

        names = expected_bodies(*expected_copies(self.contract))
        copy_name = "loose/D01-inkwell#1"
        self.seal(step=layout_step(names, shapes={copy_name: lambda: Box(6, 6, 2)}))
        self.assertIsNotNone(self.check())
        # The plate with a paving bar cut free of it: two solids in one leaf.
        self.seal(step=layout_step(names, shapes={copy_name: lambda: Compound(
            [Box(6, 6, 2), Pos(10, 0, 0) * Box(2, 6, 2)])}))
        self.assertIn("loose copy loose/D01-inkwell#1 is not one connected solid but 2 piece(s)", self.refused())

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

    # ADR 0104 (2026-11-23): the printed-only scene the viewer shows.

    PRINTED = ["A01-case-shell", "B01-cabinet-carcass", "C01-desk-body"]

    def seal_scene(self, *, printed_names=None, scene_names=None, **changes):
        removed = sorted(item["body"] for item in self.listed["bodies"])
        report = self.seal()
        scene = layout_step(scene_names if scene_names is not None else self.PRINTED + removed)
        printed = layout_step(self.PRINTED if printed_names is None else printed_names)
        (self.run_root / PRODUCT / "assembled.step").write_bytes(scene)
        (self.cad / "measure/kit/scene.step").write_bytes(printed)
        record = {"step": "measure/kit/scene.step", "sha256": hashlib.sha256(printed).hexdigest(),
                  "scene": "assembled.step", "scene_sha256": hashlib.sha256(scene).hexdigest(),
                  "removed": removed}
        record.update(changes)
        report["printed_scene"] = record
        self.write("measure/kit/print.json", report)
        return printed

    def test_a_printed_scene_is_checked_and_recorded_with_the_piece_count(self):
        printed = self.seal_scene()
        record = self.check()
        self.assertEqual(record["printed_scene_path"], "cad/measure/kit/scene.step")
        self.assertEqual(record["printed_scene_sha256"], hashlib.sha256(printed).hexdigest())
        self.assertEqual(record["pieces"], printed_pieces(self.contract))
        self.assertGreater(record["pieces"], 0)
        # The layout keeps its own fields.
        self.assertEqual(record["path"], "cad/measure/kit/print.step")

    def test_a_scene_leaf_held_once_may_drop_its_first_copy_number(self):
        removed = sorted(item["body"] for item in self.listed["bodies"])
        self.assertTrue(any(name.endswith("#1") for name in removed))
        bare = [name[: -len("#1")] if name.endswith("#1") else name for name in removed]
        self.seal_scene(scene_names=self.PRINTED + bare)
        self.assertIn("printed_scene_path", self.check())

    def test_a_layout_without_a_printed_scene_records_none(self):
        self.seal()
        self.assertNotIn("printed_scene_path", self.check())

    def test_each_wrong_printed_scene_is_refused(self):
        removed = sorted(item["body"] for item in self.listed["bodies"])
        cases = {
            "another scene": ({"scene_sha256": "0" * 64}, {}, "was cut from another scene"),
            "other bodies removed": ({"removed": removed[1:]}, {}, "removed other bodies"),
            "another file": ({"sha256": "0" * 64}, {}, "is not the scene"),
            "another path": ({"step": "measure/kit/other.step"}, {}, "printed_scene is malformed"),
            "an extra key": ({"pieces": 3}, {}, "printed_scene is malformed"),
            "a bought body kept": ({}, {"printed_names": self.PRINTED + removed[:1]}, "extra"),
            "a printed body lost": ({}, {"printed_names": self.PRINTED[1:]}, "missing A01-case-shell"),
            "a body changed": ({}, {"printed_names": self.PRINTED[:-1] + ["C01-desk-bodyX"]}, "missing"),
            "a listed body absent": ({}, {"scene_names": self.PRINTED}, "not one"),
            "a listed body twice": ({}, {"scene_names": self.PRINTED + removed + removed[:1]}, "not one"),
        }
        for label, (changes, names, words) in cases.items():
            with self.subTest(label):
                self.seal_scene(**names, **changes)
                self.assertIn(words, self.refused())

    def test_a_printed_scene_body_of_another_size_is_refused(self):
        from build123d import Box

        removed = sorted(item["body"] for item in self.listed["bodies"])
        self.seal_scene()
        report = json.loads((self.cad / "measure/kit/print.json").read_text())
        printed = layout_step(self.PRINTED, shapes={"A01-case-shell": lambda: Box(9, 9, 9)})
        (self.cad / "measure/kit/scene.step").write_bytes(printed)
        report["printed_scene"]["sha256"] = hashlib.sha256(printed).hexdigest()
        self.write("measure/kit/print.json", report)
        self.assertIn("body A01-case-shell is not the scene's body", self.refused())
        self.assertTrue(removed)


class SharedPrintTest(unittest.TestCase):
    """ADR 0092 amendment 2026-11-26: the host refuses a Made kit whose
    Parts sharing a ``print`` code are not one print, read from the sealed
    ``assembled.step`` by a fingerprint no pose changes."""

    setUp = MadeKitPrintTest.setUp
    write = MadeKitPrintTest.write
    made = MadeKitPrintTest.made
    setUpClass = MadeKitPrintTest.setUpClass
    seal = MadeKitPrintTest.seal
    check = MadeKitPrintTest.check
    refused = MadeKitPrintTest.refused

    SHARED = ("B01-cabinet-carcass", "B02-cabinet-door")

    def shared(self):
        contract = copy.deepcopy(self.contract)
        for part in contract["assembly_tree"]["parts"]:
            if part["id"] in self.SHARED:
                part["print"] = "B37"
        return contract

    def seal_shared(self, door=None, contract=None):
        from build123d import Box, Rot

        contract = contract or self.shared()
        same = lambda: Box(5, 6, 2)  # noqa: E731 - one print
        names = expected_bodies(*expected_copies(contract))
        self.seal(contract, step=layout_step(names, shapes={
            name: same for name in names if any(part in name for part in self.SHARED)}))
        removed = sorted(item["body"] for item in self.listed["bodies"])
        scene = layout_step(["A01-case-shell", *self.SHARED, "C01-desk-body", *removed], shapes={
            "B01-cabinet-carcass": same,
            # The same print in another pose: turned and tipped in the toy.
            "B02-cabinet-door": door or (lambda: Rot(30, 0, 90) * Box(5, 6, 2)),
        })
        (self.run_root / PRODUCT / "assembled.step").write_bytes(scene)
        return contract

    def test_a_shared_code_whose_parts_are_one_print_is_accepted(self):
        contract = self.seal_shared()
        record = self.check(contract)
        self.assertEqual(record["shared_prints"], {"B37": list(self.SHARED)})

    def test_mismatched_geometry_under_one_code_is_refused(self):
        from build123d import Box

        contract = self.seal_shared(door=lambda: Box(5, 6, 2.4))
        self.assertIn("share print code B37 but are not the same print", self.refused(contract))

    def test_a_shared_code_across_filaments_is_refused(self):
        contract = self.shared()
        door = next(p for p in contract["assembly_tree"]["parts"] if p["id"] == "B02-cabinet-door")
        door["filament"] = "navy" if door["filament"] != "navy" else "oak"
        self.seal_shared(contract=contract)
        self.assertIn("sharing print code B37 are not one filament", self.refused(contract))

    def test_loose_copies_under_one_code_must_match(self):
        contract = self.shared()
        names = expected_bodies(*expected_copies(contract))
        # layout_step sizes each Part by its name, so B01 and B02 differ.
        self.seal(contract, step=layout_step(names))
        self.assertIn("copies of B37 differ in volume or area", self.refused(contract))

    def test_a_contract_without_print_codes_records_none(self):
        self.seal_shared(contract=copy.deepcopy(self.contract))
        self.assertNotIn("shared_prints", self.check())


if __name__ == "__main__":
    unittest.main()
