import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.make.native import NativeMade
from workshop.release.manual_design import (
    MANUAL_DESIGN_EVIDENCE_KIND,
    MANUAL_DESIGN_EVIDENCE_PATH,
    validate_manual_design_evidence,
)


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


class ManualDesignEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        font_path = Path(reportlab.__file__).resolve().parent / "fonts/Vera.ttf"
        pdfmetrics.registerFont(TTFont("WorkshopTestVera", str(font_path)))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()
        self.product_root = self.run_root / "artifacts/make/r0001/product"
        (self.product_root / "cad/project").mkdir(parents=True)
        (self.product_root / "validation").mkdir()
        visual = b"solid exact-product-visual\nendsolid exact-product-visual\n"
        (self.product_root / "cad/project/hero.stl").write_bytes(visual)
        (self.product_root / "cad/project/hero.step").write_bytes(
            b"ISO-10303-21;\nEND-ISO-10303-21;\n"
        )
        (self.product_root / "cad/project/source.py").write_text(
            "# deterministic source\n", encoding="utf-8"
        )
        product = {"title": "Moon Nook", "summary": "A tiny lunar observatory."}
        product_bytes = _canonical(product)
        verification = _canonical({"ok": True})
        (self.product_root / "product.json").write_bytes(product_bytes)
        (self.product_root / "validation/cad-build.json").write_bytes(verification)
        self.made = NativeMade(
            round=1,
            wish_sha256="a" * 64,
            assignment_sha256="b" * 64,
            taste_sha256="c" * 64,
            blueprint_sha256="d" * 64,
            invented_sha256="e" * 64,
            product_root="artifacts/make/r0001/product",
            cad_project_path="cad/project",
            product_manifest=build_artifact_manifest(
                self.product_root, created_at="content-addressed"
            ),
            product=product,
            product_json_sha256=_sha(product_bytes),
            cad_verification_path="validation/cad-build.json",
            cad_verification_sha256=_sha(verification),
        )
        self.package = self.run_root / "artifacts/release/package"
        self.package.mkdir(parents=True)
        self.manual = self._embedded_manual()
        (self.package / "MANUAL.pdf").write_bytes(self.manual)

    def _embedded_manual(self):
        output = io.BytesIO()
        canvas = Canvas(
            output,
            pagesize=(298, 420),
            pageCompression=1,
            initialFontName="WorkshopTestVera",
        )
        for page in (1, 2):
            canvas.setFont("WorkshopTestVera", 18)
            canvas.drawString(30, 360, "Moon Nook — page %d" % page)
            canvas.setFont("WorkshopTestVera", 10)
            canvas.drawString(30, 330, "Set up the exact observatory and begin.")
            canvas.showPage()
        canvas.save()
        return output.getvalue()

    def _evidence(self):
        visual = next(
            entry
            for entry in self.made.product_manifest.entries
            if entry.path == "cad/project/hero.stl"
        )
        return {
            "schema_version": 1,
            "kind": MANUAL_DESIGN_EVIDENCE_KIND,
            "manual_sha256": _sha(self.manual),
            "design_mode": "bespoke",
            "creative_brief": {
                "emotional_promise": "Open a tiny observatory and feel the first spark of discovery.",
                "physical_format": "Two-page pocket field card",
                "format_rationale": "A compact double-sided card keeps setup and first use visible together.",
                "visual_motif": "Orbit lines guide the eye between exact observatory silhouettes.",
                "palette": ["midnight navy", "moonlit cream", "signal coral"],
                "typography": ["Vera display", "Vera instructional body"],
                "teaching_arc": [
                    "Meet every included part",
                    "Build the first tiny expedition",
                    "Reset and invent another mission",
                ],
            },
            "product_visuals": [
                {
                    "source_path": visual.path,
                    "source_sha256": visual.sha256,
                    "pages": [1, 2],
                }
            ],
            "review": {
                "page_count": 2,
                "color_pages": [1, 2],
                "grayscale_pages": [1, 2],
                "first_time_owner_pass": True,
                "independent_reviewer": "native-subagent",
                "findings": ["The first setup cue competed with the cover title."],
                "resolved_changes": ["Moved the setup cue to page two and enlarged its action number."],
                "status": "approved",
            },
        }

    def _write(self, evidence):
        (self.package / MANUAL_DESIGN_EVIDENCE_PATH).write_bytes(
            _canonical(evidence)
        )

    def test_accepts_exact_bespoke_design_and_complete_review(self):
        evidence = self._evidence()
        self._write(evidence)

        observed = validate_manual_design_evidence(
            self.package,
            manual=self.manual,
            made=self.made,
        )

        self.assertEqual(observed, evidence)

    def test_rejects_generic_unbound_or_incomplete_evidence(self):
        cases = (
            (lambda value: value.update(design_mode="template"), "identity"),
            (
                lambda value: value.update(manual_sha256="f" * 64),
                "identity",
            ),
            (
                lambda value: value.update(product_visuals=[]),
                "product-derived visuals",
            ),
            (
                lambda value: value["product_visuals"][0].update(
                    source_sha256="f" * 64
                ),
                "sealed Made bytes",
            ),
            (
                lambda value: value["review"].update(grayscale_pages=[1]),
                "review is incomplete",
            ),
            (
                lambda value: value["review"].update(
                    independent_reviewer="self"
                ),
                "review is incomplete",
            ),
        )
        for mutate, message in cases:
            with self.subTest(message=message):
                evidence = self._evidence()
                mutate(evidence)
                self._write(evidence)
                with self.assertRaisesRegex(ContractError, message):
                    validate_manual_design_evidence(
                        self.package,
                        manual=self.manual,
                        made=self.made,
                    )

    def test_rejects_unembedded_standard_fonts(self):
        output = io.BytesIO()
        canvas = Canvas(output, pagesize=(298, 420), pageCompression=1)
        canvas.setFont("Times-Roman", 12)
        canvas.drawString(30, 350, "A generic fallback manual with no embedded font.")
        canvas.showPage()
        canvas.save()
        manual = output.getvalue()
        evidence = self._evidence()
        evidence["manual_sha256"] = _sha(manual)
        evidence["review"].update(
            page_count=1,
            color_pages=[1],
            grayscale_pages=[1],
        )
        evidence["product_visuals"][0]["pages"] = [1]
        self._write(evidence)

        with self.assertRaisesRegex(ContractError, "embed every used font"):
            validate_manual_design_evidence(
                self.package,
                manual=manual,
                made=self.made,
            )


if __name__ == "__main__":
    unittest.main()
