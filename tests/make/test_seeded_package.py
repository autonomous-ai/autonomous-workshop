"""ADR 0098: the seeded batch's mechanical project and package steps.

Contract: `prepare` copies the seed's CAD project without the approval, its
review, checklist, product source or approved STEPs, and installs the run's
own print-details library; `product` writes product.json (the title from the
Wish's name line when it has one, else the Proof's), the Spark source from
the host assignment and the sealed concept, the root assembled copies of the
final combined STEP and a powered toy's README verbatim, and exits 1 naming
what is missing."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

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
        (self.project / "proof.step.json").write_text("{}")
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
        self.assertEqual((self.product_root / "README.md").read_text(), "Solder the LED.\n")

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


if __name__ == "__main__":
    unittest.main()
