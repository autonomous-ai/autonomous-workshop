from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.make.native import NativeMade
from workshop.workflow.native_run import (
    _MAKE_PROPOSAL_REJECTION_FEEDBACK,
    _MakeProposalRejected,
    _validate_made_production_parts,
)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _package(names):
    return {
        "schemaVersion": 2,
        "entryKind": "assembly",
        "kind": "assembly-package",
        "packageSchemaVersion": 3,
        "rootName": "toy",
        "units": "mm",
        "occurrences": [
            {
                "id": "o1.%d.1" % (index + 1),
                "name": name,
                "component": "c%d" % index,
                "transform": [
                    1.0, 0.0, 0.0, 0.0,
                    0.0, 1.0, 0.0, 0.0,
                    0.0, 0.0, 1.0, 0.0,
                    0.0, 0.0, 0.0, 1.0,
                ],
                "color": [0.5, 0.5, 0.5, 1.0],
            }
            for index, name in enumerate(names)
        ],
        "stats": {"occurrenceCount": len(names)},
    }


class MakeProductionPartsRuleTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()

    def _made(self, descriptor, parts=()):
        product_root = self.run_root / "artifacts/make/r0001/product"
        project = product_root / "cad/project"
        validation = product_root / "validation"
        project.mkdir(parents=True)
        validation.mkdir()
        product = {"title": "Moon Nook", "summary": "A tiny lunar observatory."}
        product_bytes = (
            json.dumps(product, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        (product_root / "product.json").write_bytes(product_bytes)
        (product_root / "assembled.step").write_bytes(b"ISO-10303-21;\n")
        (product_root / "assembled.step.json").write_bytes(descriptor)
        (product_root / "assembled.stl").write_bytes(b"solid moon\nendsolid moon\n")
        for name in parts:
            (product_root / "parts").mkdir(exist_ok=True)
            (product_root / "parts" / ("%s.stl" % name)).write_bytes(
                b"solid part\nendsolid part\n"
            )
        (project / "moon.step.py").write_text("def build():\n    return None\n")
        (project / "moon.step").write_bytes(b"ISO-10303-21;\n")
        (project / "moon.stl").write_bytes(b"solid moon\nendsolid moon\n")
        verification = b'{"ok":true}\n'
        (validation / "cad-build.json").write_bytes(verification)
        manifest = build_artifact_manifest(product_root, created_at="content-addressed")
        return NativeMade(
            round=1,
            wish_sha256="a" * 64,
            assignment_sha256="b" * 64,
            taste_sha256="c" * 64,
            blueprint_sha256="d" * 64,
            invented_sha256="e" * 64,
            product_root="artifacts/make/r0001/product",
            cad_project_path="cad/project",
            product_manifest=manifest,
            product=product,
            product_json_sha256=_sha(product_bytes),
            cad_verification_path="validation/cad-build.json",
            cad_verification_sha256=_sha(verification),
        )

    def test_a_multipart_package_with_every_part_counts_its_occurrences(self):
        made = self._made(
            json.dumps(_package(["owl", "nest"])).encode(), parts=("owl", "nest")
        )

        self.assertEqual(_validate_made_production_parts(made, self.run_root), 2)

    def test_a_missing_part_rejects_the_proposal_naming_the_path(self):
        made = self._made(json.dumps(_package(["owl", "nest"])).encode(), parts=("owl",))

        with self.assertRaises(_MakeProposalRejected) as raised:
            _validate_made_production_parts(made, self.run_root)

        rejection = raised.exception
        self.assertEqual(rejection.failure_code, "make-production-parts-missing")
        self.assertIn("parts/nest.stl", rejection.feedback)
        self.assertNotIn("parts/owl.stl", rejection.feedback)
        self.assertTrue(
            rejection.feedback.startswith(
                _MAKE_PROPOSAL_REJECTION_FEEDBACK["make-production-parts-missing"]
            )
        )

    def test_single_occurrence_and_foreign_descriptors_bind_no_rule(self):
        single = self._made(json.dumps(_package(["owl"])).encode())
        self.assertEqual(_validate_made_production_parts(single, self.run_root), 0)

        self.temporary.cleanup()
        self.temporary = tempfile.TemporaryDirectory()
        self.run_root = Path(self.temporary.name).resolve()
        foreign = self._made(b'{"assembly":"Moon Nook","parts":1}\n')
        self.assertEqual(_validate_made_production_parts(foreign, self.run_root), 0)

        self.temporary.cleanup()
        self.temporary = tempfile.TemporaryDirectory()
        self.run_root = Path(self.temporary.name).resolve()
        malformed = self._made(
            b'{"kind":"assembly-package","schemaVersion":2,"occurrences":[]}\n'
        )
        self.assertEqual(_validate_made_production_parts(malformed, self.run_root), 0)


if __name__ == "__main__":
    unittest.main()
