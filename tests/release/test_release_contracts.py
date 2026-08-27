import json
import io
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.release import ProductRelease
from reportlab.pdfgen import canvas


SHA256 = "a" * 64


class ProductReleaseContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / "release"
        self.root.mkdir()
        self.claims = {"mechanical-check": {"passed": True}}
        (self.root / "MANUAL.md").write_text("# Manual\n\nUse the toy safely.\n")
        (self.root / "product.json").write_bytes(
            json.dumps(
                {
                    "schema_version": 3,
                    "kind": "workshop.release-package",
                    "status": "page-ready",
                    "title": "Verified Toy",
                    "summary": "A sealed toy with a complete product page.",
                    "hero": {
                        "headline": "Verified Toy",
                        "body": "A compact toy described by the sealed Made artifact.",
                        "visual_direction": "Show only the exact assembled model.",
                        "evidence_refs": ["made:product.json"],
                    },
                    "cinematic": {
                        "headline": "Ready for a closer look",
                        "body": "Explore the exact shape and included parts.",
                        "visual_direction": "Use a close view of the exact model.",
                        "evidence_refs": ["made:product.json"],
                    },
                    "use_case": {
                        "headline": "Made for tabletop play",
                        "body": (
                            "Follow the sealed manual to identify every included part, "
                            "place the toy on a stable tabletop, and begin the first "
                            "activity exactly as documented. Reset the parts between "
                            "turns and keep the manual nearby when choosing the next "
                            "supported play pattern."
                        ),
                        "visual_direction": "Show the model beside its manual.",
                        "evidence_refs": ["made:product.json"],
                    },
                    "story_blocks": [
                        {
                            "headline": "Evidence attached",
                            "body": (
                                "The required mechanical check ran against the sealed "
                                "product revision and recorded its exact evidence. This "
                                "page reports only that bounded digital result; it does "
                                "not turn the automated observation into a claim about "
                                "printing, durability, or human play."
                            ),
                            "visual_direction": "Use a simple verified-check motif.",
                            "evidence_refs": ["playtest:mechanical-check"],
                        }
                    ],
                    "what_arrives": ["one sealed toy"],
                    "limitations": ["No physical-use claim is made"],
                    "product_artifact_sha256": SHA256,
                    "playtest_evidence_artifact_sha256": "c" * 64,
                    "claims": self.claims,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        self.manifest = build_artifact_manifest(
            self.root, created_at="content-addressed"
        )

    def test_local_release_requires_no_publication_receipt(self):
        release = ProductRelease.from_root(
            self.root, SHA256, "MANUAL.md", self.claims
        )

        self.assertEqual(release.manual_path, "MANUAL.md")
        self.assertEqual(release.release_sha256, self.manifest.artifact_sha256)
        self.assertFalse(hasattr(release, "site_receipt"))
        self.assertFalse(hasattr(release, "publication_receipt"))

    def test_local_release_accepts_the_new_pdf_manual_path(self):
        (self.root / "MANUAL.md").unlink()
        output = io.BytesIO()
        document = canvas.Canvas(output, pagesize=(297.64, 419.53))
        document.drawString(36, 380, "Verified Toy")
        document.drawString(36, 360, "Open the box and follow this safe first play.")
        document.showPage()
        document.save()
        (self.root / "MANUAL.pdf").write_bytes(output.getvalue())
        product_path = self.root / "product.json"
        product = json.loads(product_path.read_text(encoding="utf-8"))
        product["schema_version"] = 4
        product["status"] = "manual-ready"
        for field in ("hero", "cinematic", "use_case", "story_blocks"):
            product.pop(field)
        product_path.write_bytes(
            json.dumps(
                product,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )

        release = ProductRelease.from_root(
            self.root, SHA256, "MANUAL.pdf", self.claims
        )

        self.assertEqual(release.manual_path, "MANUAL.pdf")
        release.assert_current()

    def test_local_release_rejects_schema_three_with_pdf_manual(self):
        (self.root / "MANUAL.md").rename(self.root / "MANUAL.pdf")

        with self.assertRaisesRegex(ContractError, "requires product.json schema_version 4"):
            ProductRelease.from_root(
                self.root, SHA256, "MANUAL.pdf", self.claims
            )

    def test_local_release_rejects_invalid_pdf_bytes(self):
        (self.root / "MANUAL.md").unlink()
        (self.root / "MANUAL.pdf").write_bytes(b"%PDF-1.7\nnot a PDF\n%%EOF\n")
        product_path = self.root / "product.json"
        product = json.loads(product_path.read_text(encoding="utf-8"))
        product["schema_version"] = 4
        product["status"] = "manual-ready"
        for field in ("hero", "cinematic", "use_case", "story_blocks"):
            product.pop(field)
        product_path.write_bytes(
            json.dumps(product, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        )

        with self.assertRaisesRegex(ContractError, "MANUAL.pdf"):
            ProductRelease.from_root(
                self.root, SHA256, "MANUAL.pdf", self.claims
            )

    def test_local_release_rejects_schema_four_with_markdown_manual(self):
        product_path = self.root / "product.json"
        product = json.loads(product_path.read_text(encoding="utf-8"))
        product["schema_version"] = 4
        product["status"] = "manual-ready"
        for field in ("hero", "cinematic", "use_case", "story_blocks"):
            product.pop(field)
        product_path.write_bytes(
            json.dumps(
                product,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )

        with self.assertRaisesRegex(ContractError, "requires product.json schema_version 3"):
            ProductRelease.from_root(
                self.root, SHA256, "MANUAL.md", self.claims
            )

    def test_local_release_rejects_noncanonical_product_json(self):
        product_path = self.root / "product.json"
        product = json.loads(product_path.read_text(encoding="utf-8"))
        product_path.write_text(json.dumps(product, indent=2), encoding="utf-8")

        with self.assertRaisesRegex(ContractError, "canonical JSON"):
            ProductRelease.from_root(
                self.root, SHA256, "MANUAL.md", self.claims
            )

    def test_local_release_rejects_noncanonical_manual_name(self):
        (self.root / "guide.pdf").write_bytes(b"guide")

        with self.assertRaisesRegex(ContractError, "MANUAL.md or MANUAL.pdf"):
            ProductRelease.from_root(
                self.root, SHA256, "guide.pdf", self.claims
            )


if __name__ == "__main__":
    unittest.main()
