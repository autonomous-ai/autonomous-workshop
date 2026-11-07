"""ADR 0098: the seeded batch's mechanical project and package steps.

Contract: `prepare` copies the seed's CAD project without the approval, its
review, checklist, product source or approved STEPs, and installs the run's
own print-details library; `product` writes product.json (the title from the
Wish's name line when it has one, else the Proof's), the Spark source from
the host assignment and the sealed concept, the root assembled copies of the
final combined STEP and a powered toy's README verbatim, and exits 1 naming
what is missing. `parts` writes parts/<occurrence>.step for every printed
occurrence of a multi-part package from the Component STEP the print gates
passed: a one-solid Component's bytes copied (every instance alike), a
several-solid Component split by label; Bought Parts get none, a one-part
package needs none, and an occurrence no Component holds, or more than one
holds, is named."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.make.test_assembly_package import quarterhoot_package
from tests.skills.test_seal_proof import SEED_PRODUCT
from workshop.make import seeded_package as package


class SeededPackageTest(unittest.TestCase):
    def setUp(self):
        self.run_root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        seed = self.run_root / "seed"
        for name, text in {"APPROVAL.json": "{}", "CRITIC.json": "{}", "CONCEPT-CHECKLIST.md": "x",
                           "SEED-PRODUCT.json": json.dumps(SEED_PRODUCT), "approved/part_body.step": "step",
                           "params.py": "A = 1\n", "part_body.step.py": "body\n", "proof.step.py": "asm\n",
                           "features/print_details.py": "old library\n", "snap/iso.png": "png"}.items():
            (seed / name).parent.mkdir(parents=True, exist_ok=True)
            (seed / name).write_text(text)
        library = self.run_root / package.PRINT_DETAILS
        library.parent.mkdir(parents=True)
        library.write_text("run library\n")
        (self.run_root / "WISH.json").write_text(json.dumps({"objective": "Name this toy exactly: Hinge Box (v2).\n# Box"}))
        (self.run_root / "STAGE.json").write_text(json.dumps({"inputs": {"workshop_selection": {"assignment": {
            "selected_inventor_id": "rowan-vale", "ranking": [{"inventor_id": "rowan-vale", "rationale": "named"}]}}}}))
        self.product_root = self.run_root / "artifacts/make/r0001/product"
        self.project = self.product_root / "cad"

    def _main(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = package.main([str(item) for item in argv])
        self.stderr = err.getvalue()
        return code

    def test_prepare_copies_the_project_and_installs_the_run_library(self):
        self.assertEqual(self._main("prepare", self.run_root, "--project", self.project), 0, self.stderr)
        files = sorted(path.relative_to(self.project).as_posix() for path in self.project.rglob("*") if path.is_file())
        self.assertEqual(files, ["features/print_details.py", "params.py", "part_body.step.py", "proof.step.py",
                                 "snap/iso.png"])
        self.assertEqual((self.project / "features/print_details.py").read_text(), "run library\n")
        self.assertEqual(package.prepare(self.run_root, self.project), [], "a second prepare changes nothing")

    def test_product_writes_what_the_finalizer_reads(self):
        package.prepare(self.run_root, self.project)
        (self.project / "proof.step").write_text("combined")
        # cadgen keys the package by the entry source's name (the arcade
        # run's Manager copied it from here by hand).
        descriptor = self.project / "__cadgen__/models/proof.step.py/assembly.json"
        descriptor.parent.mkdir(parents=True)
        descriptor.write_text('{"kind": "package"}')
        (self.project / "proof.step.json").write_text("not the package")
        (self.project / "measure/electrical").mkdir(parents=True)
        (self.project / "measure/electrical/assembly.md").write_text("Solder the LED.\n")
        source = self.run_root / "work/seeded/spark-source.json"
        self.assertEqual(self._main("product", self.run_root, "--project", self.project, "--product-root",
                                    self.product_root, "--source", source), 0, self.stderr)
        self.assertEqual(json.loads((self.product_root / "product.json").read_text()),
                         {"title": "Hinge Box (v2)", "summary": SEED_PRODUCT["summary"]})
        spark = json.loads(source.read_text())
        self.assertEqual((spark["selected_inventor_id"], spark["concept"]), ("rowan-vale", SEED_PRODUCT["concept"]))
        self.assertEqual((self.product_root / "assembled.step").read_text(), "combined")
        self.assertEqual((self.product_root / "assembled.step.json").read_text(), '{"kind": "package"}')
        self.assertEqual((self.product_root / "README.md").read_text(), "Solder the LED.\n")

    def test_product_without_the_cadgen_package_is_refused(self):
        package.prepare(self.run_root, self.project)
        (self.project / "proof.step").write_text("combined")
        (self.project / "proof.step.json").write_text("{}")
        source = self.run_root / "work/seeded/spark-source.json"
        self.assertEqual(self._main("product", self.run_root, "--project", self.project, "--product-root",
                                    self.product_root, "--source", source), 1)
        self.assertIn("__cadgen__/models/proof.step.py/assembly.json", self.stderr)

    def test_without_a_name_line_the_proof_title_stands(self):
        (self.run_root / "WISH.json").write_text(json.dumps({"objective": "# Box"}))
        self.assertIsNone(package.wish_name(self.run_root))

    def test_product_names_what_is_missing(self):
        package.prepare(self.run_root, self.project)
        self.assertEqual(self._main("product", self.run_root, "--project", self.project, "--product-root",
                                    self.product_root, "--source", self.run_root / "s.json"), 1)
        self.assertIn("final verification wrote no proof.step", self.stderr)
        (self.run_root / "seed/SEED-PRODUCT.json").write_text("{}")
        self.assertEqual(self._main("product", self.run_root, "--project", self.project, "--product-root",
                                    self.product_root, "--source", self.run_root / "s.json"), 1)
        self.assertIn("SEED-PRODUCT.json must have exactly", self.stderr)



def _occurrence(name, color=(0.1, 0.1, 0.1, 1.0)):
    return {"id": "o1.%d" % (abs(hash(name)) % 1000), "name": name, "component": "c%s" % name,
            "transform": [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            "color": list(color)}


class SeededPartsTest(unittest.TestCase):
    """The production parts a multi-part seeded build needs (ADR 0098)."""

    def setUp(self):
        self.product_root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.project = self.product_root / "cad"
        self.project.mkdir()
        (self.project / "proof.step.py").write_text("asm\n")
        for role in ("bezel", "dowel", "side-left"):
            (self.project / ("part_%s.step" % role)).write_bytes(b"STEP " + role.encode())
        self.leaves = {"bezel": {"part_bezel": "B"}, "dowel": {"dowel": "D"},
                       "side-left": {"side-left": "S", "side-left-trim": "T"}}
        self.exported = {}

    def _package(self, *names, bought=()):
        occurrences = [_occurrence(name) for name in names]
        occurrences += [_occurrence(name, (1.0, 0.0, 1.0, 1.0)) for name in bought]
        (self.product_root / "assembled.step.json").write_text(json.dumps(quarterhoot_package(
            occurrences=occurrences, stats={"occurrenceCount": len(occurrences), "shapeCount": len(occurrences)})))

    def _export(self):
        return package.export_parts(
            self.project, self.product_root,
            read_parts=lambda path: self.leaves[path.name[len("part_"):-len(".step")]],
            export_leaf=lambda shape, path: (self.exported.__setitem__(path.name, shape),
                                             path.write_text("leaf %s" % shape)))

    def test_every_printed_occurrence_gets_its_components_solid(self):
        self._package("bezel_black", "dowel-1_dark_blue", "dowel-2_dark_blue", "side-left_dark_blue",
                      "side-left-trim_mint", bought=("bought_switch",))
        written = self._export()
        self.assertEqual(written, ["bezel_black", "dowel-1_dark_blue", "dowel-2_dark_blue", "side-left_dark_blue",
                                   "side-left-trim_mint"])
        parts = self.product_root / "parts"
        self.assertEqual((parts / "bezel_black.step").read_bytes(), b"STEP bezel", "a gated STEP is copied")
        self.assertEqual((parts / "dowel-2_dark_blue.step").read_bytes(), b"STEP dowel")
        self.assertEqual(self.exported, {"side-left_dark_blue.step": "S", "side-left-trim_mint.step": "T"})
        self.assertFalse((parts / "bought_switch.step").exists(), "a Bought Part is not printed")

    def test_a_one_part_package_needs_no_parts(self):
        self._package("bezel_black")
        self.assertEqual(self._export(), [])
        self.assertFalse((self.product_root / "parts").exists())

    def test_an_occurrence_no_component_holds_is_named(self):
        self._package("bezel_black", "lid_black", "knob_white")
        with self.assertRaisesRegex(package.PackageError, "no Component STEP holds lid_black, knob_white"):
            self._export()
        self.assertFalse((self.product_root / "parts").exists(), "nothing is written on a refusal")

    def test_a_label_two_components_hold_is_named(self):
        self.leaves["dowel"] = {"dowel": "D", "side-left-trim": "X"}
        self._package("bezel_black", "side-left-trim_mint")
        with self.assertRaisesRegex(package.PackageError,
                                    r"more than one Component STEP holds side-left-trim_mint \(in dowel, side-left\)"):
            self._export()

    # -- the design batch's packaging check on a Proof

    def _proof_package(self, *names):
        self._package(*names)
        descriptor = self.project / "__cadgen__/models/proof.step.py/assembly.json"
        descriptor.parent.mkdir(parents=True)
        (self.product_root / "assembled.step.json").replace(descriptor)

    def _check(self):
        return package.check_package(
            self.project, read_parts=lambda path: self.leaves[path.name[len("part_"):-len(".step")]])

    def test_the_proof_check_resolves_every_part_and_writes_nothing(self):
        self._proof_package("bezel_black", "dowel-1_dark_blue", "side-left_dark_blue", "side-left-trim_mint")
        before = sorted(path for path in self.product_root.rglob("*"))
        self.assertEqual(self._check(), ["bezel_black", "dowel-1_dark_blue", "side-left_dark_blue",
                                         "side-left-trim_mint"])
        self.assertEqual(sorted(path for path in self.product_root.rglob("*")), before)

    def test_the_proof_check_refuses_an_unnamed_colour_and_an_unresolved_part(self):
        self._proof_package("bezel_black", "dowel_purple_haze")
        with self.assertRaisesRegex(package.PackageError, "must end in a stocked filament colour.*dowel_purple_haze"):
            self._check()
        self._proof_package_reset()
        self._proof_package("bezel_black", "lid_black")
        with self.assertRaisesRegex(package.PackageError, "no Component STEP holds lid_black"):
            self._check()

    def _proof_package_reset(self):
        shutil.rmtree(self.project / "__cadgen__")

    def test_the_proof_check_needs_final_verifications_package(self):
        with self.assertRaisesRegex(package.PackageError,
                                    "final verification wrote no __cadgen__/models/proof.step.py/assembly.json"):
            self._check()

    def test_the_command_exits_1_naming_the_occurrence(self):
        from unittest import mock

        self._package("bezel_black", "lid_black")
        reader = lambda path: self.leaves[path.name[len("part_"):-len(".step")]]  # noqa: E731
        with mock.patch("workshop.make.proof_diff.read_parts", reader), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = package.main(["parts", "--project", str(self.project), "--product-root", str(self.product_root)])
        self.assertEqual(code, 1)
        self.assertIn("lid_black", err.getvalue())

    def test_real_step_files_split_by_label(self):
        try:
            import build123d as bd
        except ImportError:
            self.skipTest("build123d is not installed")
        from workshop.make import proof_diff

        body = bd.Box(10, 10, 4)
        body.label = "side-left"
        trim = bd.Pos(0, 0, 5) * bd.Box(4, 4, 1)
        trim.label = "side-left-trim"
        side = bd.Compound(children=[body, trim])
        side.label = "side-left"
        bd.export_step(side, str(self.project / "part_side-left.step"))
        bd.export_step(bd.Box(3, 3, 3), str(self.project / "part_bezel.step"))
        (self.project / "part_dowel.step").unlink()
        self._package("bezel_black", "side-left_dark_blue", "side-left-trim_mint")
        self.assertEqual(len(package.export_parts(self.project, self.product_root)), 3)
        parts = self.product_root / "parts"
        self.assertEqual((parts / "bezel_black.step").read_bytes(), (self.project / "part_bezel.step").read_bytes())
        trim_part = bd.import_step(str(parts / "side-left-trim_mint.step"))
        self.assertAlmostEqual(trim_part.volume, 16.0, places=3)
        self.assertAlmostEqual(trim_part.bounding_box().min.Z, 4.5, places=3, msg="kept its place in the part")
        self.assertEqual(len(proof_diff.read_parts(parts / "side-left_dark_blue.step")), 1)


if __name__ == "__main__":
    unittest.main()
