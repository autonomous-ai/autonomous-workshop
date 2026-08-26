import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.release import ProductRelease
from workshop.runtime import Receipt


SHA256 = "a" * 64


class ProductReleaseContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / "release"
        self.root.mkdir()
        self.claims = {"mechanical-check": {"passed": True}}
        (self.root / "MANUAL.md").write_text("# Manual\n\nUse the toy safely.\n")
        (self.root / "product.json").write_text(
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
                }
            )
            + "\n"
        )
        self.manifest = build_artifact_manifest(
            self.root, created_at="content-addressed"
        )

    def receipt(
        self,
        *,
        page_url=True,
        project_url=None,
        product_page_sha256=None,
    ):
        expected_product_page_sha256 = next(
            entry.sha256
            for entry in self.manifest.entries
            if entry.path == "product.json"
        )
        details = {
            "release_sha256": self.manifest.artifact_sha256,
            "product_page_sha256": (
                expected_product_page_sha256
                if product_page_sha256 is None
                else product_page_sha256
            ),
        }
        if page_url:
            details["page_url"] = (
                "https://www.autonomous.ai/factory/product/current-route"
            )
        return Receipt(
            payload_sha256="b" * 64,
            artifact_sha256=SHA256,
            adapter="factory",
            status="draft",
            observed_at="2026-08-26T00:00:00Z",
            reference="design-1",
            details=details,
            design_id="design-1",
            slug="current-route",
            owner_id="owner-1",
            root_id="design-1",
            current_history_id="history-1",
            project_url=project_url or "https://cdn.autonomous.ai/projects/history-1/",
        )

    def test_site_receipt_is_the_only_receipt_property(self):
        receipt = self.receipt()
        release = ProductRelease.from_root(
            self.root, SHA256, "MANUAL.md", self.claims, receipt
        )

        self.assertIs(release.site_receipt, receipt)
        self.assertFalse(hasattr(release, "publication_receipt"))
        self.assertEqual(
            release.page_url,
            "https://www.autonomous.ai/factory/product/current-route",
        )

    def test_project_url_cannot_substitute_for_page_url(self):
        receipt = self.receipt(
            page_url=False,
            project_url="https://www.autonomous.ai/factory/product/old-route",
        )

        with self.assertRaisesRegex(ContractError, "customer product page URL"):
            ProductRelease.from_root(
                self.root, SHA256, "MANUAL.md", self.claims, receipt
            )

    def test_receipt_must_bind_exact_product_page_bytes(self):
        receipt = self.receipt(product_page_sha256="f" * 64)

        with self.assertRaisesRegex(ContractError, "product-page bytes"):
            ProductRelease.from_root(
                self.root, SHA256, "MANUAL.md", self.claims, receipt
            )


if __name__ == "__main__":
    unittest.main()
